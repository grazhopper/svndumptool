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


# OrderedDict: a class stolen from Innoconda
# http://innoconda.berlios.de/

class OrderedDict( dict ):
    """A dict which you can access in order through items() or popitem().

        Supports all normal dict operations, but keep in mind that if you
        update() it from a regular (non-ordered) dict, the new items will
        not be in any order (but will follow all the old items). Updating
        from another OrderedDict will preserve the order of both dicts."""

    def __init__( self, t=() ):
        self.order = []
        for key, value in t:
            self[key] = value

    def __setitem__( self, key, value ):
        if key in self.keys() and value == self[key]:
            return
        dict.__setitem__( self, key, value )
        if key in self.order:
            self.order.remove( key )
        self.order.append( key )

    def __delitem__( self, key ):
        dict.__delitem__( self, key )
        self.order.remove( key )

    def items( self ):
        """Return a list with the dict's items, in order."""
        return [ ( key, dict.get( self, key ) ) for key in self.order ]

    def copy( self ):
        newdict = OrderedDict()
        for key, value in self.items():
            newdict[key] = value
        return newdict

    def update( self, other_dict ):
        for key, value in other_dict.items():
            self[key] = value

    def clear( self ):
        r = dict.clear( self )
        self.order = []
        return r

    def popitem( self ):
        key, value = self.items()[0]
        del self[key]
        return key, value

    # added by mf for getting ordered keys
    def keys( self ):
        """Returns the keys in order."""
        return self.order

    # comment by MFen #python@freenode
    # def values(self): return zip(*self.items())[1]
    # func( *list )  ==  func( list[0], list[1], ..., list[len(list)] )
    # that trick is sometimes called unzip.
    # if l3=zip(l1, l2) then zip(*l3) == (l1, l2)
    # sorta.  you always end up with tuples of course

