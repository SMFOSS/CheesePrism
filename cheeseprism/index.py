from cheeseprism import EnvFactory
from cheeseprism import arch
from cheeseprism.desc import updict 
from path import path
import logging
import os
import re
import subprocess
import sys
import tempfile

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
        if self.template_env is None:
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
    def file_pattern(self):
        return 

    @property
    def files(self):
        return (x for x in self.path.files() if self.EXTS.match(x))

    def load_projects(self):
        projects = {}
        for item in self.files:
            tempdir = tempfile.mkdtemp()
            itempath = self.path / item
            logger.debug("Processing %s", itempath)
            project, revision = self.extract_name_version(itempath, tempdir)
            projects.setdefault(project, []).append((revision, item))
            path(tempdir).rmtree()
        return sorted(projects.items())

    @classmethod
    def regenerate(cls, indexpath, template_env=None):
        logger.info('Regenerate instance')
        im = cls(indexpath, template_env)

        items = im.load_projects()
        home_file = indexpath / im.root_index_file

        yield im.write_index_home(home_file, items)
        yield [im.write_leaf(indexpath / key, value) for key, value in items]

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
        data = dict(package_title=leafdir.name,
                    title="%s:%s" %(self.index_data['title'], leafdir.name),
                    versions=[self.leaf_values(leafdir.name, archive)\
                              for revision, archive in versions])
        text = self.leaf_template.render(**data)
        leafhome.write_text(text)
        return leafhome

    def leaf_values(self, leafname, archive):
        url = "%s/%s" %(self.urlbase, archive.name)
        return dict(url=url, name=archive.name)

    @staticmethod
    def extract_name_version(filename, tempdir):
        #@@ refactor
        archive = None
        if filename.endswith('.gz') or filename.endswith('.tgz') or filename.endswith('.bz2'):
            archive = arch.TarArchive(filename)

        elif filename.endswith('.egg') or filename.endswith('.zip'):
            archive = arch.ZipArchive(filename)

        if archive is None:
            return
        try:
            for name in archive.names():
                if len(name.split('/'))==2  and name.endswith('PKG-INFO'):
                    project, version = None, None
                    lines = archive.lines(name)
                    for line in lines:
                        key, value = line.split(':', 1)
                        if key == 'Name':
                            print filename, value
                            project = value.strip()

                        elif key == 'Version':
                            version = value.strip()

                        if project is not None and version is not None:
                            return project, version
                        continue

            archive.extractall(tempdir)
            dirs = os.listdir(tempdir)
            dir = os.path.join(tempdir, dirs[0])
            if not os.path.isdir(dir):
                dir = tempdir
            command = ('cd %s && %s setup.py --name --version'
                           % (dir, sys.executable))
            popen = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    shell=True,
                                    )
            output = popen.communicate()[0]
            archive.close()
            return output.splitlines()[:2]
        except:
            archive.close()
            import traceback
            print traceback.format_exc()
        return

regenerate = IndexManager.regenerate
