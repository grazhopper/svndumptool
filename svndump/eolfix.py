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

class SvnDumpEolFix:
    """A class for fixing mixed EOL style files in a svn dump file."""

    def __init__( self ):

        # input file name
        self.__in_file = ""
        # output file name
        self.__out_file = ""
        # dry-run, do not create an output file
        self.__dry_run = True
        # temp files
        self.__temp_dir = "."
        self.__temp_file_max_nr = 0
        self.__temp_file_nr = 0

    def set_input_file( self, filename ):
        """Sets the input dump file name."""
        self.__in_file = filename

    def set_output_file( self, filename ):
        """Sets the output dump file name and clears the dry-run flag."""
        self.__out_file = filename

    def set_mode_prop( self ):
        """Sets mode to 'prop'.

            in this mode SvnDumpEolFix assumes text files have the property
            svn:eol-style set."""
        self.__is_text_file = self.__callback_prop
        self.__is_text_file_params = {}

    def set_mode_regexp( self, expressions ):
        """Sets mode to regexp.

            In this mode every file which matches at least one of the regexps
            is treated as text file."""
        self.__is_text_file = self.__callback_regexp
        self.__is_text_file_params = []
        for expr in expressions:
            self.__is_text_file_params.append( re.compile( expr ) )

    def set_mode_callback( self, callback, parameter ):
        """Sets mode to callback.

            ++++"""

        self.__is_text_file = callback
        self.__is_text_file_params = parameter

    def execute( self ):
        """Executes the EolFix."""

        srcdmp = SvnDumpFile()
        srcdmp.open( self.__in_file )

        dstdmp = None

        hasrev = srcdmp.read_next_rev()
        if hasrev:
            if not self.__dry_run:
                dstdmp = SvnDumpFile()
                if srcdmp.get_rev_nr() == 0:
                    # create new dump with revision 0
                    dstdmp.create_with_rev_0( dstfile, srcdmp.get_uuid(),
                                srcdmp.get_rev_date_str() )
                    hasrev = srcdmp.read_next_rev()
                else:
                    # create new dump starting with the same revNr
                    # as the input dump file
                    dstdmp.create_with_rev_n( dstfile, srcdmp.get_uuid(),
                                srcdmp.get_rev_nr() )
            # now copy all the revisions
            while hasrev:
                print "\n\n*** r%d ***\n" % srcdmp.get_rev_nr()
                self.__process_rev( srcdmp, dstdmp )
                hasrev = srcdmp.read_next_rev()

    def __process_rev( self, srcdmp, dstdmp ):
        """Process one revision."""

        # clear temp file nr (overwrite old files)
        self.__temp_file_nr = 0

        # add revision and revprops
        if dstdmp != None:
            dstdmp.add_rev( srcdmp.get_rev_props() )

        # process nodes
        index = 0
        nodeCount = srcdmp.get_node_count()
        while index < nodeCount:
            node = srcdmp.get_node( index )
            print "  '%s'" % node.get_path()
            istextfile = self.__is_text_file( srcdmp, node,
                                              self.__is_text_file_params )
            if istextfile and node.has_text():
                node = self.__convert_eol( node )
            if dstdmp != None:
                dstdmp.add_node( node )
            index = index + 1

    def __convert_eol( self, node ):
        """Convert EOL of a node"""

        if node.get_text_length == -1:
            # no text
            print "    is_text"
            return node

        # search for CR
        need_conv = False
        handle = node.text_open()
        data = node.text_read( handle )
        while len(data) > 0:
            if data.find( "\r" ) != -1:
                # found one, need to convert the file
                need_conv = True
                break
            data = node.text_read( handle )
        if need_conv:
            print "    is_text, convert"
            if self.__dry_run:
                # do not convert with --dry-run
                need_conv = False
        else:
            print "    is_text"
        if need_conv:
            # do the conversion
            node.text_reopen( handle )
            outfilename = self.__temp_file_name()
            outfile = open( outfilename, "w+" )
            outlen = 0
            md = md5.new()
            data = node.text_read( handle )
            carry = ""
            while len(data) > 0:
                if len(carry) != 0:
                    data = carry + data
                n = len( data ) - 1
                carry = data[n]
                if carry == "\r":
                    data = data[:n]
                else:
                    carry = ""
                data = data.replace( "\r\n", "\n" ).replace( "\r", "\n" )
                md.update( data )
                outfile.write( data )
                outlen = outlen + len( data )
                data = node.text_read( handle )
            if len( carry ) != 0:
                outfile.write( "\n" )
                outlen = outlen + 1
            outfile.close()
            newnode = SvnDumpNode( node.get_path(), node.get_action(),
                                   node.get_kind() )
            newnode.set_action( node.get_action() )
            if node.has_copy_from():
                newNode.set_copy_from( node.get_copy_from_path(),
                                       node.get_copy_from_rev() )
            if node.has_properties():
                newNode.set_properties( node.get_properties() )
            newNode.set_text_file( outfilename, outlen, md.hexdigest() )
        else:
            newnode = node

        node.text_close( handle )
        return newnode

    def __temp_file_name( self ):
        """Create temp file name"""
        self.__temp_file_nr = self.__temp_file_nr + 1
        if self.__temp_file_nr > self.__temp_file_max_nr:
            self.__temp_file_max_nr = self.__temp_file_nr
        return "%s/tmpnode%d" % ( self.__temp_dir, self.__temp_file_nr )

    def __callback_prop( self, dumpfile, node, textfiles ):
        """Check for property and do conversion if needed."""

        # do we allready know that it is a textfile ?
        if textfiles.has_key( node.get_path() ):
            if node.get_action() == "delete":
                del textfiles[node.get_path()]
            return True

        # handle copy-from-path ??? +++

        # check properties
        properties = node.get_properties()
        if properties == None:
            return False
        if not properties.has_key("svn:eol-style"):
            return False

        # is a text file, add to the list
        textfiles[node.get_path()] = dumpfile.get_rev_nr()
        return True

    def __callback_regexp( self, dumpfile, node, expressions ):
        """Check regexp list and do conversion if needed."""

        for re in expressions:
            if re.match( node.get_path() ) != None:
                return True
        return False


def svndump_eol_fix_cmdline( appname, args ):
    """cmdline..."""

    usage = "usage: %s [options] src dst" % appname
    parser = OptionParser( usage=usage, version="%prog 0.1" )
    parser.add_option( "-m", "--mode",
                       action="store", dest="mode", default="prop",
                       type="choice", choices=[ "prop", "regexp" ],
                       help="text file detection mode: one of "
                            "'prop' [default], 'regexp'" )
    parser.add_option( "-r", "--regexp",
                       action="append", dest="regexp",
                       help="regexp for matching text file names" )
    parser.add_option( "--dry-run",
                       action="store_true", dest="dry_run", default=False,
                       help="just show what would be done but don't do it" )
    (options, args) = parser.parse_args( args )

    print options
    print args

    #if len( args ) < 1 or len( args ) > 2:
    #    print

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
        

