from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implements


class IPackageEvent(Interface):
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


class PackageEvent(object):
    """
    Baseclass for pacakage events
    """
    implements(IPackageEvent)

    def __init__(self, index_manager, path):
        self.im = index_manager
        self.path = path

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
