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

from common import *
from node import SvnDumpNode

class SvnDumpFile:
    "a class for reading/writing svn dump files"

    def __init__( self ):
        # states
        self.ST_NONE    =  0
        self.ST_READ    = 10
        self.ST_EOF     = 11
        self.ST_CREATE  = 20
        self.ST_WRITE   = 21

        # state of this SvnDumpFile
        self.__state = self.ST_NONE
        # name of the dump file
        self.__filename = ""
        # the file object to read from/write to
        self.__file = None
        # end of file
        self.__file_eof = 0
        # UUID of the repository
        self.__uuid = ""
        # curent revision number
        self.__rev_nr = 0
        # date of the revision
        self.__rev_date = [0,0]
        # start offset of the next revision
        self.__rev_start_offset = 0
        # revision properties
        self.__rev_props = {}
        # nodes of the revision (files, dirs)
        self.__nodes = []
        # offset of a tag list
        self.__tag_start_offset = 0
        # count lines for debugging
        self.__line__counting = 1
        self.__line_nr = 0
        self.__tag_start_line_nr = 0

        # variables and their default value


    def __read_line( self, raiseEof ):
        "read one line from teh dump file, returns (eof, line), line without LF"

        line = self.__file.readline()
        if self.__line__counting != 0:
            self.__line_nr = self.__line_nr + 1
        if len( line ) != 0:
            return 0, line[:-1]
        self.__file_eof = 1
        if raiseEof == 0:
            return 1, ""
        raise SvnDumpException, "unexpected end of file"

    def __read_bin( self, length ):
        "read LEN bytes"

        data = self.__file.read( length )
        if self.__line__counting != 0:
            self.__line_nr = self.__line_nr + data.count( "\n" )
        return data

    def __skip_bin( self, length ):
        "skip LEN bytes"

        if self.__line__counting == 0:
            self.__file.seek( self.__file.tell() + length )
            return
        nBytes = 4096
        while length > 0:
            if length < 4096:
                nBytes = length
            data = self.__file.read( nBytes )
            self.__line_nr = self.__line_nr + data.count( "\n" )
            length = length - nBytes

    def __skip_empty_line( self ):
        "read one line from the dump file and check that it is empty"

        eof, line = self.__read_line( 0 )
        if eof != 0 or len( line ) != 0:
            raise SvnDumpException, "expected empty line, found '%s'" % line
        return

    def __get_tag( self, raiseEof ):
        "read a Tag line (name: value)"

        eof, line = self.__read_line( raiseEof )
        if len( line ) == 0:
            return []
        words = line.split( " ", 1 )
        if len( words ) != 2:
            raise SvnDumpException, "illegal Tag line"
        return words

    def __get_tag_list( self ):
        "get a list of tags, end is an empty line"

        tags = {}
        self.__tag_start_offset = self.__file.tell()
        self.__tag_start_line_nr = self.__line_nr
        tag = self.__get_tag( 0 )
        while len( tag ) == 0:
            if self.__file_eof:
                return tags
            self.__tag_start_offset = self.__file.tell()
            self.__tag_start_line_nr = self.__line_nr
            tag = self.__get_tag( 0 )
        while len( tag ) == 2:
            tags[ tag[0] ] = tag[1]
            tag = self.__get_tag( 1 )
        return tags

    def __get_prop_list( self ):
        "get a list of properties"

        props = OrderedDict()
        eof, line = self.__read_line( 1 )
        while line != "PROPS-END":
            # key
            words = line.split()
            if len( words ) != 2 or (words[0] != "K" and words[0] != "D"):
                raise SvnDumpException, "illegal proprty key ???"
            key = self.__read_bin( int(words[1]) )
            self.__skip_empty_line()
            # value
            value = None
            if words[0] == "K":
                eof, line = self.__read_line( 1 )
                words = line.split()
                if len( words ) != 2 or words[0] != "V":
                    raise SvnDumpException, "illegal proprty value ???"
                value = self.__read_bin( int(words[1]) )
                self.__skip_empty_line()
            # set property
            props[key] = value
            # next line...
            eof, line = self.__read_line( 1 )
        return props


    def __create_prop_string( self, properties ):
        "create a string from a dict containing properties"

        propStr = ""
        if properties != None:
            for key, val in properties.items():
                if val != None:
                    # add/change property
                    propStr = propStr + ("K %d"%len(key)) + "\n" + key + "\n"
                    propStr = propStr + ("V %d"%len(val)) + "\n" + val + "\n"
                else:
                    # delete property
                    propStr = propStr + ("D %d"%len(key)) + "\n" + key + "\n"
            propStr = propStr + "PROPS-END\n"
        return propStr


    def __set_rev_date( self, dateStr ):
        "check a date string and return a valid one"

        date = parse_svn_date_str( dateStr )
        if self.__rev_nr > 1:
            if date[0] < self.__rev_date[0] or \
                    (date[0] == self.__rev_date[0] and date[1] <= self.__rev_date[1]):
                date[0] = self.__rev_date[0]
                date[1] = self.__rev_date[1] + 1
                if date[1] > 999999:
                    date[1] = 0
                    date[0] = date[0] + 1
        self.__rev_date[0] = date[0]
        self.__rev_date[1] = date[1]
        dat = time.localtime( self.__rev_date[0] )
        dstr = time.strftime( "%Y-%m-%dT%H:%M:%S", dat )
        mstr = ".%06dZ" % ( self.__rev_date[1] )
        return dstr + mstr

    #------------------------------------------------------------
    #  open / create / close

    def open( self, filename ):
        """open a dump file for reading and read the header
                - filename: name of an existing dump file"""

        # check state
        if self.__state != self.ST_NONE:
            raise SvnDumpException, "invalid state %d (should be %d)" % \
                        ( self.__state, self.ST_NONE )

        # set parameters
        self.__filename = filename

        # open the file for reading
        self.__file = open( filename, "r" )

        # check that it is a svn dump file
        tag = self.__get_tag( 1 )
        if tag[0] != "SVN-fs-dump-format-version:":
            raise SvnDumpException, "not a svn dump file ???"
        if tag[1] != "2":
            raise SvnDumpException, "wrong svn dump file version (expected 2 found %s)" % ( tag[1] )
        self.__skip_empty_line()

        # get UUID
        tag = self.__get_tag( 1 )
        if tag[0] != "UUID:":
            raise SvnDumpException, "missing UUID"
        self.__uuid = tag[1]
        self.__skip_empty_line()

        # done initializing
        self.__rev_start_offset = self.__file.tell()
        self.__state = self.ST_READ

    def create_with_rev_0( self, filename, uuid, rev0date ):
        """Create a new dump file.

            This method creates a new dump file starting with revision 0.
             - filename:    name of the new dump file
             - uuid:        uuid of the new dump file
             - rev0date:    date of revision 0"""

        # check state
        if self.__state != self.ST_NONE:
            raise SvnDumpException, "invalid state %d (should be %d)" % \
                        ( self.__state, self.ST_NONE )

        # set parameters
        self.__filename = filename
        self.__uuid = uuid

        # check rev0date
        rev0date = self.__set_rev_date( rev0date )

        # open file for writing
        self.__file = open( filename, "w" )

        # write header and uuid
        self.__file.writelines( [ "SVN-fs-dump-format-version: 2\n",
                                "\n",
                                "UUID: " + uuid + "\n",
                                "\n" ] )

        # write header and uuid
        self.__file.writelines( [ "Revision-number: 0\n",
                                "Prop-content-length: 56\n",
                                "Content-length: 56\n",
                                "\n",
                                "K 8\n",
                                "svn:date\n",
                                "V 27\n",
                                rev0date + "\n",
                                "PROPS-END\n",
                                "\n" ] )

        # done initializing
        self.__state = self.ST_CREATE

    def create_with_rev_n( self, filename, uuid, firstRevNr ):
        """create a new dump file
                - filename: name of the new dump file
                - uuid: uuid of the new dump file
                - firstRevNr: first revision number (>0)"""

        # check state
        if self.__state != self.ST_NONE:
            raise SvnDumpException, "invalid state %d (should be %d)" % \
                        ( self.__state, self.ST_NONE )

        # check firstRevNr
        if firstRevNr < 1:
            raise SvnDumpException, "invalid firstRevNr %d (should be >= 1)" % ( firstRevNr )

        # set parameters
        self.__filename = filename
        self.__uuid = uuid
        self.__rev_nr = firstRevNr - 1

        # open file for writing
        self.__file = open( filename, "w" )

        # write header and uuid
        self.__file.writelines( [ "SVN-fs-dump-format-version: 2\n",
                                "\n",
                                "UUID: " + uuid + "\n",
                                "\n" ] )

        # done initializing
        self.__state = self.ST_CREATE

    def close( self ):
        "close this svn dump file"

        # close only if state != ST_NONE
        if self.__state != self.ST_NONE:
            self.__file.close()
            self.__line_nr = 0
            self.__file_eof = 0
            del self.__filename
            del self.__uuid
            del self.__file
            #del self.__rev_props
            #del self.__nodes   +++ why can't i delete that ???
            self.__state = self.ST_NONE

    #------------------------------------------------------------
    #  read methods
    
    def read_next_rev( self ):
        "read the next revision"

        # check state
        if self.__state != self.ST_READ:
            raise SvnDumpException, "invalid state %d (should be %d)" % \
                        ( self.__state, self.ST_READ )

        # check for end of file
        if self.__file_eof:
            self.__state = self.ST_EOF
            return 0

        # go to start of revision
        if self.__rev_start_offset != self.__file.tell():
            self.__file.seek( self.__rev_start_offset )

        # get rev tags
        tags = self.__get_tag_list()
        self.__rev_nr = int( tags["Revision-number:"] )

        # read revision properties
        self.__rev_props = self.__get_prop_list()
        self.__skip_empty_line()
        if not self.__rev_props.has_key("svn:log"):
            self.__rev_props["svn:log"] = ""
        if not self.__rev_props.has_key("svn:author"):
            self.__rev_props["svn:author"] = ""
        #if self.__rev_props.has_key("svn:date"):
        #  self.__rev_props["svn:date"] = self.__set_rev_date( self.__rev_props["svn:date"] )
        #else:
        #  self.__rev_props["svn:date"] = self.__set_rev_date( self.__rev_props["svn:date"] )

        # read nodes (files, dirs)
        self.__nodes = []
        #self.nodeList = []
        tags = self.__get_tag_list()
        while len(tags) != 0:
            # check that it's not the next revision
            if tags.has_key( "Revision-number:" ):
                # go back to start of tag list
                self.__file.seek( self.__tag_start_offset )
                self.__line_nr = self.__tag_start_line_nr
                break
            # get node properties
            if tags.has_key( "Prop-content-length:" ):
                properties = self.__get_prop_list()
            else:
                properties = None
            # skip node data
            if tags.has_key( "Text-content-length:" ):
                tags["Text-content-length:"] = int( tags["Text-content-length:"] )
                offset = self.__file.tell()
                self.__skip_bin( tags["Text-content-length:"] )
                self.__skip_empty_line()
            else:
                offset = 0
            # add node
            path = tags["Node-path:"]
            action = tags["Node-action:"]
            if action == "delete":
                node = SvnDumpNode( path, action, "" )
            else:
                node = SvnDumpNode( path, action, tags["Node-kind:"] )
            if properties != None:
                node.set_properties( properties )
            if tags.has_key( "Node-copyfrom-path:" ):
                node.set_copy_from( tags["Node-copyfrom-path:"],
                                    int(tags["Node-copyfrom-rev:"]) )
            if tags.has_key( "Text-content-length:" ):
                node.set_text_fileobj( self.__file, offset,
                                       int(tags["Text-content-length:"]),
                                       tags["Text-content-md5:"] )
            self.__nodes.append( node )
            # next one...
            tags = self.__get_tag_list()

        self.__rev_start_offset = self.__file.tell()
        return 1

    def has_revision( self ):
        "Returns false when EOF occured."
        return self.__state == self.ST_READ or self.__state == self.ST_WRITE

    def get_uuid( self ):
        "Returns the UUID of this dump file."
        return self.__uuid

    def get_rev_nr( self ):
        "Returns the current revision number."
        return self.__rev_nr

    def get_rev_date( self ):
        "Returns the date of the current revision as [ time_t, millis ]."
        return self.__rev_date[:]

    def get_rev_date_str( self ):
        "Returns the date of the current revision as string."
        return self.__rev_props["svn:date"]

    def get_rev_author( self ):
        "Returns the author of the current revision."
        return self.__rev_props["svn:author"]

    def get_rev_log( self ):
        "Returns the log message of the current revision."
        return self.__rev_props["svn:log"]

    def get_rev_prop_names( self ):
        "Returns a list of revision property names of the current revision."
        return self.__rev_props.keys()

    def has_rev_prop( self, name ):
        "Returns true if the current revision has a property with the specified name."
        return self.__rev_props.has_key(name)

    def get_rev_props( self ):
        "Returns a dict containing the revision properties."
        return self.__rev_props

    def get_rev_prop_value( self, name ):
        "Returns the value of the revision property with the specified name."
        return self.__rev_props[name]

    def get_node_count( self ):
        "Returns the count of nodes of the current revision."
        return len( self.__nodes )

    def get_node( self, index ):
        "Returns the node at the given index."
        return self.__nodes[ index ]


    #------------------------------------------------------------
    #  write methods

    def add_rev_from_dump( self, dump ):
        """Add the current revision of the specified dump file to this dump file
            - dump: a dump file"""

        # check of state is done in add_rev
        # add revision and revprops
        self.add_rev( dump.get_rev_props() )

        # add nodes
        index = 0
        nodeCount = dump.get_node_count()
        while index < nodeCount:
            self.add_node( dump.get_node( index ) )
            index = index + 1

    def add_rev( self, revProps ):
        """Add a new revision to this dump file
                - revProps: a dict with revision properties"""

        # check state
        if self.__state != self.ST_WRITE and self.__state != self.ST_CREATE :
            raise SvnDumpException, "invalid state %d (should be %d or %d)" % ( self.__state, self.ST_CREATE, self.ST_WRITE )

        # set rev nr and check rev props
        self.__rev_nr = self.__rev_nr + 1
        if not revProps.has_key("svn:date"):
            revProps["svn:date"] = self.__set_rev_date( "" )
        else:
            revProps["svn:date"] = self.__set_rev_date( revProps["svn:date"] )
        if not revProps.has_key("svn:author"):
            revProps["svn:author"] = ""
        if not revProps.has_key("svn:log"):
            revProps["svn:log"] = ""

        propStr = self.__create_prop_string( revProps )
        # write revision
        self.__file.writelines( [ "Revision-number: %d\n" % self.__rev_nr,
                                "Prop-content-length: %d\n" % len(propStr),
                                "Content-length: %d\n" % len(propStr),
                                "\n",
                                propStr,
                                "\n" ] )

        # we have a revision now
        self.__state = self.ST_WRITE

    def add_node( self, node ):
        """Add a node to the current revision
                - node: the node to add (class SvnDumpNode)"""

        # check state
        if self.__state != self.ST_WRITE:
            raise SvnDumpException, "invalid state %d (should be %d)" % \
                        ( self.__state, self.ST_WRITE )

        # write the node
        self.__file.write( "Node-path: " + node.get_path() + "\n" )
        action = node.get_action()
        if action == "delete":
            # delete needs only the action
            self.__file.write( "Node-action: " + action + "\n" )
        else:
            # other actions than delete always have kind and action
            self.__file.write( "Node-kind: " + node.get_kind() + "\n" )
            self.__file.write( "Node-action: " + action + "\n" )
            # copied ?
            if node.get_copy_from_rev() != 0:
                self.__file.write( "Node-copyfrom-rev: %d\n" % \
                            node.get_copy_from_rev() )
                self.__file.write( "Node-copyfrom-path: " + \
                            node.get_copy_from_path() + "\n" )
            # calculate length's of properties text and total
            propstr = self.__create_prop_string( node.get_properties() )
            proplen = len( propstr )
            textlen = node.get_text_length()
            if node.has_text():
                totlen = proplen + textlen
            else:
                totlen = proplen
            # write length's of properties text and total
            if proplen > 0:
                self.__file.write( "Prop-content-length: %d\n" % proplen )
            if node.has_text():
                self.__file.write( "Text-content-length: %d\n" % textlen )
                self.__file.write( "Text-content-md5: %s\n" % node.get_text_md5() )
            if proplen > 0 or node.has_text():
                self.__file.write( "Content-length: %d\n" % totlen )
                self.__file.write( "\n" )
            # write properties
            if proplen > 0:
                self.__file.write( propstr )
            # write text
            if node.has_text():
                node.write_text_to_file( self.__file )
            self.__file.write( "\n" )
        # CR after each node
        self.__file.write( "\n" )


