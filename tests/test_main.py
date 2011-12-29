def test_main():
    """
    sanity check for code that creates wsgi app
    """
    from cheeseprism import main
    globconf = dict()
    app = main(globconf, **{'cheeseprism.index_templates':''})
    assert app
