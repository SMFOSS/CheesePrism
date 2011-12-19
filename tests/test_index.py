from cheeseprism.utils import resource_spec
from itertools import count
from path import path
from pprint import pformat as pprint
import logging
import textwrap
import unittest


logger = logging.getLogger(__name__)


class IndexTestCase(unittest.TestCase):
    counter = count()
    index_parent = "egg:CheesePrism#tests/test-indexes"

    @classmethod
    def get_base(cls):
        return path(resource_spec(cls.index_parent))

    @property
    def base(self): return self.get_base()
    
    def make_one(self, index_name='test-index'):
        from cheeseprism import index
        self.count = next(self.counter)
        index_path = self.base / ("%s-%s" %(self.count, index_name))
        return index.IndexManager(index_path)

    def setUp(self):
        self.im = self.make_one()
        dummy = path(__file__).parent / "dummypackage/dist/dummypackage-0.0dev.tar.gz"
        dummy.copy(self.im.path)
        self.dummypath = self.im.path / dummy.name

    def test_regenerate_index(self):
        home, leaves = self.im.regenerate(self.im.path)
        pth = self.im.path
        file_structure = [(x.parent.name, x.name) for x in pth.walk()]
        index_name = u'%s-test-index' %self.count
        expected = [(index_name, u'dummypackage'),
                    (u'dummypackage', u'index.html'),
                    (index_name, u'dummypackage-0.0dev.tar.gz'),
                    (index_name, u'index.html')]
        assert len(leaves) == 1
        assert leaves[0].exists()
        assert leaves[0].name == 'index.html'
        assert leaves[0].parent.name == 'dummypackage'
        assert file_structure == expected, \
               textwrap.dedent("""
               File structure does not match::

               expected:

                %s

               actual:

                %s""") %(pprint(expected), pprint(file_structure))

    def test_regenerate_leaf_event(self):
        from cheeseprism.event import PackageAdded
        from cheeseprism.index import rebuild_leaf
        event = PackageAdded(self.im, self.dummypath)
        out = rebuild_leaf(event)

        
        

    def tearDown(self):
        logger.debug("teardown: %s", self.count)
        dirs = self.base.dirs()
        logger.info(pprint(dirs))
        logger.info(pprint([x.rmtree() for x in dirs]))

def test_cleanup():
    assert not IndexTestCase.get_base().dirs()
