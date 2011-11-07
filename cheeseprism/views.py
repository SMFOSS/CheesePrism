from cheeseprism import pipext
from cheeseprism import resources
from cheeseprism import utils
from path import path
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
from werkzeug import secure_filename
import tempfile

_ = TranslationStringFactory('CheesePrism')


@view_config(renderer='instructions.html', context=resources.App)
def index(context, request):
    return {}


@view_config(name='simple', renderer='index.html', context=resources.App)
def upload(context, request):
    f = request.files['content']
    f.save(path(request.file_root) / secure_filename(f.filename))
    utils.regenerate_index(request.file_root, 'index.html')
    response = request.get_response()
    response.headers['X-Swalow-Status'] = 'SUCCESS'
    return response


#@app.route('/search', methods=['GET','POST'])
@view_config(name='search', renderer='find_packages.html', context=resources.App)
def find_packages(context, request):
    #search pypi on post
    releases = None
    search_term = None
    if request.method == "POST":
        search_term = request.form['search_box']
        releases = utils.search_pypi(search_term)
    return dict(releases=releases, search_term=search_term)


## #@app.route('/package/<name>/<version>')
## def package(name, version):
##     details = package_details(name, version)
##     if details:
##         details = details[0]
##         url = details['url']
##         filename = details['filename']
##         try:
##             req = Request(url)
##             f = urlopen(req)
##             print "downloading " + url

##         	# Open our local file for writing
##             local_file = open(os.path.join(app.config['FILE_ROOT'],filename), "w")
##             #Write to our local file
##             local_file.write(f.read())
##             local_file.close()
##             print 'finished downloading'
##         #handle errors
##         except HTTPError, e:
##             print "HTTP Error:", e.code , url
##         except URLError, e:
##             print "URL Error:", e.reason , url
##         regenerate_index(app.config['FILE_ROOT'],'index.html')
##         flash('%s-%s was installed into the index successfully.' % (name, version))
##     return redirect('/')


#@app.route('/regenerate-index', methods=['POST', 'GET'])
@view_config(name='regenerate-index', renderer='regenerate.html', context=resources.App)
def regenerate(context, request):
    if request.method == 'POST':
        utils.regenerate_index(request.file_root, 'index.html')
        return HTTPFound('/index')
    return {}


def flash(msg):
    raise NotImplementedError

#@app.route('/requirements', methods=['POST','GET'])
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
            utils.regenerate_index(request.file_root,'index.html')
        
        return HTTPFound('/requirements')
    return {}
