import unittest

class TestUpdict(unittest.TestCase):

    def makeone(self):
        from cheeseprism.desc import updict
        self.seed = dict(default=True)

        class Obj(object):
            attr = updict(self.seed)

        self.klass = Obj
        return Obj()

    def setUp(self):
        self.test_obj = self.makeone()
    
    def test_get(self):
        assert 'default' in self.test_obj.attr
        assert self.klass.attr is self.test_obj.attr

    def test_set(self):
        self.test_obj.attr = dict(add=1)
        assert 'add' in self.test_obj.attr

    def test_del(self):
        self.test_obj.attr = dict(add=1)
        assert 'add' in self.test_obj.attr
        del self.test_obj.attr
        assert not 'add' in self.test_obj.attr
