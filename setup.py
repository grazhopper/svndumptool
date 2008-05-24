#!/usr/bin/env python
#
# Installing:
#   ./setup.py install
#
# See also README.txt under 'Packaging'
#

from distutils.core import setup
import svndump

args = {
    "name": 'svndumptool',
    "version": svndump.__version,
    "description": 'Package and cmdline tool for processing Subversion dump files.',
    "license": 'GNU General Public License (GPL)',
    "url": 'http://svn.borg.ch/svndumptool/',
    "download_url": 'http://svn.borg.ch/svndumptool/0.5.0/svndumptool-0.5.0.tar.gz',
    "author": 'Martin Furter',
    "author_email": 'mf@rola.ch',
    "packages": [ 'svndump' ],
    "scripts": [ 'svndumptool.py' ],
    "classifiers": [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Topic :: Software Development :: Version Control :: SVN',
    ],
}

try:
    import py2exe
    args["console"] = [ 'svndumptool.py' ]
except:
    pass
 
setup( **args )

