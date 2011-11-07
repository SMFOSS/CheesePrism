from pip.index import PackageFinder
from pip.locations import build_prefix, src_prefix
from pip.log import logger
from pip.req import RequirementSet, parse_requirements
from pip.util import display_path
import os
import shutil

def parse_reqs(filename, download_dir):
    build_dir = os.path.abspath(build_prefix)
    src_dir = os.path.abspath(src_prefix)
    finder = PackageFinder(
        find_links=[],
        index_urls=['http://pypi.python.org/simple'])
    requirement_set = CheeseRequirementSet(
        build_dir=build_dir,
        src_dir=src_dir,
        download_dir=download_dir,
        download_cache=None,
        upgrade=False,
        ignore_installed=True,
        ignore_dependencies=False)
    Options = type('Options', (),{})
    Options.skip_requirements_regex = ''
    Options.default_vcs = ''
    options = Options()
    names = []
    for req in parse_requirements(filename, finder=finder, options=options):
        requirement_set.add_requirement(req)
        names.append(req.req)
    requirement_set.prepare_files(finder, force_root_egg_info=False, bundle=False)
    return names

class CheeseRequirementSet(RequirementSet):
    def copy_file(self, filename, location, content_type, link):
        copy = True
        download_location = os.path.join(location, link.filename)
        if os.path.exists(download_location):
            copy = False
            logger.notify('Ignoring already existing file.')
        if copy:
            shutil.copy(filename, download_location)
            logger.indent -= 2
            logger.notify('Saved %s' % display_path(download_location))
    
