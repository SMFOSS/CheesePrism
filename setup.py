from setuptools import find_packages
from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = ['Jinja2',
            'path.py',
            'pkginfo',
            'pyramid',
            'pyramid_debugtoolbar',
            'pyramid_jinja2',
            'requests',
            'pip']

setup(name='CheesePrism',
      version='0.1a1',
      description='CheesePrism',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Whit Morriss (et al.)',
      author_email='whit-at-surveymonkey-dot-com',
      url='https://github.com/SurveyMonkey/CheesePrism',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="cheeseprism",
      entry_points = """\
      [paste.app_factory]
      main = cheeseprism.wsgiapp:main
      """,
      paster_plugins=['pyramid'],
      )
