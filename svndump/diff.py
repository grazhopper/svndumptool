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

import md5
from optparse import OptionParser

from file import SvnDumpFile

class SvnDumpDiffCallback:
    """Callback function for SvnDumpDiff.

        blabla+++++"""

    def __init__( self, verbosity ):
        """Init method."""
        self.verbosity = verbosity
        self.diffs = False
        self.filename1 = ""
        self.filename2 = ""
        self.revnr1 = -1
        self.revnr2 = -1
        self.action = ""
        self.kind = ""
        self.path = ""
        self.index1 = -1
        self.index2 = -1
        self.__rev_printed = False
        self.__node_printed = False

    def comparing( self, filename1, filename2 ):
        """Called at the beginning."""

        self.filename1 = filename1
        self.filename2 = filename2
        if self.verbosity > 0:
            print "Comparing"
            print "    dump1: '%s'" % self.filename1
            print "    dump2: '%s'" % self.filename2

    def compare_done( self ):
        """Called at the end of the diff."""

        if self.verbosity > 0:
            if self.diffs:
                print "Done, found diffs."
            else:
                print "Done."

    def next_revision( self, revnr1, revnr2 ):
        """Called when starting to compare a new revision."""

        self.revnr1 = revnr1
        self.revnr2 = revnr2
        self.__rev_printed = False
        if self.verbosity > 1:
            self.__print_rev()

    def __print_rev( self ):
        if not self.__rev_printed:
            self.__rev_printed = True
            print "  Revision: %d/%d" % ( self.revnr1, self.revnr2 )

    def next_node( self, node, index1, index2 ):
        """Called when starting to compare a new node."""

        self.action = node.get_action()
        self.kind = node.get_kind()
        self.path = node.get_path()
        self.index1 = index1
        self.index2 = index2
        self.__node_printed = False
        if self.verbosity > 1:
            self.__print_node()

    def __print_node( self ):
        self.__print_rev()
        if not self.__node_printed:
            self.__node_printed = True
            print "  Node: %s %s '%s' (%d/%d)" % \
                ( self.action, self.kind, self.path, self.index1, self.index2 )

    def rev_diff( self, type, value1, value2 ):
        """Called when a difference has been found."""

        self.diffs = True
        if self.verbosity > 0:
            self.__print_rev()
            print "+ Different %s:" % type
            print "    dump1: '%s'" % value1
            print "    dump2: '%s'" % value2

    def node_diff( self, type, value1, value2 ):
        """Called when a difference has been found."""

        self.diffs = True
        if self.verbosity > 0:
            self.__print_node()
            print "+ Different %s:" % type
            print "    dump1: '%s'" % value1
            print "    dump2: '%s'" % value2

    def node_missing( self, dumpnr, node ):
        """Called when a node exists in one dump only."""

        self.diffs = True
        if self.verbosity > 0:
            self.__print_rev()
            print "+ Node missing in dump%d:" % dumpnr
            print "    Node: %s %s '%s'" % \
                ( node.get_action(), node.get_kind(), node.get_path() )

    def wrong_md5( self, dumpnr, should, calc ):
        """Called when text has worng MD5."""

        self.diffs = True
        if self.verbosity > 0:
            self.__print_node()
            print "+ Wrong MD5 in dump%d:" % dumpnr
            print "    should be:   '%s'" % should
            print "    calculated:  '%s'" % calc

    def text_diff( self, type ):
        """Called when text differs."""

        self.diffs = True
        if self.verbosity > 0:
            self.__print_node()
            print "+ Text differs in '%s'" % type
        
