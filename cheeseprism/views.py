from cheeseprism import event
from cheeseprism import pipext
from cheeseprism import resources
from cheeseprism import utils
from cheeseprism.rpc import PyPi
from path import path
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
from urllib2 import HTTPError
from urllib2 import URLError
from webob import exc
import logging
import requests
import tempfile


logger = logging.getLogger(__name__)


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
    if not (request.method == 'POST' and hasattr(request.POST['content'], 'file')):
        raise RuntimeError('No file attached') 

    fieldstorage = request.POST['content']
    dest = path(request.file_root) / utils.secure_filename(fieldstorage.filename)

    dest.write_bytes(fieldstorage.file.read())
    request.index.update_by_request(request)
    request.response.headers['X-Swalow-Status'] = 'SUCCESS'
    return request.response


@view_config(name='find-packages', renderer='find_packages.html', context=resources.App)
def find_package(context, request):
    releases = None
    search_term = None
    if request.method == "POST":
        search_term = request.POST['search_box']
        releases = PyPi.search(search_term)
    url = request.resource_url(context, request.view_name)
    return dict(releases=releases, search_term=search_term, here=url)


def package(request, fpkgs='/find-packages'):
    """
    @@ convert to use action on a post rather than on a get
    """
    name = request.matchdict['name']
    version = request.matchdict['version']
    details = PyPi.package_details(name, version)
    flash = request.session.flash 
    if not details:
        flash("%s-%s not found" %(name, version))
        return HTTPFound(fpkgs)
        
    if details[0]['md5_digest'] in request.index_data:
        logger.debug('Package %s-%s already in index' %(name, version))
        return HTTPFound('/index/%s' %name)
            
    details = details[0]
    url = details['url']
    filename = details['filename']
    newfile = None
    try:
        resp = requests.get(url)
        newfile = request.file_root / filename
        newfile.write_bytes(resp.content)
    except HTTPError, e:
        error = "HTTP Error: %d %s - %s" %(e.code, exc.status_map[e.code].title, url)
        logger.error(error)
        flash(error)
    except URLError, e:
        logger.error("URL Error: %s, %s", e.reason , url)
        flash('Url error attempting to grab %s: %s' %(url, e.reason))

    if newfile is not None:
        try:
            added_event = event.PackageAdded(request.index, path=newfile)
            request.registry.notify(added_event)            
            flash('%s-%s was installed into the index successfully.' % (name, version))
            return HTTPFound('/index/%s' %name)
        except Exception, e:
            flash('Issue with adding %s to index: See logs: %s' % (newfile.name, e))

    return HTTPFound(fpkgs)


@view_config(name='regenerate-index', renderer='regenerate.html', context=resources.App)
def regenerate_index(context, request):
    if request.method == 'POST':
        logger.debug("Regenerate index")
        homefile, leaves = request.index.regenerate_all()
        logger.debug("regeneration done:\n %s %s", homefile, leaves) #@@ time it 
        return HTTPFound('/index')
    return {}


@view_config(name='load-requirements', renderer='requirements_upload.html', context=resources.App)
def from_requirements(context, request):
    if request.method == "POST":
        req_text = request.POST['req_file'].file.read()
        index = request.index

        filename = path(tempfile.gettempdir()) / 'temp-req.txt'
        filename.write_text(req_text)
        
        names = []
        requirement_set, finder = pipext.RequirementDownloader.req_set_from_file(filename, request.file_root)
        downloader = pipext.RequirementDownloader(requirement_set, finder, seen=set(request.index_data))

        for pkginfo, outfile in downloader.download_all():
            name = pkginfo.name
            names.append(name)

        index.update_by_request(request)
        flash = request.session.flash
        if names:
            flash('The following packages were installed from the requirements file: %s' % ", ".join(names))

        if downloader.skip:
            for dl in (x.filename for x in downloader.skip):
                flash("Skipped (already in index): %s" %dl)

        if downloader.errors:
            for error in downloader.errors:
                flash('Download issue: %s' %error)
        
        return HTTPFound('/load-requirements')
    return {}

