from pyramid.config import Configurator
from cheeseprism.resources import Root

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=Root, settings=settings)
    config.add_view('cheeseprism.views.my_view',
                    context='cheeseprism:resources.Root',
                    renderer='cheeseprism:templates/mytemplate.pt')
    config.add_static_view('static', 'cheeseprism:static', cache_max_age=3600)
    return config.make_wsgi_app()
