from pyramid import testing
from cheeseprism.resources import App
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

        response = index(App(request), request)
        self.assertEqual(response['page'], 'instructions')

    def test_regenerate(self):
        raise NotImplementedError
