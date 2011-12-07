from cheeseprism import arch
from jinja2 import Template
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

    def _get_default_template_dir(self):
        pass
    
    def __init__(self, index_path, template_path=None):
        if template_path is None:
            self.template_path = self._get_default_template_dir()
        self.path = path(index_path)
        if not self.path.exists():
            self.path.makedirs()        

    def leaf_template(self):
        pass

    def home_template(self):
        pass

    @property
    def file_pattern(self):
        return 

    @property
    def files(self):
        return (x for x in self.path.files() if self.EXTS.match(x))

    @classmethod
    def regenerate(cls, indexpath):
        #@@ refactor into class
        logger.info('Regenerate instance')
        im = cls(indexpath)

        projects = {}

        for item in im.files:
            tempdir = tempfile.mkdtemp()
            itempath = indexpath / item
            logger.debug("Processing %s", itempath)
            project, revision = im.extract_name_version(itempath, tempdir)
            projects.setdefault(project, []).append((revision, item))
            path(tempdir).rmtree()
##             except:
##                 import traceback
##                 tb = traceback.format_exc()
##                 logger.error(tb)

        items = sorted(projects.items())

        #@@ <needs to be templatized >
        f = indexpath / im.root_index_file
        f.write_lines(['<html>\n',
                        '<body>\n',
                        '<h1>Package Index</h1>\n',
                        '<ul>\n'])

        for key, value in items:
            dirname = indexpath / key
            if not dirname.exists():
                dirname.makedirs()
            f.write_text('<li><a href="%s/index.html">%s</a>\n' % (key, key), append=True)
            sub = indexpath / key / 'index.html' 
            sub.write_lines(['<html>\n',
                            '<body>\n',
                            '<h1>%s Distributions</h1>\n' % key,
                            '<ul>\n'])
            for revision, archive in value:
                logger.info('  -> %s, %s', revision, archive)
                sub.write_text('<li><a href="../%s">%s</a>\n' % (archive.name, archive.name), append=True)

            sub.write_lines(['</ul>',
                            '</body>',
                            '</html>'], append=True)
        f.write_lines(['</ul>',
                        '</body>',
                        '</html>'], append=True)
    #@@ </needs to be templatized >    

    @staticmethod
    def extract_name_version(filename, tempdir):
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
