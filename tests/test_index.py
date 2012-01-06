from cheeseprism.utils import resource_spec
from itertools import count
from mock import Mock
from mock import patch
from nose.tools import raises
from path import path
from pprint import pformat as pprint
import logging
import textwrap
import unittest

logger = logging.getLogger(__name__)

here = path(__file__).parent

class IndexTestCase(unittest.TestCase):
    counter = count()
    index_parent = "egg:CheesePrism#tests/test-indexes"

    tdir = path(resource_spec('egg:CheesePrism#tests'))

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

    def test_data_from_path(self):
        assert self.im.data_from_path(here / 'index.json') == {}

    def test_regenerate_index(self):
        home, leaves = self.im.regenerate_all()
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

    @patch('cheeseprism.index.IndexManager.regenerate_leaf')
    def test_regenerate_leaf_event(self, rl):
        """
        Cover event subscriber
        """
        from cheeseprism.event import PackageAdded
        from cheeseprism.index import rebuild_leaf

        event = PackageAdded(self.im, self.tdir / path('dummypackage2/dist/dummypackage-0.1.tar.gz'))
        out = rebuild_leaf(event)
        assert out is not None
        assert rl.call_args == (('dummypackage',), {})

    def test_regenerate_leaf(self):
        [x for x in self.im.regenerate_all()]
        leafindex = self.im.path / 'dummypackage/index.html'
        new_arch = self.tdir / path('dummypackage2/dist/dummypackage-0.1.tar.gz')
        new_arch.copy(self.im.path)
        added = self.im.path / new_arch.name

        before_txt = leafindex.text()
        info = self.im.pkginfo_from_file(added)
        out = self.im.regenerate_leaf(info.name)
        assert before_txt != out.text()

    @patch('pyramid.threadlocal.get_current_registry')
    def test_notify_packages_added(self, getreg):
        from cheeseprism.index import notify_packages_added
        pkg = dict(name='pkg', version='0.1'); pkgs = pkg,
        index = Mock(name='index')
        getreg.return_value = Mock(name='registry')                
        out = list(notify_packages_added(index, pkgs))

        assert len(out) == 1
        assert getreg.called
        assert 'notify' in getreg.return_value._children
        (event,), _ = getreg.return_value._children['notify'].call_args
        assert event.im is index
        assert event.version == '0.1'
        assert event.name == 'pkg'

    @raises(StopIteration)
    def test_notify_packages_added_raises(self):
        from cheeseprism.index import notify_packages_added
        next(notify_packages_added(Mock(name='index'), []))

    @patch('pkginfo.bdist.BDist', new=Mock(return_value=True))
    def test_pkginfo_from_file_egg(self):
        from cheeseprism.index import IndexManager
        assert IndexManager.pkginfo_from_file('blah.egg') is True

    @patch('pkginfo.sdist.SDist', new=Mock(return_value=True))
    def test_pkginfo_from_file_sdist(self):
        from cheeseprism.index import IndexManager
        for ext in ('.gz','.tgz', '.bz2', '.zip'):
            assert IndexManager.pkginfo_from_file('blah.%s' %ext) is True

    @raises(RuntimeError)
    def test_pkginfo_from_bad_ext(self):
        from cheeseprism.index import IndexManager
        IndexManager.pkginfo_from_file('adfasdkfha.adkfhalsdk')

    @raises(RuntimeError)
    def test_pkginfo_from_no_ext(self):
        from cheeseprism.index import IndexManager
        IndexManager.pkginfo_from_file('adfasdkfha')        

    def tearDown(self):
        logger.debug("teardown: %s", self.count)
        dirs = self.base.dirs()
        logger.info(pprint(dirs))
        logger.info(pprint([x.rmtree() for x in dirs]))



def test_cleanup():
    assert not IndexTestCase.get_base().dirs()
