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
from optparse import OptionParser

from file import SvnDumpFile

class SvnDumpMerge:
    "a class for merging svn dump files"

    # handle copyfrom-rev !!!

    def __init__( self ):

        # output file name
        self.__out_file = ""
        # list additional directories
        self.__out_dirs = []
        # log message for directory creating revision
        self.__out_message = ""
        # author for the additional revision
        self.__out_author = "svndumpmerge"

        # variables used for input dump files
        # file names
        self.__in_files = []
        # path renames [ [ ( from, to ), ... ], ... ]
        self.__in_renames = []
        # mkdir excludes [ {}, ... ]
        self.__in_excludes = []
        # revision number mappings [ {}, ... ]
        self.__in_rev_nr_maps = []
        # dump files (class SvnDumpFile)
        self.__in_dumps = []
        # revision dates of the dumps
        self.__in_rev_dates = []


    def set_output_file( self, filename, startRev=0 ):
        """Sets the output file name and optional start revision
             - filename (string): name of the output dump file
             - startRev (int, optional): start revision number, default is 0"""

        self.__out_file = filename
        self.outStartRev = startRev

    def add_input_file( self, filename ):
        """Adds an input file and returns it's index
            - filename (string): name of a input dump file
            - return (int): index of the input file"""

        index = len( self.__in_files )
        self.__in_files = self.__in_files + [ filename ]
        self.__in_renames = self.__in_renames + [ [] ]
        self.__in_excludes = self.__in_excludes + [ {} ]
        self.__in_rev_nr_maps = self.__in_rev_nr_maps + [ {} ]
        return index

    def add_rename( self, index, prefixFrom, prefixTo ):
        """Adds a path prefix reanme.
             - index (int): index of the dump file
             - prefixFrom (string): from path prefix (directory)
             - prefixTo (string): to path prefix (directory)"""

        # make sure that prefixFrom starts and ends with a /
        if prefixFrom[0:1] == "/":
            prefixFrom = prefixFrom[1:]
        if prefixFrom[len(prefixFrom)-1:] != "/":
            prefixFrom = prefixFrom + "/"
        # make sure that prefixTo starts and ends with a /
        if prefixTo[0:1] == "/":
            prefixTo = prefixTo[1:]
        if prefixTo[len(prefixTo)-1:] != "/":
            prefixTo = prefixTo + "/"
        # add the rename
        self.__in_renames[index] = self.__in_renames[index] + \
                                [ (prefixFrom, prefixTo ) ]

    def add_mkdir_exclude( self, index, dirName ):
        """Adds a mkdir exclude.
             - index (int): index of the dump file
             - dirName (string): name of the directory"""

        # add the mkdir exclude
        self.__in_excludes[index][dirName] = None

    def add_directory( self, dirName ):
        """adds an additional directory"""
        if dirName[0:1] == "/":
            dirName = dirName[1:]
        if dirName[-1:] == "/":
            dirName = dirName[:-1]
        self.__out_dirs = self.__out_dirs + [ dirName ]

    def set_log_message( self, msg ):
        """set log message for additional dirs revision"""
        self.__out_message = msg

    def merge( self ):
        """Executes the merge."""

        # open input dump files
        for inFile in self.__in_files:
            inDump = SvnDumpFile()
            inDump.open( inFile )
            inDump.read_next_rev();
            self.__in_dumps = self.__in_dumps + [ inDump ]

        # remove empty dumps
        dumpCount = self.__remove_empty_dumps()
        if dumpCount == 0:
            return

        # open output file
        self.outDump = SvnDumpFile()
        if self.outStartRev == 0:
            self.outDump.create_with_rev_0( self.__out_file,
                self.__in_dumps[0].get_uuid(), self.__in_dumps[0].get_rev_date_str() )
        else:
            self.outDump.create_with_rev_n( self.__out_file,
                self.__in_dumps[0].get_uuid(), self.outStartRev )

        # skip revision 0 of all dumps
        for inDump in self.__in_dumps:
            if inDump.get_rev_nr() == 0:
                inDump.read_next_rev()

        # remove empty dumps
        dumpCount = self.__remove_empty_dumps()
        if dumpCount == 0:
            self.outDump.close()
            return

        # get revision dates
        oldest = None
        oldestStr = ""
        for index in range(len(self.__in_dumps)):
            revDat = self.__in_rev_dates + [ self.__in_dumps[index].get_rev_date() ]
            self.__in_rev_dates = revDat
            if oldest == None or revDat < oldest:
                oldest = revDat
                oldestStr = self.__in_dumps[index].get_rev_date_str()

        # add additional directories
        if len(self.__out_dirs) > 0:
            self.outDump.add_rev( { "svn:log" : self.__out_message,
                                        "svn:author" : self.__out_author,
                                        "svn:date" : oldestStr } )
            for dirName in self.__out_dirs:
                node = SvnDumpNode( "dir", dirName )
                node.set_action( "add" )
                self.outDump.add_node( node )

        # loop over all revisions
        while dumpCount > 0:
            # find index of the oldest revision
            oldestIndex = 0
            for index in range( 1, dumpCount ):
                if self.__in_rev_dates[index] < self.__in_rev_dates[oldestIndex]:
                    oldestIndex = index
            # copy revision
            self.__copy_revision( oldestIndex )
            print "Revision: %d" % self.outDump.get_rev_nr()
            # read next revision
            srcDump = self.__in_dumps[oldestIndex]
            if srcDump.read_next_rev():
                self.__in_rev_dates[oldestIndex] = srcDump.get_rev_date()
            else:
                dumpCount = self.__remove_empty_dumps()

        # close output
        print "created %d revisions" % self.outDump.get_rev_nr()
        self.outDump.close()
            

    def __copy_revision( self, dumpIndex ):
        """INTERNAL: don't use !!!
             copies a revision from inDump[dumpIndex] to outDump"""

        srcDump = self.__in_dumps[dumpIndex]

        # add revision and revprops
        self.outDump.add_rev( srcDump.get_rev_props() )

        # add nodes
        index = 0
        nodeCount = srcDump.get_node_count()
        while index < nodeCount:
            node = srcDump.get_node( index )
            newNode = self.__change_node( dumpIndex, node )
            if newNode != None:
                self.outDump.add_node( newNode )
            index = index + 1

        # add revision info
        self.__in_rev_nr_maps[dumpIndex][srcDump.get_rev_nr()] = \
                    self.outDump.get_rev_nr()

    def __change_node( self, dumpIndex, node ):
        """INTERNAL: don't use !!!
             creates a new node if the path changed, else returns the old node"""

        path = node.get_path()
        # mkdir exclude check
        if node.get_kind() == "dir" and node.get_action() == "add":
            if path in self.__in_excludes[dumpIndex]:
                return None
        fromPath = node.get_copy_from_path()
        fromRev = node.get_copy_from_rev()
        change = 0
        newPath = self.__rename_path( path, self.__in_renames[dumpIndex] )
        newFromPath = fromPath
        newFromRev = fromRev
        if path != newPath:
            change = 1
        if fromRev > 0:
            newFromPath = self.__rename_path( fromPath, self.__in_renames[dumpIndex] )
            if fromPath != newFromPath:
                change = 1
            newFromRev = self.__in_rev_nr_maps[dumpIndex][fromRev]
            if fromRev != newFromRev:
                change = 1

        if not change:
            # no change needed
            return node

        # do the rename
        newNode = SvnDumpNode( newPath, node.get_kind() )
        newNode.set_action( node.get_action() )
        if node.has_copy_from():
            newNode.set_copy_from( node.get_copy_from_path(),
                                   node.get_copy_from_rev() )
        if node.has_properties():
            newNode.set_properties( node.get_properties() )
        if node.has_text():
            newNode.set_text_node( node )
        return newNode

    def __rename_path( self, path, renames ):
        """INTERNAL: don't use !!!
             Applies the renames to the path and returns the new path
             - path (string): a path
             - renames: list of rename tuples"""

        # ensure that path does not a leading slash
        if len(path) > 1 and path[0:1] == "/":
            path = path[1:]
        sPath = path + "/"
        for sPfx, dPfx in renames:
            sLen = len( sPfx )
            if sPath[:sLen] == sPfx:
                if len(path) <= len(sPfx):
                    # it's the full path
                    return dPfx[0:len(dPfx)-1]
                else:
                    # there's a suffix
                    return dPfx + path[sLen:]
        return path

    def __remove_empty_dumps( self ):
        """INTERNAL: don't use !!!
        +++++++++ not used ??? (*&#^(*&@#^%($#!!!
             removes dump files which reached EOF and returns the count of dumps"""

        index = 0
        while index < len( self.__in_dumps ):
            inDump = self.__in_dumps[index]
            if inDump.has_revision():
                index = index + 1
            else:
                inDump.close()
                eidx = index + 1
                self.__in_files[index:eidx] = []
                self.__in_renames[index:eidx] = []
                self.__in_rev_nr_maps[index:eidx] = []
                self.__in_dumps[index:eidx] = []
                self.__in_rev_dates[index:eidx] = []
        return index


