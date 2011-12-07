import os
import tarfile
import zipfile


class TarArchive(object):
    modes = {'.bz2':"r:bz2",
             '.gz':"r:gz",
             '.tgz':"r:gz"}

    default_mode = 'r'
    
    def __init__(self, filename):
        self.filename = filename
        self.tgz = tarfile.TarFile.open(filename, self.mode)

    @classmethod
    def extensions(cls):
        return cls.modes.keys()

    @property
    def mode(self):
        try:
            return next(self.modes[x] for x in self.modes if self.filename.endswith(x))
        except StopIteration:
            return self.default_mode
        
    def names(self):
        return self.tgz.getnames()

    def lines(self, name):
        return self.tgz.extractfile(name).readlines()

    def extract(self, name, tempdir):
        return self.tgz.extract(name, tempdir)

    #@@ use tarfile
    def extractall(self, tempdir):
        os.system('cd %s && tar xzf %s' % (tempdir, 
                                           os.path.abspath(self.filename)))

    def close(self):
        return self.tgz.close()

 
class ZipArchive(object):
    """
    An utility wrapper for zip and eggfile
    """
    ext = '.zip','.egg',

    @classmethod
    def extensions(cls): return cls.ext

    def __init__(self, filename):
        self.filename = filename
        self.zipf = zipfile.ZipFile(filename, 'r')

    def names(self):
        return self.zipf.namelist()

    def lines(self, name):
        return self.zipf.read(name).split('\n')

    def extract(self, name, tempdir):
        data = self.zipf.read(name)
        fn = name.split(os.sep)[-1]
        fn = os.path.join(tempdir, fn)
        f = open(fn, 'wb')
        f.write(data)

    def extractall(self, tempdir):
        os.system('cd %s && unzip %s' % (tempdir, 
                                         os.path.abspath(self.filename)))

    def close(self):
        return self.zipf.close()
