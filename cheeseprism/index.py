"""
Classes, subscribers and functions for dealing with index management
"""
from cheeseprism import event
from cheeseprism.desc import template
from cheeseprism.desc import updict
from functools import partial
from path import path
from pyramid import threadlocal
from pyramid.events import ApplicationCreated
from pyramid.events import subscriber
import jinja2
import json
import logging
import pkginfo
import re
import threading
import time
import traceback


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
    datafile_name = "index.json"
    index_data_lock = threading.Lock()

    leaf_template = template('leaf.html')
    home_template = template('home.html')

    def __init__(self, index_path, template_env=None, arch_baseurl='/index/', urlbase='',
                 index_data={}, leaf_data={}, error_folder='_errors'):
        self.urlbase = urlbase
        self.arch_baseurl = arch_baseurl
        self.template_env = template_env
        if not self.template_env:
            self.template_env = self.default_env_factory('')
        self.index_data = index_data.copy()            
        self.leaf_data = leaf_data.copy()
        self.path = path(index_path)
        self.datafile_path = self.path / self.datafile_name
        if not self.path.exists():
            self.path.makedirs()
        self.error_folder = self.path / error_folder
        self.move_on_error = partial(self.move_on_error, self.error_folder)

    @classmethod
    def from_settings(cls, settings):
        file_root = path(settings['cheeseprism.file_root'])
        if not file_root.exists():
            file_root.makedirs()

        urlbase = settings.get('cheeseprism.urlbase', '')
        abu = settings.get('cheeseprism.archive.urlbase', '..')
        return cls(settings['cheeseprism.file_root'],
                   urlbase=urlbase,
                   arch_baseurl=abu,
                   template_env=settings['cheeseprism.index_templates'])

    @staticmethod
    def move_on_error(error_folder, exc, path):
        logger.error(traceback.format_exc())
        path.rename(error_folder)
    
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
        data['packages'] = [dict(name=key, url=str(path(self.urlbase) / key )) \
                            for key, value in items]
        home_file.write_text(self.home_template.render(**data))
        return home_file

    def write_leaf(self, leafdir, versions, indexhtml="index.html", indexjson="index.json"):
        if not leafdir.exists():
            leafdir.makedirs()

        leafhome = leafdir / indexhtml
        leafjson = leafdir / indexjson

        versions = list(versions)
        title = "%s:%s" %(self.index_data['title'], leafdir.name)
        tversions = (self.leaf_values(leafdir.name, archive)\
                     for info, archive in versions)

        text = self.leaf_template\
               .render(package_title=leafdir.name,
                       title=title,
                       versions=tversions)

        leafhome.write_text(text)
        with self.index_data_lock: #@@ more granular locks
            with open(leafjson, 'w') as jsonout:
                leafdata = [dict(filename=str(fpath.name),
                                 name=dist.name,
                                 version=dist.version,
                                 mtime=fpath.mtime,
                                 ctime=fpath.ctime,
                                 atime=fpath.ctime,
                                 ) for dist, fpath in versions]
                json.dump(leafdata, jsonout)
                
        leafhome.utime((time.time(), time.time()))
        return leafhome

    def leaf_values(self, leafname, archive):
        url = str(path(self.arch_baseurl) / archive.name)
        return dict(url=url, name=archive.name)

    @classmethod
    def extension_of(cls, path):
        match = cls.EXTS.match(path)
        if match:
            return match.groupdict()['ext']

    @classmethod
    def pkginfo_from_file(cls, path, handle_error=None):
        ext = cls.extension_of(path)
        try:
            if ext is not None:
                if ext in set(('.gz','.tgz', '.bz2', '.zip')):
                    return pkginfo.sdist.SDist(path)
                elif ext == '.egg':
                    return pkginfo.bdist.BDist(path)
        except Exception, e:
            if handle_error is not None:
                return handle_error(e, path)
            raise 
        raise RuntimeError("Unrecognized extension: %s" %path)

    @staticmethod
    def data_from_path(datafile):
        datafile = path(datafile)
        if datafile.exists():
            with open(datafile) as stream:
                return json.load(stream)
        logger.error("No datafile found for %s", datafile)
        return {}

    def write_datafile(self, **data):
        with self.index_data_lock:
            if self.datafile_path.exists():
                newdata = data
                with open(self.datafile_path) as root:
                    data = json.load(root)
                    data.update(newdata)
            with open(self.datafile_path, 'w') as root:
                json.dump(data, root)
            return data
        
    def register_archive(self, arch, registry=None):
        """
        Adds an archive to the master data store (index.json)
        """
        pkgdata = self.arch_to_add_map(arch)
        md5 = arch.read_md5().encode('hex')

        self.write_datafile(**{md5:pkgdata})
        return pkgdata, md5

    def arch_to_add_map(self, arch):
        start = time.time()
        pkgi = self.pkginfo_from_file(arch, self.move_on_error)
        if pkgi:
            pkgdata = dict(name=pkgi.name,
                           version=pkgi.version,
                           filename=str(arch.name),
                           added=start)
            return pkgdata

    def update_data(self, datafile=None):
        if datafile is None:
            datafile = self.datafile_path
        start = time.time()
        with self.index_data_lock:
            data = self.data_from_path(datafile)
            new = []
            for arch in self.files:
                md5 = arch.read_md5().encode('hex')
                if not arch.exists():
                    del data[md5]
                    
                if not md5 in data:
                    pkgdata = self.arch_to_add_map(arch)
                    if pkgdata:
                        data[md5] = pkgdata
                        new.append(pkgdata)

            pkgs = len(set(x['name'] for x in data.values()))
            logger.info("Inspected %s versions for %s packages" %(len(data), pkgs))
            with open(datafile, 'w') as root:
                json.dump(data, root)
                
        elapsed = time.time() - start
        logger.info("Generate json representation of index in %s seconds" %elapsed)
        return new


@subscriber(event.IPackageAdded)
def rebuild_leaf(event):
    return event.im.regenerate_leaf(event.name)


@subscriber(event.IIndexUpdate)
def bulk_update_index(event):
    new_pkgs = event.index.update_data(event.datafile)
    return list(notify_packages_added(event.index, new_pkgs))


def notify_packages_added(index, new_pkgs, reg=None):
    if reg is None:
        reg = threadlocal.get_current_registry()    
    for data in new_pkgs:
        yield reg.notify(event.PackageAdded(index,
                                            name=data['name'],
                                            version=data['version']))


@subscriber(ApplicationCreated)
def bulk_update_index_at_start(event):
    reg = event.app.registry
    settings = reg.settings
    
    index = IndexManager.from_settings(settings)

    new_pkgs = index.update_data()
    pkg_added = list(notify_packages_added(index, new_pkgs, reg))

    home_file = index.path / index.root_index_file
    if not home_file.exists():
        items = index.projects_from_archives()
        index.write_index_home(home_file, items)    
    return pkg_added


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



