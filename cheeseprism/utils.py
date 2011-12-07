from werkzeug.contrib.cache import SimpleCache
import logging
import pkg_resources
import xmlrpclib


logger = logging.getLogger(__name__)

#@@ refactor into class
cache = SimpleCache()

def list_pypi():
    rs = cache.get('package-list')
    if rs:
        print 'found cached list'
        return rs
    else:
        print 'getting list from pypi'
        client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
        rs = client.list_packages()
        cache.set('package-list',rs,timeout=5 * 60)
        return rs


def search_pypi(package_name):
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    return client.package_releases(package_name)


def package_details(package_name, version_number):
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    return client.release_urls(package_name,version_number)


def resource_spec(spec):
    """
    Loads resource from a string specifier. 
    >>> from doula.utils import resource_spec
    >>> resource_spec('egg:ReleaseDoula#doula/roles.yml')
    '.../doula/roles.yml'

    >>> resource_spec('file:data/languages.ini')
    'data/languages.ini'

    >>> resource_spec('data/languages.ini')
    'data/languages.ini'
    """
    filepath = spec
    if spec.startswith('egg:'):
        req, subpath = spec.split('egg:')[1].split('#')
        req = pkg_resources.get_distribution(req).as_requirement()
        filepath = pkg_resources.resource_filename(req, subpath)
    elif spec.startswith('file:'):
        filepath = spec.split('file:')[1]
    # Other specs could be added, but egg and file should be fine for
    # now
    return filepath
