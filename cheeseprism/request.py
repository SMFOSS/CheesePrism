from cheeseprism.index import IndexManager
from path import path
from pyramid.decorator import reify
from pyramid.request import Request
from pyramid.security import unauthenticated_userid
import json


class CPRequest(Request):
    """
    Custom CheesePrism request object
    """

    imclass = IndexManager

    @reify
    def userid(self):
        return unauthenticated_userid(self)

    @reify
    def settings(self):
        return self.registry.settings

    @reify
    def index_templates(self):
        return self.registry.settings['cheeseprism.index_templates']
    

    @reify
    def file_root(self):
        return path(self.registry.settings['cheeseprism.file_root'])

    @reify
    def index(self):
        return self.imclass(self.file_root, template_env=self.index_templates)

    @reify
    def index_data_path(self):
        return self.registry.settings['cheeseprism.data_json']

    @reify
    def index_data(self):
        return self.index.data_from_path(self.file_root / self.registry.settings['cheeseprism.data_json'])
    
