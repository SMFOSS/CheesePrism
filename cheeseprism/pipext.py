from pip.index import PackageFinder
from pip.locations import build_prefix, src_prefix
from pip.log import logger
from pip.req import RequirementSet, parse_requirements
from pip.util import display_path
from path import path


def parse_reqs(filename, download_dir):
    build_dir = path(build_prefix).abspath()
    src_dir = path(src_prefix).abspath()

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
        download_location = path(location) / link.filename
        if download_location.exists():
            copy = False
            logger.notify('Ignoring already existing file.')
        if copy:
            download_location.copy(filename)
            logger.indent -= 2
            logger.notify('Saved %s' % display_path(download_location))
    
