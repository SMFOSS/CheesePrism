=============
 CheesePrism
=============

A python simple index implementation with maintained by a pyramid
webapp.


Basic Design
============

All serving of packages, metadata and index html is handled by a
separate commodity server: nginx, apache, etc.  The webapp provides
interfaces for getting new packages into the repository, rebuilding
the repository's html index, and other basic management tasks.

Index structure
===============

The repository index is a folder containing all active packages and
subfolders named for packages that contain an index.html file with
links to each package version.  This subfolder also will contain a
json file of arbitrary metadata for all versions for a package in the
repo.

Basic Metadata
--------------

 * epoch date package is created 
 * human date package is created
 * name of package
 * versions of package
  - url of version in repo
 * [ng] uploaded by

 Possible Extra
 
  * vc information (git hash for release)