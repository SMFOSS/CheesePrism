================
 Cheese Pyramid
================

A simple application for managing a static python package index.  It
borrows heavily from `BasketWeaver` and `cheese_emporium`.  It
leverages `pip` and `setuptools/distribute` for various package
management tasks.


Running
=======

Dev
---

Install
~~~~~~~

Activate a virtual env. Then either check out the code to your chosen location::

 $ git clone git://github.com/SurveyMonkey/CheesePrism.git

and install::

 $ cd CheesePrism; pip install -e ./

or use pip to clone and install directly to $VIRTUAL_ENV/src::

 $ pip install git+git://github.com/SurveyMonkey/CheesePrism.git#egg=CheesePrism
 $ cd $VIRTUAL_ENV/src/cheeseprism

Test
~~~~

To run the tests, first install the test requirements

:: 
 
 $ cd CheesePrism
 $ pip install -r tests-require.txt
 
Then::

 $ nosetests -vv

This will run tests and spit out coverage.


Run
~~~

The following will start the application and a static file server for
`CheesePrism` suitable for testing and development::

 $ paster serve development.ini

To run the tests::

 $ pip install


Prod
----

`CheesePrism` doesn't pretend that it or python servers excell at
serving flat files.

For a more durable and performing setup, you will want to split the
serving between a wsgi host for the management application and a
industrial strength file server (say nginx).


Configure Nginx
~~~~~~~~~~~~~~~

See `sample-nginx.conf` and replace `alias CheesePrism/files;` and
`alias CheesePrism/static` with your fileroot and static filepath.
 
:todo:
  have start up announce static and file_root (and document)


Serve management app
~~~~~~~~~~~~~~~~~~~~

Use the prod.ini (edited for your setup) for simplest serving::

 $ paster serve prod.ini

:todo:
  ini config generation script
                                   

How to use
==========

CheesePrism understand the upload interface of pypi. This means for
python2.6 and better you can setup your ~/.pypirc and then upload to
your prism as you would pypi::

 [distutils]
    index-servers =
        pypi
        local


 [pypi]
    username:user
    password:secret

 [local]
    # your prism of fromage
    username:user
    password:secret
    repository:http://mycheese


The you can upload a source ala::

  $  cd /src/MyAwesomePyPkg
  $  python setup.py sdist upload -r local

The prism currently has the most basic support for pypi's basic auth
scheme.  This mainly exists for the purpose of grabbing the identity
of who pupports to be uploading a package, rather than any actual
security.  If you need more, it should provide a starting point for
extension.

Now your package is available for install from your prism::

  $ pip install -i http://mycheese/index/ MyAwesomePyPkg

