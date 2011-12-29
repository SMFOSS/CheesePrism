#from pyramid.url import resource_url

class BaseResource(dict):
    """
    Base class for resources
    """

##     @property
##     def approot(self):
##         return self.recurse_parent(App)
            
##     def recurse_parents(self, klass, parent=None):
##         if parent is None:
##             parent = self.__parent__
##         else:
##             parent = parent.__parent__
##         if parent is None:
##             # we've rooted out
##             return None
##         if isinstance(parent, klass):
##             return parent
##         return self.recurse_parent(klass, parent)
    
##     def suburls(self, request):
##         for name in sorted(self):
##             obj = self[name]
##             url = resource_url(self, request, name)
##             yield obj, url


class App(BaseResource):
    __name__ = ''
    __parent__ = None
    
    def __init__(self, request):
        self.request = request
