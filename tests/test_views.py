from cheeseprism.resources import App
from path import path
from pyramid import testing
from pyramid.httpexceptions import HTTPFound
import itertools
import unittest


class CPDummyRequest(testing.DummyRequest):
    settings = {}
    counter = itertools.count()

    @property
    def file_root(self):
        test_dir = getattr(self, 'test_dir', None)
        if test_dir is None:
            test_dir = '%s-view-tests' %next(self.counter)
            self.test_dir = test_dir = path(__file__).parent / "test-indexes" / test_dir
        return test_dir
    

class ViewTests(unittest.TestCase):

    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

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
        from cheeseprism.views import regenerate_index
        out = regenerate_index(*self.base_cr)
        assert isinstance(out, dict)
        assert not out
        context, req = self.base_cr
        req.method = "POST"

        out = regenerate_index(context, req)
        assert isinstance(out, HTTPFound)
        assert len(req.file_root.files()) == 1
        assert req.file_root.files()[0].name == 'index.html'
        req.file_root.rmtree()
