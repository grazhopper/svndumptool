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
__all__ = [ "common", "node", "file", "merge", "eolfix" ]

import common

#import OrderedDict
#import SvnDumpException
#import SvnDumpNode
#import SvnDumpFile
#import SvnDumpMerge
#import SvnDumpEolFix



def copyDumpFile( srcfile, dstfile ):
    "copy a dumpfile"

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

def fixEolStyleAndAddRevisionFromDump( srcdump, dstdump, textfiles ):
    """++++
        - srcdump: source dump file
        - dstdump: destination dump file"""

    # check of state is done in add_rev
    # add revision and revprops
    dstdump.add_rev( srcdump.get_rev_props() )

    #print textfiles
    # add nodes
    index = 0
    nodeCount = srcdump.get_node_count()
    while index < nodeCount:
        node = srcdump.get_node( index )
        istextfile = textfiles.has_key( node.get_path() )
        if not istextfile and node.get_properties() != None:
            if node.get_properties().has_key("svn:eol-style"):
                istextfile = True
                textfiles[ node.get_path() ] = 1
        if istextfile:
            #print "convert node %s in r%d" % ( node.get_path(), srcdump.get_rev_nr() )
            if node.convert_eol_hack( "tmpnode_%d" % index ):
                print "  converted %s" %  node.get_path()
        dstdump.add_node( node )
        index = index + 1

def fixEolStyle( srcfile, dstfile ):
    "copy a dumpfile"
    # add support for --dry-run

    # SvnDumpFile classes for reading/writing dumps
    srcdmp = SvnDumpFile()
    dstdmp = SvnDumpFile()

    # open source file
    srcdmp.open( srcfile )

    # a dict listing the textfiles
    textfiles = {}

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
            print "\n\n*** r%d ***\n" % srcdmp.get_rev_nr()
            fixEolStyleAndAddRevisionFromDump( srcdmp, dstdmp, textfiles )
            hasrev = srcdmp.read_next_rev()
    else:
        print "no revisions in the source dump '%s' ???" % srcfile

    # cleanup
    srcdmp.close()
    dstdmp.close()
    return 0



