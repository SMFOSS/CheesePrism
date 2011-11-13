import unittest
from pyramid import testing
from pyramid.i18n import TranslationStringFactory
from __init__ import get_app
from indexer import PackageRoot
import tempfile
import os
import settings

_ = TranslationStringFactory('cheeseprism')

class ViewTests(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        self.App = get_app({})

    def tearDown(self):
        testing.tearDown()

    def test_search_view(self):
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

class PackageRootTest(unittest.TestCase):

    def test_package_root_yaml_from_list(self):
        list = ["pv1", "pv2",]
        root = PackageRoot('packageName')
        yaml_obj = root._get_yaml(list)
        expected = "packages: [pv1, pv2]\n"
        self.assertEqual(yaml_obj, expected)

    def test_add_node(self):
        path = self._write_yaml('packages: [bean, frank]')
        root = PackageRoot(path)
        root.load()
        result = root.add_node('rice')
        self.assertTrue('rice' in result)

    def _write_yaml(self, yaml_string = None):
        if (not yaml_string):
            yaml_string  = "packages: [pv1, pv2]"
        dir = tempfile.mkdtemp()
        path = os.path.join(dir, settings.YAML_FILE_NAME)
        with open(path, "w") as f:
            f.write(yaml_string)
        return dir

    def test_load_yaml(self):
        expected = "packages: [pv1, pv2]\n"
        path = self._write_yaml(expected)
        root = PackageRoot(path)
        y = root._load_yaml_str()
        self.assertEqual(y, expected)

    def test_load(self):
        yam = 'packages: [pv1, pv2]'
        path = self._write_yaml(yam)
        root = PackageRoot(path)
        list = root.load()
        self.assertTrue('pv1' in list)
        self.assertTrue('pv2' in list)

    def test_write_yaml(self):
        packages = ['dookie', 'burger']
        dir = tempfile.mkdtemp()
        p = PackageRoot(dir)
        p._write_yaml(packages, dir)
        result = p.load()
        self.assertTrue('dookie' in result)
        self.assertTrue('burger' in result)
