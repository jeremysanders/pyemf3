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

module_version=str(pyemf.__version__)
module_author=pyemf.__author__
module_email=pyemf.__author_email__
module_url=pyemf.__url__
module_description=pyemf.__description__
module_list=['pyemf']

#print "Version = %s" % module_version

setup(name = "pyemf",
      version = module_version,
      description = module_description,
      author = module_author,
      author_email = module_email,
      url = module_url,
      platforms='any',
      py_modules = module_list,
      
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: by End-User Class :: Developers',
                   'License :: OSI-Approved Open Source :: GNU Library or Lesser General Public License (LGPL)',
                   'Operating System :: Grouping and Descriptive Categories :: OS Independent (Written in an interpreted language)',
                   'Programming Language :: Python',
                   'Topic :: Multimedia :: Graphics',
                   ]
      )

