from cheeseprism import index
from cheeseprism.resources import App
from mock import Mock
from mock import patch
from nose.tools import raises
from path import path
from pyramid import testing
from pyramid.decorator import reify
from pyramid.events import subscriber
from pyramid.httpexceptions import HTTPFound
from test_pipext import PipExtBase
import itertools
import unittest

class CPDummyRequest(testing.DummyRequest):
    test_dir = None
    counter = itertools.count()
    env = None
    _index_data = {}

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
        return self.file_root / 'index.json'

    @reify
    def index_data(self):
        return self._index_data


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
        CPDummyRequest._index_data = {}

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

    @patch('cheeseprism.rpc.PyPi.package_details')
    def test_package_no_details(self, pd):
        """
        pypi doesn't know anything about our package
        """
        from cheeseprism.views import package
        pd.return_value = None
        request = testing.DummyRequest()
        request.matchdict.update(dict(name='boto',
                                      version='1.2.3'))
        out = package(request)
        assert isinstance(out, HTTPFound)
        assert out.location == '/find-packages'

    @patch('cheeseprism.rpc.PyPi.package_details')
    def test_package_md5_matches(self, pd):
        """
        package is already in index
        """
        from cheeseprism.views import package
        td = dict(name='boto',
                  version='1.2.3',
                  md5_digest='12345')
        pd.return_value = [td]        
        request = CPDummyRequest()
        request.matchdict.update(td)
        request.index_data.update({'12345':True})
        out = package(request)
        assert isinstance(out, HTTPFound)
        assert out.location == '/index/boto'

    @patch('cheeseprism.rpc.PyPi.package_details')
    def test_package_httperror(self, pd):
        """
        package: test catching httperror
        """
        request = self.package_request(pd)
        with patch('requests.get') as get:
            from cheeseprism import views; reload(views)
            get.side_effect = views.HTTPError('http://boto', 500, 'KABOOM', dict(), None)
            out = views.package(request)
        assert isinstance(out, HTTPFound)

    @patch('cheeseprism.rpc.PyPi.package_details')
    def test_package_urlerror(self, pd):
        """
        package: test catching urlerror
        """
        request = self.package_request(pd)
        with patch('requests.get') as get:
            from cheeseprism import views; reload(views)
            get.side_effect = views.URLError('kaboom')
            out = views.package(request)
        assert isinstance(out, HTTPFound)
        assert out.location == '/find-packages'

    @patch('cheeseprism.rpc.PyPi.package_details')
    def test_package_good(self, pd):
        """
        package: test catching urlerror
        """
        request = self.package_request(pd)
        request.file_root.mkdir()
        with patch('requests.get') as get:
            resp = get.return_value = Mock('response')
            resp.content = PipExtBase.dists['dp'].bytes()
            from cheeseprism import views; reload(views)
            out = views.package(request)
        assert isinstance(out, HTTPFound)
        assert out.location == '/index/boto'

    @patch('cheeseprism.rpc.PyPi.package_details')
    def test_package_downloads_ok_but_bad(self, pd):
        """
        package: test catching urlerror
        """
        request = self.package_request(pd)
        request.file_root.mkdir()
        with patch('requests.get') as get:
            resp = get.return_value = Mock('response')
            resp.content = PipExtBase.dists['dp'].bytes()
            from cheeseprism import views; reload(views)
            with patch('cheeseprism.index.IndexManager.pkginfo_from_file') as pkff:
                pkff.side_effect = ValueError("KABOOM")
                out = views.package(request)
        assert isinstance(out, HTTPFound)
        assert out.location == '/find-packages'

    def package_request(self, pd, td=None):
        if td is None:
            td = dict(name='boto',
                      version='1.2.3',
                      md5_digest='12345',
                      url='http://boto',
                      filename='boto-1.2.3.tar.gz')
        pd.return_value = [td]
        request = CPDummyRequest()
        request.matchdict.update(td)
        return request

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
