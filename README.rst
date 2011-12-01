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

The following will start the application and a static file server for
`CheesePrism` suitable for testing and development::

 $ paster serve development.ini


Prod
----

`CheesePrism` doesn't pretend to be good at serving flat files.

For a more durable and performing setup, you will want to split the
serving between a wsgi host for the management application and a
industrial strength file server (say nginx).

Configure Nginx
~~~~~~~~~~~~~~~

See `sample-nginx.conf` and replace `alias CheesePrizm/files;` and
`alias CheesePrizm/static` with your fileroot and static filepath.
 
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

The prism currently doesn't do anything with the credentials
(patches welcome).

Now your package is available for install from your prism::

  $ pip install -i http://mycheese/index/ MyAwesomePyPkg

