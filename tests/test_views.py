from cheeseprism import index
from pyramid.events import subscriber
from cheeseprism.resources import App
from mock import Mock
from mock import patch
from nose.tools import raises
from path import path
from pyramid import testing
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
import itertools
import unittest


class CPDummyRequest(testing.DummyRequest):
    test_dir = None
    counter = itertools.count()
    env = None

    @property
    def userid(self):
        return 'bob'
    
    @property
    def file_root(self):
        test_dir = getattr(self, 'test_dir')
        if test_dir is None:
            test_dir = '%s-view-tests' %next(self.counter)
            self.test_dir = test_dir = path(__file__).parent / "test-indexes" / test_dir
        return test_dir

    @property
    def index_templates(self):
        if self.env is None:
            self.env = index.EnvFactory.from_str()
        return self.env

    @property
    def index(self):
        return index.IndexManager(self.file_root, template_env=self.index_templates)

    @reify
    def response(self):
        return DummyResponse()

    @reify
    def index_data_path(self):
        return self.file_root / 'data.json'
    

class DummyResponse(object):
    def __init__(self):
        self.headers = {}


class FakeFS(object):
    def __init__(self, path):
        self.filename = path.name
        self.file = Mock()
        self.file.read.return_value = "Some gzip binary"


def test_instructions():
    from cheeseprism.views import instructions
    assert instructions(None, None)


class ViewTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        if CPDummyRequest.test_dir is not None:
            CPDummyRequest.test_dir.rmtree()
            CPDummyRequest.test_dir = None

    @patch('cheeseprism.rpc.PyPi.search')
    def test_find_package(self, search_pypi):
        search_pypi.return_value = ['1.3a2']
        from cheeseprism.views import find_package
        request = testing.DummyRequest()
        request.POST['search_box'] = 'pyramid'
        out = find_package(App(request), request)
        assert out['releases'] == None
        assert out['search_term'] == None

        request.method = 'POST'
        out = find_package(App(request), request)
        assert out['releases'] == ['1.3a2'], "%s != %s" %(out['releases'], ['1.3a2'])
        assert out['search_term'] == 'pyramid'

    def test_index_view(self):
        from cheeseprism.views import homepage as index
        request = testing.DummyRequest()
        assert index(App(request), request) == {}

    @property
    def base_cr(self):
        self.curreq = request = CPDummyRequest()
        return App(request), request

    def test_regenerate_index(self):
        """
        Basic regeneration of entire index
        """
        from cheeseprism.views import regenerate_index
        context, request = self.base_cr
        out = regenerate_index(context, request)
        assert not out
        assert isinstance(out, dict)

        context, req = self.base_cr
        req.method = "POST"

        out = regenerate_index(context, req)
        assert isinstance(out, HTTPFound)
        assert req.file_root.exists(), "index not created at %s" %req.file_root
        assert len(req.file_root.files()) == 1
        assert req.file_root.files()[0].name == 'index.html'

    @raises(RuntimeError)
    def test_upload_raises(self):
        from cheeseprism.views import upload
        context, request = self.base_cr
        request.POST['content'] = ''
        upload(context, request)

    def setup_event(self):
        self.event_results = {}
        from cheeseprism.event import IPackageAdded
        
        @subscriber(IPackageAdded)
        def test_event_fire(event):
            self.event_results['fired'] = True
            
        self.config.add_subscriber(test_event_fire)

    @patch('path.path.write_bytes')
    @patch('pkginfo.sdist.SDist')
    def test_upload(self, sdist, wb):
        from cheeseprism.views import upload
        self.setup_event()
        context, request = self.base_cr
        request.method = 'POST'
        request.POST['content'] = FakeFS(path('dummypackage/dist/dummypackage-0.0dev.tar.gz'))
        res = upload(context, request)
        assert res.headers == {'X-Swalow-Status': 'SUCCESS'}
        assert 'fired' in self.event_results
