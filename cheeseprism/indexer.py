import yaml
from os import path
import settings

class PackageRoot(object):
    def __init__(self, dir):
        self.dir = dir
        self.head, self.tail = path.split(self.dir)
        self.yaml_path = path.join(self.dir, settings.YAML_FILE_NAME)
        self.packages = set()
        self.loaded = False
        self.saved = False

    def _get_yaml(self, list):
        return yaml.dump({'packages': list})

    def _load_yaml_str(self):
        s = yaml.dump(self._load_yaml())
        if(s is None):
            return ''
        else:
            return s

    def _load_yaml(self):
        if (path.exists(self.yaml_path)):
            with file(self.yaml_path, 'r') as stream:
                return yaml.load(stream)
        else:
            return None

    def _get_sorted_set(self, data):
        l = list(data)
        l.sort()
        return set(l)

    def _get_packages(self):
        if(self.loaded):
            return self.packages
        else:
            return self.load()

    def _write_yaml(self, packages = None, dir = None):
        """Writes representitive yaml file.
        :param list: overrides the internal package list.  Good for testing.setUp
        :param dir: your target directory
        """
        packages = (self.packages if packages is None else packages)
        out = {'packages': self._get_sorted_set(packages)}
        out_dir = (self.dir if dir is None else dir)
        p = path.join(out_dir, settings.YAML_FILE_NAME)
        with open(p, "w") as f:
            f.write(yaml.dump(out))
        self.saved = True
        return dir

    def sorted_nodes(self):
        return self._get_sorted_set(self.packages)

    def add_node(self, node):
        packages = self._get_packages()
        packages.add(node)
        self.saved = False
        return self.packages

    def remove_node(self, node):
        packages = self._get_packages()
        packages.discard(node)
        self.saved = False
        return self.packages

    def load(self):
        packages = self._load_yaml()
        if(packages is not None):
            self.packages = set(self._load_yaml()['packages'])
        self.loaded = True
        return self.packages

    def save(self):
        self._write_yaml()
        self.saved = True
        return self.packages