class SvnDumpDiff:
    """A class for comparing svn dump files."""

    def __init__( self, filename1, filename2 ):

        self.__filename1 = filename1
        self.__filename2 = filename2


    def execute( self, callback ):
        """Execute the diff."""

        # diff started
        callback.comparing( self.__filename1, self.__filename2 )

        # open files
        dump1 = SvnDumpFile()
        dump2 = SvnDumpFile()
        dump1.open( self.__filename1 )
        dump2.open( self.__filename2 )

        # compare uuid
        if dump1.get_uuid() != dump2.get_uuid():
            callback.rev_diff( "UUID", dump1.get_uuid(), dump2.get_uuid() )

        hasrev1 = dump1.read_next_rev()
        hasrev2 = dump2.read_next_rev()

        while hasrev1 and hasrev2:
            # compare rev numbers
            if dump1.get_rev_nr() != dump2.get_rev_nr():
                callback.rev_diff( "RevNr", dump1.get_rev_nr(), dump2.get_rev_nr() )
                hasrev1 = False
                hasrev2 = False
                break

            # next revision...
            callback.next_revision( dump1.get_rev_nr(), dump2.get_rev_nr() )

            # compare rev date
            if dump1.get_rev_date() != dump2.get_rev_date():
                callback.rev_diff( "RevDate", dump1.get_rev_date(), dump2.get_rev_date() )
            if dump1.get_rev_date_str() != dump2.get_rev_date_str():
                callback.rev_diff( "RevDateStr", dump1.get_rev_date_str(), dump2.get_rev_date_str() )

            # compare rev author
            # compare rev log
            # compare rev props
            # compare nodes
            self.__compare_nodes( dump1, dump2, callback )

            # read next revision
            hasrev1 = dump1.read_next_rev()
            hasrev2 = dump2.read_next_rev()

        if hasrev1 or hasrev2:
            print "random error ;-)"

        # done.
        callback.compare_done()

    def __compare_nodes( self, dump1, dump2, callback ):
        """Compares the nodes of the current revision of two dump files."""

        n1 = dump1.get_node_count()
        n2 = dump2.get_node_count()

        if n1 != n2:
            callback.rev_diff( "NodeCount", n1, n2 )

        list2 = {}
        for i in range( 0, n2 ):
            node = dump2.get_node( i )
            list2[ node.get_action() + ":" + node.get_path() ] = i
        indexlist = []
        for i in range( 0, n1 ):
            node = dump1.get_node( i )
            nodekey = node.get_action() + ":" + node.get_path()
            if list2.has_key( nodekey ):
                i2 = list2[ nodekey ]
                del list2[ nodekey ]
            else:
                i2 = -1
            indexlist.append( [ i, i2 ] )
        for nodekey, i2 in list2:
            indexlist.append( [ -1, i2 ] )

        for indices in indexlist:
            if indices[0] == -1:
                node2 = dump2.get_node( indices[1] )
                callback.node_missing( 1, node2 )
            elif indices[1] == -1:
                node1 = dump1.get_node( indices[0] )
                callback.node_missing( 1, node1 )
            else:
                node1 = dump1.get_node( indices[0] )
                node2 = dump2.get_node( indices[1] )
                callback.next_node( node1, indices[0], indices[1] )
                self.__compare_node( node1, node2, callback )

    def __compare_node( self, node1, node2, callback ):
        """Compare two nodes."""

        # compare path
        if node1.get_path() != node2.get_path():
            callback.node_diff( "Path", node1.get_path(), node2.get_path() )
            return
        # compare action
        if node1.get_action() != node2.get_action():
            callback.node_diff( "Action", node1.get_action(), node2.get_action() )
            return
        # compare kind
        if node1.get_kind() != node2.get_kind():
            callback.node_diff( "Kind", node1.get_kind(), node2.get_kind() )
            return
        # compare copy-from-path
        if node1.get_copy_from_path() != node2.get_copy_from_path():
            callback.node_diff( "CopyFromPath", node1.get_copy_from_path(), node2.get_copy_from_path() )
            return
        # compare copy-from-rev
        if node1.get_copy_from_rev() != node2.get_copy_from_rev():
            callback.node_diff( "CopyFromRev", node1.get_copy_from_rev(), node2.get_copy_from_rev() )
            return
        # properties...
        # compare text
        if node1.has_text() != node2.has_text():
            callback.node_diff( "HasText", node1.has_text(), node2.has_text() )
            return
        if not node1.has_text():
            # no text to compare
            return
        if node1.get_text_length() != node2.get_text_length():
            callback.node_diff( "TextLen", node1.get_text_length(), node2.get_text_length() )
        if node1.get_text_md5() != node2.get_text_md5():
            callback.node_diff( "TextMD5", node1.get_text_md5(), node2.get_text_md5() )
        md1 = md5.new()
        md2 = md5.new()
        handle1 = node1.text_open()
        handle2 = node2.text_open()
        str1 = node1.text_read( handle1 )
        str2 = node2.text_read( handle2 )
        n1 = len(str1)
        n2 = len(str2)
        old1 = ""
        old2 = ""
        cmpmode = 0
        havediff = 0
        while n1 > 0 or n2 > 0:
            md1.update( str1 )
            md2.update( str2 )
            if cmpmode == 0:
                if str1 != str2:
                    # have a diff
                    cmpmode = 2
                    havediff = 2
                    # check for EOL diff
                    if n1 == n2: # this cmp is crap!
                        n = self.__str_diff_index( str1, str2 )
                        if  str1[n] == "\n" or str1[n] == "\r" or \
                            str2[n] == "\n" or str2[n] == "\r":
                            # EOL mode
                            cmpmode = 1
                            havediff = 1
            #if cmpmode == 0:
            #   implement EOL stuff ++++++
            if n1 > 0:
                old1 = str1[-1]
                str1 = node1.text_read( handle1 )
                n1 = len(str1)
            if n2 > 0:
                old2 = str2[-1]
                str2 = node2.text_read( handle2 )
                n2 = len(str2)
        mdstr1 = md1.hexdigest()
        mdstr2 = md2.hexdigest()
        if node1.get_text_md5() != mdstr1:
            callback.wrong_md5( 1, node1.get_text_md5(), mdstr1 )
        if node2.get_text_md5() != mdstr2:
            callback.wrong_md5( 2, node2.get_text_md5(), mdstr2 )
        if havediff != 0:
            if havediff == 1:
                callback.text_diff( "EOL" )
            else:
                callback.text_diff( "Text" )

    def __str_diff_index( self, str1, str2 ):
        """Returns the index of the first diff between two strings."""

        n1 = len(str1)
        n2 = len(str2)
        if n1 > n2:
            n = n2
        else:
            n = n1
        i = 0
        while i < n:
            if str1[i] != str2[i]:
                return i
            i = i + 1
        return i
        # crap :(
        #nh = len(str1)
        #n = len(str2)
        #if n < nh:
        #    nh = n + 1
        #nl = 0
        #while (nh-nl) > 1:
        #    nm = (nh + nl) / 2
        #    if str1[:nm] == str2[:nm]:
        #        nl = nm
        #    else:
        #        nh = nm
        
                

