from setuptools import find_packages
from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires=['pyramid', 'pyyaml', 'Jinja2', 'pyramid_jinja2', 'path.py', 'werkzeug', 'pyramid_debugtoolbar']

setup(name='CheesePrism',
      version='0.0',
      description='CheesePrism',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="cheeseprism",
      entry_points = """\
      [paste.app_factory]
      main = cheeseprism:main
      """,
      paster_plugins=['pyramid'],
      )