def __svndump_merge_opt_i( option, opt, value, parser, *args ):
    # option parser callback for input file '-i <filename>'
    merge = args[0]
    vars = args[1]
    vars["fileindex"] = merge.add_input_file( value )

def __svndump_merge_opt_r( option, opt, value, parser, *args ):
    # option parser callback for rename '-r from to'
    merge = args[0]
    vars = args[1]
    merge.add_rename( vars["fileIndex"], value[0], value[1] )

def __svndump_merge_opt_x( option, opt, value, parser, *args ):
    # option parser callback for mkdir exclude '-x dir'
    merge = args[0]
    vars = args[1]
    merge.add_mkdir_exclude( vars["fileIndex"], value )

def __svndump_merge_opt_o( option, opt, value, parser, *args ):
    # option parser callback for output file '-o filename'
    merge = args[0]
    vars = args[1]
    merge.set_output_file( value )
    vars["outFileSet"] = 1

def __svndump_merge_opt_d( option, opt, value, parser, *args ):
    # option parser callback for mkdir '-d dirname'
    merge = args[0]
    vars = args[1]
    merge.add_directory( value )

def __svndump_merge_opt_m( option, opt, value, parser, *args ):
    # option parser callback for message '-m message'
    merge = args[0]
    vars = args[1]
    merge.set_log_message( value )
    vars["logMsgSet"] = 1

