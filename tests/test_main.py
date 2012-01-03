from path import path

here = path('.')
testdir = here / 'test-indexes/test-main'

def test_main():
    """
    sanity check for code that creates wsgi app
    """
    from cheeseprism.wsgiapp import main
    globconf = dict()
    app = main(globconf, **{'cheeseprism.index_templates':'',
                            'cheeseprism.file_root': testdir,
                            'cheeseprism.data_json': 'data.json'})
    assert app

def teardown():
    if testdir.exists():
        testdir.rmtree()
