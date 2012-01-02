from cheeseprism.utils import resource_spec
from itertools import count
from mock import Mock
from mock import patch
from path import path
from pprint import pformat as pp
from urllib2 import HTTPError
import pkginfo
import logging
import unittest

logger = logging.getLogger(__name__)
here = path(__file__).parent


class PipExtBase(unittest.TestCase):
    counter = count()
    index_parent = "egg:CheesePrism#tests/test-indexes"
    dists = dict(dp=(here / 'dummypackage/dist/dummypackage-0.0dev.tar.gz'),
                 dp2=(here / 'dummypackage2/dist/dummypackage-0.1.tar.gz'),
                 se=(here / 'something_else/dist/something_else-2.0.tar.gz'))

    filename = here / 'req-1.txt'

    @classmethod
    def get_base(cls):
        return path(resource_spec(cls.index_parent))

    @property
    def base(self): return self.get_base()
    
    def makeone(self, dd=None):
        from cheeseprism import pipext
        rs, finder = self.make_finder_and_reqset()
        return pipext.RequirementDownloader(rs, finder=finder)

    def make_finder_and_reqset(self):
        from cheeseprism import pipext
        return pipext.RequirementDownloader.req_set_from_file(self.filename, self.download_dir)

    def setUp(self):
        self.count = next(self.counter)
        self.download_dir = self.base / ("%s-%s" %(self.count, 'req-dl'))
        
    def tearDown(self):
        logger.debug("teardown: %s", self.count)
        dirs = self.base.dirs()
        logger.info(pp(dirs))
        logger.info(pp([x.rmtree() for x in dirs]))


class TestReqDownloader(PipExtBase):
    def test_init(self):
        """
        Sanity test creation
        """
        rd = self.makeone()
        reqs = rd.req_set.requirements
        assert len(reqs.values()) == 1
        assert reqs.keys() == ['dummypackage'], reqs.keys()
        self.download_dir = None
        rd = self.makeone(dd='')


@patch('cheeseprism.pipext.RequirementDownloader.download_url')
class TestReqDownloaderHandler(PipExtBase):

    @property
    def mock_finder(self):
        finder = Mock()
        finder.find_requirement.return_value = 'http://pkgurl'
        return finder
    
    def raise_http_error(self, url, *args, **kw):
        raise HTTPError(url, 500, 'kaboom: %s %s' %(pp(args), pp(kw)), dict(), None)

    def get_pkginfo(self, dist):
        pkg = self.dists[dist]
        return pkginfo.sdist.SDist(pkg)

    def test_handle_requirement_httperror(self, download_url):
        rd = self.makeone()
        req = rd.req_set.requirements.values().pop()
        download_url.side_effect = self.raise_http_error
        assert rd.handle_requirement(req, self.mock_finder) is None
        assert req in rd.errors

    def test_handle_requirement_noreqs(self, download_url):
        rd = self.makeone()
        req = rd.req_set.requirements.values().pop()
        download_url.return_value = (self.get_pkginfo('dp'), self.dists['dp'])
        (pkginfo, path_to_sdist, deps) = rd.handle_requirement(req, self.mock_finder)
        assert deps is None, deps
        assert pkginfo.name == 'dummypackage'
        assert path_to_sdist == self.dists['dp']

    def test_handle_requirement_w_reqs(self, download_url):
        rd = self.makeone()
        req = rd.req_set.requirements.values().pop()
        download_url.return_value = (self.get_pkginfo('dp2'), self.dists['dp2'])
        (pkginfo, path_to_sdist, deps) = rd.handle_requirement(req, self.mock_finder)
        assert pkginfo.name == 'dummypackage'
        assert path_to_sdist == self.dists['dp2']
        assert deps.requirements.keys() == ['something-else'], deps.requirements.keys()


