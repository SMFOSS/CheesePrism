import unittest
from test_views import CPDummyRequest


class CPBasicAuthTest(unittest.TestCase):
    def makeone(self, check=None):
        from cheeseprism.auth import BasicAuthenticationPolicy as policy
        if check is None:
            check = policy.noop_check
        return policy(check)

    def setUp(self):
        self.req = CPDummyRequest()
        self.req.environ['HTTP_AUTHORIZATION'] = 'Basic d2hpdDpzZWNyZXQ='
        self.req.headers['Authorization'] = 'Basic d2hpdDpzZWNyZXQ='
        self.req.environ['wsgi.version'] = '1.0'

    def test_authenticated_userid(self):
        policy = self.makeone()
        userid = policy.authenticated_userid(self.req)
        assert userid == 'whit'
        
    def test_authenticated_userid_nocred(self):
        policy = self.makeone()
        del self.req.environ['HTTP_AUTHORIZATION'] 
        userid = policy.authenticated_userid(self.req)
        assert userid is None

    def test_get_cred_good(self):
        from cheeseprism.auth import BasicAuthenticationPolicy as policy
        cred = policy._get_credentials(self.req)
        assert cred == {'login': 'whit', 'password': 'secret'}

    def test_get_cred_bad(self):
        from cheeseprism.auth import BasicAuthenticationPolicy as policy

        self.req.environ['HTTP_AUTHORIZATION'] = 'bleh'
        assert policy._get_credentials(self.req) is None

        self.req.environ['HTTP_AUTHORIZATION'] = 'Basic 123'
        assert policy._get_credentials(self.req) is None

        self.req.environ['HTTP_AUTHORIZATION'] = 'Basic d2hpdCtzZWNyZXQ=\n'
        assert policy._get_credentials(self.req) is None

        self.req.environ['HTTP_AUTHORIZATION'] = 'fah nah'
        assert policy._get_credentials(self.req) is None

    def test_effective_principals(self):
        policy = self.makeone()
        princs = policy.effective_principals(self.req)
        assert princs == ['system.Everyone', 'system.Authenticated', 'whit']

    def test_effective_p_without_cred(self):
        self.req.environ['HTTP_AUTHORIZATION'] = 'Basic d2hpdCtzZWNyZXQ=\n'
        policy = self.makeone()
        assert policy.effective_principals(self.req) == ['system.Everyone']

    def test_effective_p_without_groups(self):
        policy = self.makeone(lambda x, y: None)
        assert policy.effective_principals(self.req) == ['system.Everyone']

    def test_unauth_userid(self):
        policy = self.makeone()
        assert 'whit' == policy.unauthenticated_userid(self.req)
        self.req.environ['HTTP_AUTHORIZATION'] = 'Bad Auth'
        assert policy.unauthenticated_userid(self.req) is None


    def test_remember(self):
        policy = self.makeone()
        assert policy.remember(self.req, 'whit') == []

    def test_forget(self):
        policy = self.makeone()
        assert policy.forget(self.req) == [('WWW-Authenticate', 'Basic realm="Realm"')]
        
        
