from cheeseprism.__init__ import get_app
from pyramid import testing
from cheeseprism.walker import RootWalker
import unittest
import os
import os.path as path
import tempfile

class RootWalkerTests(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        self.App = get_app({})

    def tearDown(self):
        testing.tearDown()

    def test_walk(self):
        dir = tempfile.mkdtemp()
        packages = ['p1', 'p2', 'p3']
        for p in packages:
            os.makedirs(path.join(dir, p))

        w = RootWalker(dir)
        packages = w.walk()
        self.assertEqual(len(packages), 3)