def __svndump_merge_example( option, opt, value, parser, *args ):
    # option parser callback for example output
    "prints a little usage example"

    print ""
    print "svndumpmerge.py \\"
    print "  -i proj1.dmp \\"
    print "  -r trunk trunk/proj1 -r tags tags/proj1 -r branches branches/proj1 \\"
    print "  -i proj2.dmp \\"
    print "  -r trunk trunk/proj2 -r tags tags/proj2 -r branches branches/proj2 \\"
    print "  -o merged.dmp \\"
    print "  -d trunk -d tags -d branches"
    print ""
    print "This commandline merges the svn dump files proj1.dmp and proj2.dmp"
    print "into one big dump file named merged.dmp."
    print "The contents of trunk of proj1 will be moved to trunk/proj1 and "
    print "tags into tags/proj1 and branches into branches/proj1. The same"
    print "renames are done with trunk tags and branches of proj2."
    print "The directories trunk tags and branches would not exist in the new"
    print "dump file if they weren't created with the -d options."
    print ""
    sys.exit( 0 )


def svndump_merge_cmdline( appname, args ):
    """cmdline..."""

    usage = "usage: %s [options]" % appname
    parser = OptionParser( usage=usage, version="%prog 0.1" )
    merge = SvnDumpMerge()
    vars = {}
    vars["fileIndex"] = -1
    vars["outFileSet"] = 0
    vars["logMsgSet"] = 0
    cbargs = ( merge, vars )
    parser.add_option( "-i", "--input-file",
                       action="callback", callback=__svndump_merge_opt_i,
                       callback_args=cbargs,
                       dest="infile",
                       nargs=1, type="string",
                       help="adds an input dump filename." )
    parser.add_option( "-r", "--rename",
                       action="callback", callback=__svndump_merge_opt_r,
                       callback_args=cbargs,
                       dest=" from to",
                       nargs=2, type="string",
                       help="adds a rename to the previously added file." )
    parser.add_option( "-x", "--mkdir-exclude",
                       action="callback", callback=__svndump_merge_opt_x,
                       callback_args=cbargs,
                       dest="dir",
                       nargs=1, type="string",
                       help="exclude mkdir from the previously added file." )
    parser.add_option( "-o", "--output-file",
                       action="callback", callback=__svndump_merge_opt_o,
                       callback_args=cbargs,
                       nargs=1, type="string",
                       dest="outfile",
                       help="sets the output filename." )
    parser.add_option( "-d", "--mkdir",
                       action="callback", callback=__svndump_merge_opt_d,
                       callback_args=cbargs,
                       nargs=1, type="string",
                       dest="dir",
                       help="create an additional directory." )
    parser.add_option( "-m", "--message",
                       action="callback", callback=__svndump_merge_opt_m,
                       callback_args=cbargs,
                       nargs=1, type="string",
                       dest="msg",
                       help="logmessage for the directory creating revision." )
    parser.add_option( "--example",
                       action="callback", callback=__svndump_merge_example,
                       callback_args=cbargs,
                       nargs=0,
                       dest="",
                       help="show a little usage example." )
    (options, args) = parser.parse_args( args )

    merge.merge()
    return 0

