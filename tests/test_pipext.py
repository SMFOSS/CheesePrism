from cheeseprism.utils import resource_spec
from itertools import count
from mock import Mock
from mock import patch
from path import path
from pprint import pformat as pp
from urllib2 import HTTPError
import logging
import unittest

logger = logging.getLogger(__name__)


class TestReqDownloader(unittest.TestCase):
    counter = count()
    index_parent = "egg:CheesePrism#tests/test-indexes"

    @classmethod
    def get_base(cls):
        return path(resource_spec(cls.index_parent))

    @property
    def base(self): return self.get_base()
    
    def makeone(self, filename=path(__file__).parent / 'req-1.txt'):
        from cheeseprism import pipext
        rs, finder = pipext.RequirementDownloader.req_set_from_file(filename, self.download_dir)
        return pipext.RequirementDownloader(rs, self.download_dir, finder=finder)

    def setUp(self):
        self.count = next(self.counter)
        self.download_dir = self.base / ("%s-%s" %(self.count, 'req-dl'))

    def test_init(self):
        """
        Sanity test creation
        """
        rd = self.makeone()
        reqs = rd.req_set.requirements
        assert len(reqs.values()) == 1
        assert reqs.keys() == ['dummypackage'], reqs.keys()

    @property
    def mock_finder(self):
        finder = Mock()
        finder.find_requirement.return_value = 'http://pkgurl'
        return finder
    
    def raise_http_error(self, url, *args, **kw):
        raise HTTPError(url, 500, 'kaboom: %s %s' %(pp(args), pp(kw)), dict(), None)

    @patch('cheeseprism.pipext.RequirementDownloader.download_url')
    def test_handle_requirement_httperror(self, download_url):
        rd = self.makeone()
        req = rd.req_set.requirements.values().pop()
        download_url.side_effect = self.raise_http_error
        assert rd.handle_requirement(req, self.mock_finder) is None
        assert req in rd.errors

    def tearDown(self):
        logger.debug("teardown: %s", self.count)
        dirs = self.base.dirs()
        logger.info(pp(dirs))
        logger.info(pp([x.rmtree() for x in dirs]))
