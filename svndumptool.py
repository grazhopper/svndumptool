#!/usr/bin/env python
#===============================================================================
#
# Copyright (C) 2003 Martin Furter <mf@rola.ch>
#
# This file is part of SvnDumpTool
#
# SvnDumpTool is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# SvnDumpTool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SvnDumpTool; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#
#===============================================================================

import sys

from svndump import __version
from svndump.diff import svndump_diff_cmdline
from svndump.merge import svndump_merge_cmdline
from svndump.eolfix import svndump_eol_fix_cmdline

def help( x ):
    print ""
    print "svndumptool.py command [options]"
    print ""
    print "  commands:"
    print "    diff         show differences between two dump files"
    print "    eolfix       fix EOL of text files in a dump"
    print "    merge        merge dump files"
    print "    --version    print the version"
    print ""
    print "  use 'svndumptool.py command -h' for help about the commands."
    print ""
    sys.exit( 0 )

if __name__ == '__main__':
    appname = sys.argv[0].replace( "\\", "/" )
    args = sys.argv[1:]
    n = appname.rfind( "/" )
    if n >= 0:
        appname = appname[n+1:]
    if appname == "svndumpmerge.py":
        func = svndump_merge_cmdline
    elif appname == "svndumpeolfix.py":
        func = svndump_eol_fix_cmdline
    elif appname == "svndumpdiff.py":
        func = svndump_diff_cmdline
    elif len( args ) > 0:
        if args[0] == "merge":
            func = svndump_merge_cmdline
        elif args[0] == "eolfix":
            func = svndump_eol_fix_cmdline
        elif args[0] == "diff":
            func = svndump_diff_cmdline
        elif args[0] == "--version":
            print appname + " " + __version
            sys.exit( 0 )
        else:
            help( args[0] )
        appname = appname + " " + args[0]
        args = args[1:]
    else:
        help( "" )

    sys.exit( func( appname, args ) )

