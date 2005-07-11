#!/usr/bin/env python

import sys
 
from distutils.core import setup
 
setup(
    name='svndumptool',
    version = '0.3.0',
    description='Package and cmdline tool for processing Subversion dump files.',
    license='GNU General Public License (GPL)',
    url='http://queen.borg.ch/subversion/svndumptool/',
    download_url='http://queen.borg.ch/subversion/svndumptool/0.3.0/svndumptool-0.3.0.tar.gz',
    author='Martin Furter',
    author_email = 'mf@rola.ch',
    packages = [ 'svndump' ],
    scripts = [ 'svndumptool.py' ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Topic :: Software Development :: Version Control :: SVN',
    ]
)

