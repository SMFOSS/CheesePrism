from pyramid.events import subscriber, ContextFound
from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implements


class IPackageEvent(Interface):
    """
    An event involving a package
    """

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


class PackageAdded(object):
    implements(IPackageAdded)


class PackageRemoved(object):
    implements(IPackageRemoved)
