from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implements

class IIndexEvent(Interface):
    """
    An lower level event involving the index
    """

class IIndexUpdate(Interface):
    """
    An low level event involving the index
    """

class IPackageEvent(IIndexEvent):
    """
    An event involving a package
    """
    path = Attribute('Path to package')


class IPackageAdded(IPackageEvent):
    """
    A package is added to the repository
    """


class IPackageRemoved(IPackageEvent):
    """
    A package is removed to the repository
    """    


class IndexEvent(object):
    implements(IIndexEvent)
    def __init__(self, datafile, index):
        self.index = index
        self.datafile = datafile


class IndexUpdate(IndexEvent):
    implements(IIndexUpdate)


class PackageEvent(object):
    """
    Baseclass for pacakage events
    """
    implements(IPackageEvent)

    def __init__(self, index_manager, path=None, name=None, version=None):
        self.name = name
        self.version = version
        self.im = index_manager
        self.path = path

        if self.name is None and self.path:
            info = self.im.pkginfo_from_file(path, self.im.move_on_error)
            self.name = info.name
            self.version = info.version

##     def redispatch(self):
##         self.obj.registry.notify(self, self.obj)

##     @staticmethod
##     def channel_dispatch(event):
##         """
##         Resdispatches any object event with the original event and the
##         object contained
##         """
##         event.redispatch()


class PackageAdded(PackageEvent):
    implements(IPackageAdded)

    
class PackageRemoved(PackageEvent):
    implements(IPackageRemoved)


