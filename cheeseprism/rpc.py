#from time import time
import logging
import xmlrpclib


logger = logging.getLogger(__name__)


class PyPi(object):
    index = 'http://pypi.python.org/pypi'
    pkglist = None
    timeout = 5 * 60

# for autocomplete
##     @classmethod
##     def list_pkgs(cls):
##         now = time()
##         if cls.pkglist is not None:
##             expires, pkglist = cls.pkglist
##             if not expires > now:
##                 logger.debug('found cached list')
##                 return pkglist

##         logger.debug('getting list from pypi')
##         client = xmlrpclib.ServerProxy(cls.index)
##         pkglist = client.list_packages()
##         cls.pkglist = (now + cls.timeout, pkglist)
##         return pkglist

    @classmethod
    def search(cls, package_name):
        client = xmlrpclib.ServerProxy(cls.index)
        return client.package_releases(package_name)

    ### for additional information
    @classmethod
    def package_details(cls, package_name, version_number):
        client = xmlrpclib.ServerProxy(cls.index)
        return client.release_urls(package_name, version_number)
