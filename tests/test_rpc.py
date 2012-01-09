import unittest 
from mock import patch


class TestPyPiXMLRPC(unittest.TestCase):
    @patch('xmlrpclib.ServerProxy')
    def test_search(self, sp):
        from cheeseprism.rpc import PyPi
        out = PyPi.search('five.intid')
        assert sp.called
        assert out

    @patch('xmlrpclib.ServerProxy')
    def test_details(self, sp):
        from cheeseprism.rpc import PyPi
        out = PyPi.package_details('wicked', '1.0')
        ((index,)), _ = sp.call_args
        assert index == PyPi.index
        assert sp.called
        assert out
