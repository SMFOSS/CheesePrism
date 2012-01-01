"""
Classes, subscribers and functions for dealing with index management
"""
from cheeseprism import event
from cheeseprism.desc import updict 
from path import path
from pyramid.events import subscriber
import jinja2
import logging
import pkginfo
import re
import time

logger = logging.getLogger(__name__)


class IndexManager(object):
    """
    Manages the static file index
    """

    root_index_file = 'index.html'
    EXTS = re.compile(r'^.*(?P<ext>\.egg|\.gz|\.bz2|\.tgz|\.zip)$')

    leaf_name = 'leaf.html'
    home_name = 'index.html'
    def_index_title = 'CheesePrism'
    leaf_data = updict()
    index_data = updict(title=def_index_title,
                        index_title=def_index_title,
                        description="Welcome to the CheesePrism")

    def __init__(self, index_path, template_env=None, urlbase='..',
                 index_data={}, leaf_data={}):
        self.urlbase = urlbase
        self.template_env = template_env
        if not self.template_env:
            self.template_env = self.default_env_factory('')
        self.index_data = index_data.copy()            
        self.leaf_data = leaf_data.copy()
        self.path = path(index_path)
        if not self.path.exists():
            self.path.makedirs()        

    class template(object):
        """
        A little descriptor for returning templates from jinja env.
        """
        env_method = 'template_env'
        def __init__(self, name):
            self.name = name

        def get_env(self, obj):
            return getattr(obj, self.env_method, None)
        
        def __get__(self, obj, objtype):
            env = self.get_env(obj)
            return env.get_template(self.name)

    leaf_template = template('leaf.html')
    home_template = template('home.html')

    @property
    def default_env_factory(self):
        return EnvFactory.from_str

    @property
    def files(self):
        return (x for x in self.path.files() if self.EXTS.match(x))

    def projects_from_archives(self):
        files = self.files
        projects = {}
        for item in files:
            itempath = self.path / item
            info = self.pkginfo_from_file(itempath)
            projects.setdefault(info.name, []).append((info, itempath))
        return sorted(projects.items())

    def regenerate_leaf(self, leafname):
        files = self.path.files('%s-*.*' %leafname)
        versions = ((self.pkginfo_from_file(self.path / item), item) for item in files)
        return self.write_leaf(self.path / leafname, versions)

    def regenerate_all(self):
        items = self.projects_from_archives()
        home_file = self.path / self.root_index_file
        yield self.write_index_home(home_file, items)
        yield [self.write_leaf(self.path / key, value) for key, value in items]

    def write_index_home(self, home_file, items):
        logger.info('Write index home:%s', home_file)
        data = self.index_data.copy()
        data['packages'] = [dict(name=key, url="%s/%s" %(self.urlbase, key)) \
                            for key, value in items]
        home_file.write_text(self.home_template.render(**data))
        return home_file

    def write_leaf(self, leafdir, versions):
        if not leafdir.exists():
            leafdir.makedirs()

        leafhome = leafdir / "index.html"
        title = "%s:%s" %(self.index_data['title'], leafdir.name)
        tversions = [self.leaf_values(leafdir.name, archive)\
                    for info, archive in versions]
        
        text = self.leaf_template\
               .render(package_title=leafdir.name,
                       title=title,
                       versions=tversions)

        leafhome.write_text(text)
        leafhome.utime((time.time(), time.time()))
        return leafhome

    def leaf_values(self, leafname, archive):
        url = "%s/%s" %(self.urlbase, archive.name)
        return dict(url=url, name=archive.name)

    @classmethod
    def extension_of(cls, path):
        match = cls.EXTS.match(path)
        if match:
            return match.groupdict()['ext']

    @classmethod
    def pkginfo_from_file(cls, path):
        ext = cls.extension_of(path)
        if ext is not None:
            if ext in set(('.gz','.tgz', '.bz2', '.zip')):
                return pkginfo.sdist.SDist(path)
            elif ext == '.egg':
                return pkginfo.bdist.BDist(path)
        raise RuntimeError("Unrecognized extension: %s" %path)


@subscriber(event.IPackageAdded)
def rebuild_leaf(event):
    return event.im.regenerate_leaf(event.name)


class EnvFactory(object):
    env_class = jinja2.Environment
    def __init__(self, config):
        self.config = config

    @property
    def loaders(self):
        if self.config:
            loaders = self.config.split(' ')
            for loader in loaders:
                spec = loader.split(':')
                if len(spec) == 1:
                    yield jinja2.FileSystemLoader(spec); continue

                type_, spec = spec
                if type_ == "file":
                    yield jinja2.FileSystemLoader(spec); continue

                if type_ == 'pkg':
                    spec = spec.split('#')
                    if len(spec) == 1: yield jinja2.PackageLoader(spec[0])
                    else: yield jinja2.PackageLoader(*spec)
                    continue
                raise RuntimeError('Loader type not found: %s %s' %(type_, spec))

    @classmethod
    def from_str(cls, config=None):
        factory = cls(config)
        choices = [jinja2.PackageLoader('cheeseprism', 'templates/index')]
        if config: [choices.insert(0, loader) for loader in factory.loaders]
        return factory.env_class(loader=jinja2.ChoiceLoader(choices))
