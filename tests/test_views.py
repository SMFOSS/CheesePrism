from cheeseprism.resources import App
from cheeseprism import EnvFactory
from path import path
from pyramid import testing
from pyramid.httpexceptions import HTTPFound
import itertools
import unittest


class CPDummyRequest(testing.DummyRequest):
    settings = {}
    counter = itertools.count()
    env = None
    test_dir = None
    
    @property
    def file_root(self):
        test_dir = getattr(self, 'test_dir')
        if test_dir is None:
            test_dir = '%s-view-tests' %next(self.counter)
            self.test_dir = test_dir = path(__file__).parent / "test-indexes" / test_dir
        return test_dir

    @property
    def index_templates(self):
        if self.env is None:
            self.env = EnvFactory.from_str()
        return self.env
    

class ViewTests(unittest.TestCase):

    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        if CPDummyRequest.test_dir is not None:
            CPDummyRequest.test_dir.rmtree()
            CPDummyRequest.test_dir = None

    def test_search_view(self):
        raise NotImplementedError
        from cheeseprism.views import find_packages
        request = testing.DummyRequest()

        request.POST['releases'] = 'pyramid'
        response = find_packages(App(request), request)
        self.assertNotEqual(None, response['releases'])
        self.assertEqual(len(response['releases']), 1)

    def test_index_view(self):
        from cheeseprism.views import homepage as index
        request = testing.DummyRequest()
        assert index(App(request), request) == {}

    @property
    def base_cr(self):
        self.curreq = request = CPDummyRequest()
        return App(request), request

    def test_regenerate_index(self):
        """
        Basic regeneration of entire index
        """
        from cheeseprism.views import regenerate_index
        context, request = self.base_cr
        out = regenerate_index(context, request)
        assert not out
        assert isinstance(out, dict)

        context, req = self.base_cr
        req.method = "POST"
        import pdb;pdb.set_trace()
        out = regenerate_index(context, req)
        assert isinstance(out, HTTPFound)
        assert req.file_root.exists(), "index not created at %s" %req.file_root
        assert len(req.file_root.files()) == 1
        assert req.file_root.files()[0].name == 'index.html'

