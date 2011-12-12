import jinja2.loaders
from path import path


def test_envfactory_makes_loaders():
    from cheeseprism import EnvFactory
    env = EnvFactory.from_config('pkg:cheeseprism pkg:cheeseprism#templates/fake file:/tmp/ %s' %path(__file__).parent)
    assert isinstance(env.loader, jinja2.loaders.ChoiceLoader)
    assert len(env.loader.loaders) == 5
    # is this backwards?
    assert env.loader.loaders[1].searchpath[0].endswith('tests')
    assert env.loader.loaders[1].searchpath == ['/tmp/']
    assert env.loader.loaders[-1].package_path == 'template/index'
    assert env.loader.loaders[-2].package_path == 'templates'
    assert env.loader.loaders[-3].package_path == 'templates/fake'
    

    
