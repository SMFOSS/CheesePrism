from cheeseprism.resources import App
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.request import Request
from pyramid_jinja2 import renderer_factory
from pyramid.session import UnencryptedCookieSessionFactoryConfig

def get_app(settings):
    settings.setdefault('jinja2.i18n.domain', 'CheesePrism')
    session_factory = UnencryptedCookieSessionFactoryConfig('cheeseprism')

    config = Configurator(root_factory=App, settings=settings, session_factory = session_factory)
    
    config.add_translation_dirs('locale/')
    config.include('pyramid_jinja2')
    config.add_renderer('.html', renderer_factory)

    config.add_static_view('static', 'static')
    config.scan('cheeseprism.views')
    config.set_request_factory(CPRequest)
    return config.make_wsgi_app()


def main(global_config, **settings):
    """ This function returns a WSGI application.
    
    It is usually called by the PasteDeploy framework during 
    ``paster serve``.
    """
    settings = dict(settings)
    return get_app(settings)

class CPRequest(Request):
    """
    Custom CheesePrism request object
    """

    @reify
    def settings(self):
        return self.registry.settings

    @reify
    def file_root(self):
        return self.registry.settings['file_root']    


