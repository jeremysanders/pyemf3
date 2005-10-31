#!/usr/bin/env python

import sys,distutils
from distutils.core import setup

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
if sys.version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

# python looks in current directory first, so we'll be sure to get our
# freshly unpacked version here.
import pyemf

pyemf_version=str(pyemf.__version__)
pyemf_author=pyemf.__author__
pyemf_email=pyemf.__author_email__
pyemf_url=pyemf.__url__

print "Version = %s" % pyemf_version

setup(name = "pyemf",
      version = pyemf_version,
      description = "Python library for EMF vector graphics",
      author = pyemf_author,
      author_email = pyemf_email,
      url = pyemf_url,
      platforms='any',
      py_modules = ['pyemf'],
      
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: by End-User Class :: Developers',
                   'License :: OSI-Approved Open Source :: GNU Library or Lesser General Public License (LGPL)',
                   'Operating System :: Grouping and Descriptive Categories :: OS Independent (Written in an interpreted language)',
                   'Programming Language :: Python',
                   'Topic :: Multimedia :: Graphics',
                   ]
      )

