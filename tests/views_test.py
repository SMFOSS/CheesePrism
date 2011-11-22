from cheeseprism.__init__ import get_app
from pyramid import testing
import unittest

class ViewTests(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        self.App = get_app({})

    def tearDown(self):
        testing.tearDown()

    def test_search_view(self):
        raise NotImplementedError
        from cheeseprism.views import find_packages
        request = testing.DummyRequest()

        request.POST['releases'] = 'pyramid'
        response = find_packages(self.App, request)
        self.assertNotEqual(None, response['releases'])
        self.assertEqual(len(response['releases']), 1)

    def test_index_view(self):
        from cheeseprism.views import index
        request = testing.DummyRequest()

        response = index(self.App, request)
        self.assertEqual(response['page'], 'instructions')

    def test_regenerate(self):
        raise NotImplementedError
