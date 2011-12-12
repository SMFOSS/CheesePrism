from cheeseprism.resources import App
from path import path
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.request import Request
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_jinja2 import renderer_factory
import jinja2


def main(global_config, **settings):
    """ This function returns a WSGI application.
    
    It is usually called by the PasteDeploy framework during 
    ``paster serve``.
    """
    settings.setdefault('jinja2.i18n.domain', 'CheesePrism')
    session_factory = UnencryptedCookieSessionFactoryConfig('cheeseprism')

    config = Configurator(root_factory=App, settings=settings, session_factory = session_factory)
    
    config.add_translation_dirs('locale/')
    config.include('pyramid_jinja2')
    config.add_renderer('.html', renderer_factory)

    config.add_static_view('static', 'static')
    config.scan('cheeseprism.views')
    config.set_request_factory(CPRequest)
    config.add_route('package', 'package/{name}/{version}', view='cheeseprism.views.package')
    config.index_templates = EnvFactory.from_config(settings['cheeseprism.index_templates'])

    return config.make_wsgi_app()    


class EnvFactory(object):
    env_class = jinja2.Environment
    def __init__(self, config):
        self.config = config

    @property
    def loaders(self):
        if self.config:
            loaders = self.config.split(' ')
            for loader in loaders:
                spec = loader.split(':')
                if len(spec) == 1:
                    yield jinja2.FileSystemLoader(spec); continue

                type_, spec = spec
                if type_ == "file":
                    yield jinja2.FileSystemLoader(spec); continue

                if type_ == 'pkg':
                    spec = spec.split('#')
                    if len(spec) == 1: yield jinja2.PackageLoader(spec[0])
                    else: yield jinja2.PackageLoader(*spec)
                    continue
                raise RuntimeError('Loader type not found: %s %s' %(type_, spec))

    @classmethod
    def from_config(cls, config=None):
        factory = cls(config)
        choices = [jinja2.PackageLoader('cheeseprism', 'templates/index')]
        if config: [choices.insert(0, loader) for loader in factory.loaders]
        return factory.env_class(loader=jinja2.ChoiceLoader(choices))


class CPRequest(Request):
    """
    Custom CheesePrism request object
    """

    @reify
    def settings(self):
        return self.registry.settings

    @reify
    def index_templates(self):
        return self.registry.index_templates
    

    @reify
    def file_root(self):
        return path(self.registry.settings['cheeseprism.file_root'])