def svndump_diff_cmdline( appname, args ):
    """cmdline..."""

    usage = "usage: %s [options] dump1 dump2" % appname
    parser = OptionParser( usage=usage, version="%prog 0.1" )
    parser.add_option( "-e", "--check-eol",
                       action="store_const", dest="eol", const=1, default=0,
                       help="check for EOL differences" )
    parser.add_option( "-E", "--ignore-eol",
                       action="store_const", dest="eol", const=2,
                       help="ignore EOL differences" )
    parser.add_option( "-q", "--quiet",
                       action="store_const", dest="verbose", const=0, default=1,
                       help="quiet output" )
    parser.add_option( "-v", "--verbose",
                       action="store_const", dest="verbose", const=2,
                       help="verbose output" )

    (options, args) = parser.parse_args( args )

    if len(args) != 2:
        print "please specify exactly two dump files."
        return 1

    diff = SvnDumpDiff( args[0], args[1] )
    callback = SvnDumpDiffCallback( options.verbose )

    #diff.set_input_file( args[0] )
    #if len( args ) == 2:
    #    diff.set_output_file( args[1] )
    #if options.mode == "prop":
    #    diff.set_mode_prop()
    #elif options.mode == "prop":
    #    diff.set_mode_regexp( options.regexp )

    diff.execute( callback )
    return 0
