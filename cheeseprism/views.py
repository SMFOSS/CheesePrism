from cheeseprism import pipext
from cheeseprism import index
from cheeseprism import resources
from cheeseprism import utils
from path import path
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
from werkzeug import secure_filename
import tempfile

_ = TranslationStringFactory('CheesePrism')


@view_config(renderer='index.html', context=resources.App)
def homepage(context, request):
    return {}


@view_config(name='instructions', renderer='instructions.html', context=resources.App)
def instructions(context, request):
    return {'page': 'instructions'}


@view_config(name='simple', context=resources.App)
def upload(context, request):
    """
    The interface for disutils upload
    """
    if not (hasattr(request.POST['content'], 'file')):
        raise RuntimeError('No file attached') 

    fieldstorage = request.POST['content']
    dest = path(request.file_root) / secure_filename(fieldstorage.filename)

    dest.write_bytes(fieldstorage.file.read())

    index.regenerate(request.file_root)
    request.response.headers['X-Swalow-Status'] = 'SUCCESS'
    return request.response


@view_config(name='find-packages', renderer='find_packages.html', context=resources.App)
def find_packages(context, request):
    #search pypi on post
    releases = None
    search_term = None
    if request.method == "POST":
        search_term = request.form['search_box']
        releases = utils.search_pypi(search_term)
    return dict(releases=releases, search_term=search_term)


def package(request):
    """
    refactor to use http://docs.python-requests.org/en/latest/index.html
    """
    name = request.matchdict['name']
    version = request.matchdict['version']
    details = utils.package_details(name, version)
    if details:
        details = details[0]
        url = details['url']
        filename = details['filename']
        try:
            req = Request(url)
            f = urlopen(req)
            print "downloading " + url

        	# Open our local file for writing
            local_file = open(os.path.join(app.config['FILE_ROOT'],filename), "w")
            #Write to our local file
            local_file.write(f.read())
            local_file.close()
            print 'finished downloading'
        #handle errors
        except HTTPError, e:
            print "HTTP Error:", e.code , url
        except URLError, e:
            print "URL Error:", e.reason , url
        index.regenerate(app.config['FILE_ROOT'])
        flash('%s-%s was installed into the index successfully.' % (name, version))
    #@@ would be cool to return to the package in the index
    return HTTPFound('/index')


@view_config(name='regenerate-index', renderer='regenerate.html', context=resources.App)
def regenerate_index(context, request):
    if request.method == 'POST':
        index.regenerate(request.file_root)
        return HTTPFound('/index')
    return {}

#tag_build = dev
#tag_svn_revision = true


## def flash(msg):
##     session.flash(msg)


@view_config(name='requirements', renderer='requirements_upload.html', context=resources.App)
def from_requirements(context, request):
    if request.method == "POST":
        f = request.files['req_file']
        
        filename = path(tempfile.gettempdir()) / 'temp-req.txt'
        f.save(filename)
        try:
            names = pipext.parse_reqs(filename, request.file_root)
        except:
            flash('There were some errors getting files from the uploaded requirements')
        else:
            flash('packages were installed from the requirements file. %s' % names)
        finally:
            index.regenerate(request.file_root)
        
        return HTTPFound('/requirements')
    return {}
