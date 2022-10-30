#!/usr/bin/env python3

from setuptools import setup

with open('DESCRIPTION') as fin:
    long_description = fin.read()

setup(
    name = 'pyemf3',
    version = "3.0",
    description = "Pure Python Enhanced Metafile Library",
    long_description = long_description,
    keywords = "graphics, scalable, vector, image, clipart, emf",
    license = "LGPL-2.0",
    author = "Rob McMullen and Jeremy Sanders",
    url = "https://github.com/jeremysanders/pyemf",
    platforms='any',
      
    packages=[
        "pyemf3",
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Multimedia :: Graphics',
    ]
)
