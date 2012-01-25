from cheeseprism.auth import BasicAuthenticationPolicy
from cheeseprism.index import EnvFactory
from cheeseprism.request import CPRequest as Request
from cheeseprism.resources import App
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_jinja2 import renderer_factory


def main(global_config, **settings):
    settings.setdefault('jinja2.i18n.domain', 'CheesePrism')
    session_factory = UnencryptedCookieSessionFactoryConfig('cheeseprism')

    config = Configurator(root_factory=App, settings=settings,
                          session_factory=session_factory,
                          authentication_policy=\
                          BasicAuthenticationPolicy(BasicAuthenticationPolicy.noop_check))
    
    config.add_translation_dirs('locale/')
    config.include('pyramid_jinja2')
    config.add_renderer('.html', renderer_factory)

    config.add_static_view('static', 'static')
    config.scan('cheeseprism.views')
    config.scan('cheeseprism.index')
    config.set_request_factory(Request)
    config.add_route('package', 'package/{name}/{version}', view='cheeseprism.views.package')
    settings['index_templates'] = EnvFactory.from_str(settings['cheeseprism.index_templates'])

    return config.make_wsgi_app()

