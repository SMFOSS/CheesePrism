from cheeseprism.indexer import PackageRoot
from path import path


class RootWalker(object):
    def __init__(self, dir):
        self.dir = dir
        self.root_package = PackageRoot(self.dir)

    def write_root_yaml(self, files):
        raise NotImplementedError

    def walk(self):
        for filename in path(self.dir).files():
            self.root_package.add_node(filename)
        return self.root_package.packages
