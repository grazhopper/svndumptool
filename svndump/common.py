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

import time

__doc__ = """Common functions and classes."""

# perhaps some of these date functions can be replaced by
# functions provided by the svn python bindings +++++
# <sussman> it's our own string format, in libsvn_subr/time.c
# <sussman> svn_time_[to|from]_cstring()
def parse_svn_date_str( dateStr ):
    "Parse a svn date string and return a list containing time_t and micros."
    if len(dateStr) != 27:
        return [0,0]
    if dateStr[19] != "." or dateStr[26] != "Z":
        return [0,0]
    dat = time.strptime( dateStr[:19], "%Y-%m-%dT%H:%M:%S" )
    return [ int(time.mktime(dat)), int( dateStr[20:26] ) ]

def is_valid_md5_string( md5 ):
    "checks a md5 string"

    if len( md5 ) != 32:
        return 0
    return 1

class SvnDumpException( Exception ):
    """A simple exception class."""
    
    def __init__( self, text ):
        self.text = text

    def __str__( self ):
        return self.text

