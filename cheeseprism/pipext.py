from cheeseprism.index import IndexManager
from functools import partial
from path import path
from pip.exceptions import DistributionNotFound
from pip.index import PackageFinder
from pip.locations import build_prefix, src_prefix
from pip.req import RequirementSet, parse_requirements
from urllib2 import HTTPError
import logging
import requests
import tarfile
import tempfile
import zipfile


logger = logging.getLogger(__name__)


class RequirementDownloader(object):
    build_dir = path(build_prefix).abspath()
    pkginfo_from_file = IndexManager.pkginfo_from_file
    parse_requirements = staticmethod(parse_requirements)

    def __init__(self, req_set, finder=None, upgrade=False, seen=None):
        #@@ start with req_set??
        self.req_set = req_set
        self.upgrade = False
        download_dir = req_set.download_dir
        self.download_dir = path(download_dir)
        self.finder = finder
        self.seen = seen
        self.skip = []
        if self.seen is None:
            self.seen = set()
        self.errors = []

    # toupe for pip
    options = type('Options', (), dict(skip_requirements_regex='',
                                       default_vcs=''))

    @classmethod
    def req_set_from_file(cls, filename, download_dir, deplinks=None):
        src_dir = path(src_prefix).abspath()

        finder = cls.package_finder(deplinks)

        requirement_set = RequirementSet(
            build_dir=cls.build_dir,
            src_dir=src_dir,
            download_dir=download_dir,
            download_cache=None,
            upgrade=False,
            ignore_installed=True,
            ignore_dependencies=False)

        options = cls.options()
        names = []
        for req in cls.parse_requirements(filename, finder=finder, options=options):
            requirement_set.add_requirement(req)
            names.append(req.req)
        yield requirement_set
        yield finder

    @staticmethod
    def readzip(archive, name):
        return archive.read(name)

    @staticmethod
    def readtar(archive, name):
        return archive.extractfile(name).read()    

    @staticmethod
    def find_file(names, tail):
        try:
            return next(n for n in names if n.endswith(tail))
        except StopIteration:
            return None
        
    @classmethod
    def depinfo_for_file(cls, filename):
        if filename.endswith('.zip'):
            archive = zipfile.ZipFile(filename)
            names = archive.namelist()
            read = partial(cls.readzip, archive)
        elif filename.endswith('gz') or filename.endswith('bz2'):
            archive = tarfile.TarFile.open(filename)
            names = archive.getnames()
            read = partial(cls.readtar, archive)
        dl_file = cls.find_file(names, '.egg-info/dependency_links.txt')
        reqs_file = cls.find_file(names, '.egg-info/requires.txt')        
        deplinks = dl_file and read(dl_file) or ''
        requires = reqs_file and read(reqs_file) or ''
        return [x.strip() for x in deplinks.split('\n') if x],\
               [x.strip() for x in requires.split('\n') if x and not x.startswith('[')]

    def download_url(self, link):
        target_url = link.url.split('#', 1)[0]
        resp = requests.get(target_url)
        logger.info('Downloading: %s' %target_url)
        outfile = self.download_dir / link.filename
        outfile.write_bytes(resp.content)
        # requests.iter_content
        pkginfo = self.pkginfo_from_file(outfile)
        return pkginfo, outfile

    def temp_req(self, name, content=None):
        fp = path(tempfile.gettempdir()) / ('temp-req-%s.txt' %name)
        if content:
            logger.debug("Reqs for %s:\n%s", name, content)
            fp.write_text(content)
        return fp

    def handle_requirement(self, req, finder):
        """
        Download requirement, return a new requirement set of
        requirements dependencies.
        """
        if req.editable:
            msg = "Editables not supported: %s" %req
            logger.warn(msg)
            self.errors.append("%s: %s" %(req, msg)) 
            return

        try:
            url = finder.find_requirement(req, self.upgrade)
        except DistributionNotFound:
            msg = "No distribution found for %s" %req.name
            logger.warn(msg)
            self.errors.append(msg)
            return
        
        if url.md5_hash in self.seen:
            logger.debug('Seen: %s', url)
            self.skip.append(url)
            return 
            
        try:
            pkginfo, outfile = self.download_url(url)
        except HTTPError, e:
            msg = "Issue with download: %s" %e
            logger.error(msg)
            self.errors.append("%s: %s" %(req, msg)) 
            return
        except TypeError:
            raise
        except Exception, e:
            msg = "Issue with archive: %s" %e
            logger.error(msg)
            self.errors.append("%s: %s" %(req, msg)) 
            return

        self.seen.add(outfile.read_md5().encode('hex'))
        deplinks, reqs = self.depinfo_for_file(outfile)
        if not reqs:
            return pkginfo, outfile, None
        
        content = "\n".join(reqs)
        pkg = "%s-%s" %(pkginfo.name, pkginfo.version)
        req_set, _ = self.req_set_from_file(self.temp_req(pkg, content),
                                            self.download_dir,
                                            deplinks=deplinks)
        return pkginfo, outfile, req_set,

    pkg_finder_class = PackageFinder
    index_urls = ['http://pypi.python.org/simple']

    def download_all(self, req_set=None, finder=None):
        if req_set is None:
            req_set = self.req_set
        if finder is None:
            finder = self.finder or self.package_finder(None)

        for req in req_set.requirements.values():
            output = self.handle_requirement(req, finder)
            if output is None:
                continue
            self.seen.add(req)
            pkginfo, outfile, req_set = output
            yield pkginfo, outfile
            if req_set is not None:
                logger.info("Dependencies determined: %s" %req_set.requirements.keys())
                for pkginfo, outfile in self.download_all(req_set, finder):
                    yield pkginfo, outfile

    @classmethod
    def package_finder(cls, deplinks, index_urls=None):
        iu = [x for x in cls.index_urls]
        if index_urls:
            iu.extend(index_urls)
        finder = cls.pkg_finder_class(find_links=[], index_urls=iu)
        if deplinks:
            finder.add_dependency_links(deplinks)
        return finder



