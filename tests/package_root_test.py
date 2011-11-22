import unittest
from pyramid.i18n import TranslationStringFactory
from cheeseprism.indexer import PackageRoot
import tempfile
import os
import cheeseprism.settings as settings

_ = TranslationStringFactory('cheeseprism')

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

    def test_remove_node(self):
        packages = ['dookie', 'burger']
        dir = tempfile.mkdtemp()
        p = PackageRoot(dir)
        p._write_yaml(packages, dir)
        result = p.load()
        p.remove_node('dookie')
        self.assertFalse('dookie' in result)

    def test_save(self):
        dir = tempfile.mkdtemp()
        p = PackageRoot(dir)
        p.add_node('burt')
        p.add_node('renolds')
        p.add_node('rules')
        p.save()
        self.assertTrue(os.path.exists(dir))
        result = p.load()
        self.assertTrue('rules' in result)
