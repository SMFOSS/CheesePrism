from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('CheesePrism')

def my_view(request):
    return {'project':'CheesePrism'}
