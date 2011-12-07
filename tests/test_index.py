from cheeseprism.utils import resource_spec
from itertools import count
from path import path
from pprint import pprint
import unittest


class IndexTestCase(unittest.TestCase):
    counter = count()
    base = "egg:CheesePrism#tests/test-indexes"
    
    def make_one(self, index_name='test-index'):
        from cheeseprism import index
        index_path = path(resource_spec(self.base)) / "%s-%s" %(next(self.counter), index_name) 
        return index.IndexManager(index_path)

    def setUp(self):
        self.im = self.make_one()
        dummy = path(__file__).parent / "dummypackage/dist/dummypackage-0.0dev.tar.gz"
        dummy.copy(self.im.path)
        self.dummypath = self.im.path / dummy.name

    def test_regenerate_index(self):
        self.im.regenerate(self.im.path)
        pth = self.im.path
        file_structure = [(x.parent.name, x.name) for x in pth.walk()]
        expected = [(u'0-test-index', u'dummypackage'),
                    (u'dummypackage', u'index.html'),
                    (u'0-test-index', u'dummypackage-0.0dev.tar.gz'),
                    (u'0-test-index', u'index.html')]
        assert file_structure == expected,  "File structure does not match:\nexpected: %s.\n actual: %s" %(pprint(expected), pprint(file_structure))

        
