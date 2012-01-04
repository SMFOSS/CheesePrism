from cheeseprism.utils import resource_spec
from itertools import count
from mock import Mock
from mock import patch
from nose.tools import raises
from path import path
from pip.exceptions import DistributionNotFound
from pip.index import Link
from pip.index import PackageFinder
from pprint import pformat as pp
from urllib2 import HTTPError
import logging
import pkginfo
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
        if not self.download_dir.exists():
            self.download_dir.makedirs()
        
    def tearDown(self):
        logger.debug("teardown: %s", self.count)
        dirs = self.base.dirs()
        logger.info(pp(dirs))
        logger.info(pp([x.rmtree() for x in dirs]))


class TestReqDownloader(PipExtBase):
    """
    Catch all coverage tests for RequirementsDownloader
    """
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

    @patch('requests.get')
    def test_download_url(self, mockget):
        mockget.return_value = Mock()
        mockget.return_value.content = self.dists['dp'].bytes() 
        rd = self.makeone()
        pinfo, outfile = rd.download_url(Link('http://fakeurl.com/dummypackage.tar.gz#egg=dummypackage'))
        assert outfile.exists()
        assert pinfo.name == 'dummypackage'

    def test_readzip(self):
        rd = self.makeone()
        archive, name = Mock(), 'blah'
        out = rd.readzip(archive, name)
        assert out
        method, args, _ = archive.method_calls[0]
        assert method == 'read'
        assert args == (name,)

    @patch('zipfile.ZipFile')
    def test_depinfo_for_zip(self, zfmock):
        from cheeseprism import pipext
        zfmock.return_value = ZFMock()
        assert pipext.RequirementDownloader.depinfo_for_file('fake.zip') == ([], [])

    def test_package_finder_cm(self):
        from cheeseprism import pipext
        pf = pipext.RequirementDownloader.package_finder
        finder = pf(deplinks=['a deplink'], index_urls=['an index_url'])
        assert finder.dependency_links == ['a deplink']
        assert finder.index_urls == ['http://pypi.python.org/simple', 'an index_url']


class ZFMock(Mock):
    namelist = lambda self: []
    read = lambda self, name : ""
    

@patch('cheeseprism.pipext.RequirementDownloader.download_url')
class TestReqDownloaderHandler(PipExtBase):

    @property
    def mock_finder(self):
        self.link = Link('http://pkgurl/pkg.tar.gz#md5=12345')
        finder = Mock(spec_set=PackageFinder)
        finder.find_requirement.return_value = self.link
        return finder
    
    def raise_http_error(self, url, *args, **kw):
        raise HTTPError(url, 500, 'kaboom: %s %s' %(pp(args), pp(kw)), dict(), None)

    def get_pkginfo(self, dist):
        pkg = self.dists[dist]
        return pkginfo.sdist.SDist(pkg)

    def test_editable_req_error(self, download_url):
        rd = self.makeone()
        req = rd.req_set.requirements.values().pop()
        req.editable = True
        assert rd.handle_requirement(req, self.mock_finder) is None
        assert rd.errors
        assert 'Editable' in rd.errors[0]

    def raise_distnotfound(self, *args, **kw):
        raise DistributionNotFound("not found")

    def test_distribution_notfound_error(self, download_url):
        finder = self.mock_finder
        rd = self.makeone()
        finder.find_requirement.side_effect = self.raise_distnotfound
        req = rd.req_set.requirements.values().pop()
        download_url.return_value = (self.get_pkginfo('dp'), self.dists['dp']) # for failing test
        assert rd.handle_requirement(req, finder) is None

    def basic_prep(self, download_url):
        rd = self.makeone()
        req = rd.req_set.requirements.values().pop()
        download_url.return_value = (self.get_pkginfo('dp'), self.dists['dp'])
        return rd, req
        
    def test_skip(self, download_url):
        rd, req = self.basic_prep(download_url)
        finder = self.mock_finder
        rd.seen.add(self.link.md5_hash)
        assert rd.handle_requirement(req, finder) is None

    @raises(TypeError)
    def test_typeerror_raise(self, download_url):
        """
        Testing formality to make sure our diaper does not hide our
        mocks.
        """
        rd, req = self.basic_prep(download_url)
        download_url.side_effect = TypeError('Kaboom')
        assert rd.handle_requirement(req, self.mock_finder) is None

    def test_general_download_exception(self, download_url):
        """
        Check the diaper records what is dumped into it.

        At this point in `handle_requirements`, weird stuff happens
        with peoples distributions.  We can't save the world, but we
        can catch their crap and let the rest of the downloads
        continue.
        """
        rd, req = self.basic_prep(download_url)
        download_url.side_effect = Exception('Kaboom')
        assert rd.handle_requirement(req, self.mock_finder) is None
        assert len(rd.errors) == 1
        assert 'archive' in rd.errors[0]
        
        
    def test_handle_requirement_httperror(self, download_url):
        rd = self.makeone()
        req = rd.req_set.requirements.values().pop()
        download_url.side_effect = self.raise_http_error
        assert rd.handle_requirement(req, self.mock_finder) is None
        assert len(rd.errors) == 1
        assert 'download' in rd.errors[0]

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


@patch('cheeseprism.pipext.RequirementDownloader.handle_requirement')
class TestReqDownloaderAll(PipExtBase):

    @raises(StopIteration)
    def test_download_all_nothing(self, handle):
        handle.return_value = None
        rd = self.makeone()
        next(rd.download_all())

    def test_download_single_pkg(self, handle):
        marker = object()
        handle.return_value = marker, marker, None, 
        rd = self.makeone()
        output = [x for x in rd.download_all()]
        assert len(output) == 1
        assert output[0] == (marker, marker)

    def test_download_w_deps(self, handle):
        marker1 = object()
        handle.return_value = marker1, marker1, RSMock, 
        rd = self.makeone()

        out_gen = rd.download_all()
        assert next(out_gen) == (marker1, marker1)
        
        marker2 = object()
        handle.return_value = marker2, marker2, None,         
        assert next(out_gen) == (marker2, marker2)

class RSMock(Mock):
    requirements = dict(something_else="something_else_requirement")
