import logging
import os
import pkg_resources
import re

logger = logging.getLogger(__name__)


def resource_spec(spec):
    """
    Loads resource from a string specifier. 
    >>> from doula.utils import resource_spec
    >>> resource_spec('egg:ReleaseDoula#doula/roles.yml')
    '.../doula/roles.yml'

    >>> resource_spec('file:data/languages.ini')
    'data/languages.ini'

    >>> resource_spec('data/languages.ini')
    'data/languages.ini'
    """
    filepath = spec
    if spec.startswith('egg:'):
        req, subpath = spec.split('egg:')[1].split('#')
        req = pkg_resources.get_distribution(req).as_requirement()
        filepath = pkg_resources.resource_filename(req, subpath)
    elif spec.startswith('file:'):
        filepath = spec.split('file:')[1]
    # Other specs could be added, but egg and file should be fine for
    # now
    return filepath


_windows_device_files = ('CON', 'AUX', 'COM1', 'COM2', 'COM3', 'COM4', 'LPT1',
                         'LPT2', 'LPT3', 'PRN', 'NUL')
_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')


def secure_filename(filename):
    r"""Pass it a filename and it will return a secure version of it.  This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`.  The filename returned is an ASCII only string
    for maximum portability.

    On windows system the function also makes sure that the file is not
    named after one of the special device files.

    >>> secure_filename("My cool movie.mov")
    'My_cool_movie.mov'
    >>> secure_filename("../../../etc/passwd")
    'etc_passwd'
    >>> secure_filename(u'i contain cool \xfcml\xe4uts.txt')
    'i_contain_cool_umlauts.txt'

    The function might return an empty filename.  It's your responsibility
    to ensure that the filename is unique and that you generate random
    filename if the function returned an empty one.

    .. versionadded:: 0.5

    :param filename: the filename to secure

    Credit: from Armin Ronacher's Werkzeug, BSD
    """
    if isinstance(filename, unicode):
        from unicodedata import normalize
        filename = normalize('NFKD', filename).encode('ascii', 'ignore')
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
                   filename.split()))).strip('._')

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if os.name == 'nt' and filename and \
       filename.split('.')[0].upper() in _windows_device_files:
        filename = '_' + filename

    return filename
