from pyramid.config import Configurator
from cheesepyramid.resources import Root

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=Root, settings=settings)
    config.add_view('cheesepyramid.views.my_view',
                    context='cheesepyramid:resources.Root',
                    renderer='cheesepyramid:templates/mytemplate.pt')
    config.add_static_view('static', 'cheesepyramid:static', cache_max_age=3600)
    return config.make_wsgi_app()
