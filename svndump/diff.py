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

from optparse import OptionParser

from file import SvnDumpFile

class SvnDumpDiff:
    """A class for comparing svn dump files."""

    def __init__( self, filename1, filename2 ):

        self.__filename1 = filename1
        self.__filename2 = filename2


    def execute( self ):
        """Execute the diff."""

        # open files
        dump1 = SvnDumpFile()
        dump2 = SvnDumpFile()
        dump1.open( self.__filename1 )
        dump2.open( self.__filename2 )

        # compare uuid
        if dump1.get_uuid() != dump2.get_uuid():
            print "Different UUID:"
            print "  dump1: %s" % dump1.get_uuid()
            print "  dump2: %s" % dump2.get_uuid()

        hasrev1 = dump1.readNextRev()
        hasrev2 = dump1.readNextRev()

        while hasrev1 and hasrev2:
            # compare rev numbers
            if dump1.get_rev_nr() != dump1.get_rev_nr():
                print "Different revision numbers:"
                print " dump1: %d" % dump1.get_rev_nr()
                print " dump2: %d" % dump2.get_rev_nr()
                hasrev1 = False
                hasrev2 = False
                break

            # compare rev date
            if dump1.get_rev_date() != dump2.get_rev_date() or \
                dump1.get_rev_date_str() != dump2.get_rev_date_str():
                print "Different revision dates:"
                print "  dump1 (r%d): %s (%d.%d)" % ( dump1.get_rev_nr(),
                        dump1.get_rev_date_str(),
                        dump1.get_rev_date()[0], dump1.get_rev_date()[1] )
                print "  dump2 (r%d): %s (%d.%d)" % ( dump2.get_rev_nr(),
                        dump2.get_rev_date_str(),
                        dump2.get_rev_date()[0], dump2.get_rev_date()[1] )

            # compare rev author
            # compare rev log
            # compare rev props
            # compare nodes
            self.__compare_nodes( dump1, dump2 )

            # read next revision
            hasrev1 = dump1.readNextRev()
            hasrev2 = dump1.readNextRev()

        if hasrev1 or hasrev2:
            print "random error ;-)"

    def __compare_nodes( self, dump1, dump2 ):
        """Compares the nodes of the current revision of two dump files."""

        n1 = dump1.get_node_count()
        n2 = dump2.get_node_count()

        if n1 != n2:
            print "Different node counts:"
            print "  dump1 (r%d): %d" % ( dump1.get_rev_nr(), n1 )
            print "  dump2 (r%d): %d" % ( dump2.get_rev_nr(), n2 )
            return

        for i in range( 0, n1 ):
            node1 = dump1.get_node( i )
            node2 = dump2.get_node( i )
            rn = "r%d,n%d" % ( dump1.get_rev_nr(), i )
            self.__compare_node( rn, node1, node2 )

    def __compare_node( self, rn, node1, node2 ):
        """Compare two nodes."""

        # compare path
        if node1.get_path() != node2.get_path():
            print "Different path:"
            print "  dump1(%s): '%s'" % ( rn, node1.get_path() )
            print "  dump2(%s): '%s'" % ( rn, node2.get_path() )
            return
        # compare action
        if node1.get_action() != node2.get_action():
            print "Different action:"
            print "  node     : '%s'" % node1.get_path()
            print "  dump1(%s): '%s'" % ( rn, node1.get_action() )
            print "  dump2(%s): '%s'" % ( rn, node2.get_action() )
            return
        # compare kind
        if node1.get_kind() != node2.get_kind():
            print "Different kind:"
            print "  node     : '%s'" % node1.get_path()
            print "  dump1(%s): '%s'" % ( rn, node1.get_kind() )
            print "  dump2(%s): '%s'" % ( rn, node2.get_kind() )
            return
        # compare copy-from-path
        if node1.get_copy_from_path() != node2.get_copy_from_path():
            print "Different kind:"
            print "  node     : '%s'" % node1.get_path()
            print "  dump1(%s): '%s'" % ( rn, node1.get_copy_from_path() )
            print "  dump2(%s): '%s'" % ( rn, node2.get_copy_from_path() )
            return
        # compare copy-from-rev
        if node1.get_copy_from_rev() != node2.get_copy_from_rev():
            print "Different kind:"
            print "  node     : '%s'" % node1.get_path()
            print "  dump1(%s): '%s'" % ( rn, node1.get_copy_from_rev() )
            print "  dump2(%s): '%s'" % ( rn, node2.get_copy_from_rev() )
            return
        # properties...
        # compare text
        if node1.has_text() != node2.has_text():
            print "Different 'has_text':"
            print "  node     : '%s'" % node1.get_path()
            print "  dump1(%s): '%s'" % ( rn, node1.has_text() )
            print "  dump2(%s): '%s'" % ( rn, node2.has_text() )
            return
        if not node1.has_text():
            # no text to compare
            return
        if node1.get_text_length() != node2.get_text_length():
            print "Different text length:"
            print "  node     : '%s'" % node1.get_path()
            print "  dump1(%s): '%s'" % ( rn, node1.get_text_length() )
            print "  dump2(%s): '%s'" % ( rn, node2.get_text_length() )
        if node1.get_text_md5() != node2.get_text_md5():
            print "Different text md5:"
            print "  node     : '%s'" % node1.get_path()
            print "  dump1(%s): '%s'" % ( rn, node1.get_text_md5() )
            print "  dump2(%s): '%s'" % ( rn, node2.get_text_md5() )
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
                    if n1 == n2:
                        n = self.__str_diff_index( str1, str2 )
                        if  str1[n] == "\n" or str1[n] == "\r" or \
                            str2[n] == "\n" or str2[n] == "\r":
                            # EOL mode
                            cmpmode = 1
                            havediff = 1
            #if cmpmode == 0:
            # implement EOL stuff ++++++
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
        if node1.get_text_md5() != mdstr1 or node2.get_text_md5() != mdstr2:
            print "Wrong text md5:"
            print "  node     : '%s'" % node1.get_path()
            print "  dump1(%s): '%s'" % ( rn, node1.get_text_md5() )
            print "     but is: '%s'" % mdstr1
            print "  dump2(%s): '%s'" % ( rn, node2.get_text_md5() )
            print "     but is: '%s'" % mdstr2
        if havediff != 0:
            if havediff == 1:
                print "Text differs (EOL only):"
            else:
                print "Text differs:"
            print "  node     : '%s'" % node1.get_path()

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
    #parser.add_option( "-m", "--mode",
    #                   action="store", dest="mode", default="prop",
    #                   type="choice", choices=[ "prop", "regexp" ],
    #                   help="text file detection mode: one of "
    #                        "'prop' [default], 'regexp'" )
    #parser.add_option( "-r", "--regexp",
    #                   action="append", dest="regexp",
    #                   help="regexp for matching text file names" )
    #parser.add_option( "--dry-run",
    #                   action="store_true", dest="dry_run", default=False,
    #                   help="just show what would be done but don't do it" )

    parser.add_option( "-e", "--check-eol",
                       action="store_const", dest="eol", const=1, default=0,
                       help="check for EOL differences" )
    parser.add_option( "-E", "--ignore-eol",
                       action="store_const", dest="eol", const=2,
                       help="ignore EOL differences" )

    (options, args) = parser.parse_args( args )

    print options
    print args

    eolfix = SvnDumpEolFix()

    eolfix.set_input_file( args[0] )
    if len( args ) == 2:
        eolfix.set_output_file( args[1] )
    if options.mode == "prop":
        eolfix.set_mode_prop()
    elif options.mode == "prop":
        eolfix.set_mode_regexp( options.regexp )

    eolfix.execute()
    return 0
