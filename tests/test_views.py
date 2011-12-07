from cheeseprism.resources import App
from pyramid import testing
import unittest


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
        from cheeseprism.views import index
        request = testing.DummyRequest()
        assert index(App(request), request) == {}

    def test_regenerate(self):
        raise NotImplementedError
