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

#import 
__all__ = [ "common", "node", "file", "diff", "merge", "eolfix" ]

import common
from file import SvnDumpFile

__doc__ = """A package for processing subversion dump files."""
__version = "0.3.0"

def copy_dump_file( srcfile, dstfile ):
    """
    Copy a dumpfile.

    @type srcfile: string
    @param srcfile: Source filename.
    @type dstfile: string
    @param dstfile: Destination filename.
    """

    # SvnDumpFile classes for reading/writing dumps
    srcdmp = SvnDumpFile()
    dstdmp = SvnDumpFile()

    # open source file
    srcdmp.open( srcfile )

    hasrev = srcdmp.read_next_rev()
    if hasrev:
        if srcdmp.get_rev_nr() == 0:
            # create new dump with revision 0
            dstdmp.create_with_rev_0( dstfile, srcdmp.get_uuid(),
                        srcdmp.get_rev_date_str() )
            hasrev = srcdmp.read_next_rev()
        else:
            # create new dump starting with the same revNr as the original dump
            dstdmp.create_with_rev_n( dstfile, srcdmp.get_uuid(),
                        srcdmp.get_rev_nr() )
        # now copy all the revisions
        while hasrev:
            dstdmp.add_rev_from_dump( srcdmp )
            hasrev = srcdmp.read_next_rev()
    else:
        print "no revisions in the source dump '%s' ???" % srcfile

    # cleanup
    srcdmp.close()
    dstdmp.close()

