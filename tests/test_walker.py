from cheeseprism.walker import RootWalker
from path import path
import tempfile
import unittest


class RootWalkerTests(unittest.TestCase):

    def test_walk(self):
        dir = tempfile.mkdtemp()
        packages = ['p1', 'p2', 'p3']
        for p in packages:
            (path(dir) / p).makedirs()

        w = RootWalker(dir)
        packages = w.walk()
        self.assertEqual(len(packages), 3)
