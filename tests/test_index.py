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


def test_data_from_path():
    from cheeseprism import index
    datafile = here / 'index.json'
    assert index.IndexManager.data_from_path(datafile) == {}
    datafile.write_text("{}")
    assert index.IndexManager.data_from_path(datafile) == {}


class IndexTestCase(unittest.TestCase):
    counter = count()
    index_parent = "egg:CheesePrism#tests/test-indexes"

    tdir = path(resource_spec('egg:CheesePrism#tests'))
    dummy = here / "dummypackage/dist/dummypackage-0.0dev.tar.gz"
    
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
        #@@ factor out im creation
        self.im = self.make_one()
        self.dummy.copy(self.im.path)
        self.dummypath = self.im.path / self.dummy.name

    def test_register_archive(self):
        pkgdata, md5 = self.im.register_archive(self.dummypath)
        assert md5 == '3ac58d89cb7f7b718bc6d0beae85c282'
        assert pkgdata
        
        idxjson = self.im.data_from_path(self.im.datafile_path)
        assert md5 in idxjson 
        assert idxjson[md5] == pkgdata

    def test_write_datafile(self):
        """
        create and write archive data to index.json 
        """
        data = self.im.write_datafile(hello='computer')
        assert 'hello' in data
        assert self.im.datafile_path.exists()
        assert 'hello' in self.im.data_from_path(self.im.datafile_path)

    def test_write_datafile_w_existing_datafile(self):
        """
        write data to an existing datafile
        """
        data = self.im.write_datafile(hello='computer')
        assert self.im.datafile_path.exists()

        data = self.im.write_datafile(hello='operator')
        assert data['hello'] == 'operator'
        assert self.im.data_from_path(self.im.datafile_path)['hello'] == 'operator'


    def test_regenerate_index(self):
        home, leaves = self.im.regenerate_all()
        pth = self.im.path
        file_structure = [(x.parent.name, x.name) for x in pth.walk()]
        index_name = u'%s-test-index' %self.count
        expected = [(index_name, u'dummypackage'),
                    (u'dummypackage', u'index.html'),
                    (path(u'dummypackage'), path(u'index.json')),                    
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
        reg = getreg.return_value = Mock(name='registry')                
        out = list(notify_packages_added(index, pkgs))

        assert len(out) == 1
        assert getreg.called
        assert reg.notify.called
        (event,), _ = reg.notify.call_args
        assert event.im is index
        assert event.version == '0.1'
        assert event.name == 'pkg'

    @raises(StopIteration)
    def test_notify_packages_added_raises(self):
        from cheeseprism.index import notify_packages_added
        next(notify_packages_added(Mock(name='index'), []))

    def tearDown(self):
        logger.debug("teardown: %s", self.count)
        dirs = self.base.dirs()
        logger.info(pprint(dirs))
        logger.info(pprint([x.rmtree() for x in dirs]))


class ClassOrStaticMethods(unittest.TestCase):

    def test_move_on_error(self):
        from cheeseprism.index import IndexManager
        exc, path = Mock(), Mock()
        IndexManager.move_on_error('errors', exc, path)
        assert path.rename.called
        assert path.rename.call_args[0][0] == 'errors'

    @patch('pkginfo.bdist.BDist', new=Mock(return_value=True))
    def test_pkginfo_from_file_egg(self):
        """
        .pkginfo_from_file: bdist
        """                
        from cheeseprism.index import IndexManager
        assert IndexManager.pkginfo_from_file('blah.egg') is True

    @patch('pkginfo.sdist.SDist', new=Mock(return_value=True))
    def test_pkginfo_from_file_sdist(self):
        """
        .pkginfo_from_file: sdist
        """        
        from cheeseprism.index import IndexManager
        for ext in ('.gz','.tgz', '.bz2', '.zip'):
            assert IndexManager.pkginfo_from_file('blah.%s' %ext) is True

    @raises(RuntimeError)
    def test_pkginfo_from_bad_ext(self):
        """
        .pkginfo_from_file with unrecognized extension
        """
        from cheeseprism.index import IndexManager
        IndexManager.pkginfo_from_file('adfasdkfha.adkfhalsdk')

    @raises(RuntimeError)
    def test_pkginfo_from_no_ext(self):
        """
        .pkginfo_from_file with no extension
        """
        from cheeseprism.index import IndexManager
        IndexManager.pkginfo_from_file('adfasdkfha')        
    
    def test_pkginfo_from_file_exc_and_handler(self):
        """
        .pkginfo_from_file with exception and handler
        """
        from cheeseprism.index import IndexManager
        exc = Exception("BOOM")
        with patch('pkginfo.bdist.BDist', side_effect=exc):
            eh = Mock(name='error_handler')
            IndexManager.pkginfo_from_file('bad.egg', handle_error=eh)
        assert eh.called
        assert eh.call_args[0] == (exc, 'bad.egg'), eh.call_args[0]

    @raises(ValueError)
    def test_pkginfo_from_file_exc(self):
        """
        .pkginfo_from_file with exception and no handler
        """
        from cheeseprism.index import IndexManager
        exc = ValueError("BOOM")
        with patch('pkginfo.bdist.BDist', side_effect=exc):
            IndexManager.pkginfo_from_file('bad.egg')

def test_cleanup():
    assert not IndexTestCase.get_base().dirs()
