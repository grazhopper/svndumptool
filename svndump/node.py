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

class SvnDumpNode:
    """A node of a svn dump file."""

    def __init__( self, path ):
        """init function.
            - path: path of the node"""
        # path of this node relative to the repository root
        self.__path = path
        # action: 'add', 'change', 'delete' or 'replace'
        self.__action = ""
        # kind: 'file', 'dir' or 'node' if not known
        self.__kind = ""
        # list of properties name=>value pairs
        self.__properties = None
        # length of the text (file data)
        self.__text_len = -1
        # md5 hash of the text
        self.__text_md5 = ""
        # the from path if copied else ""
        self.__copy_from_path = ""
        # the from revision if copied else 0
        self.__copy_from_rev = 0
        # offset into the file
        self.__file_offset = -1
        # name of the (temp) file
        self.__file_name = ""
        # the file object to read from
        self.__file_obj = None

    def get_path( self ):
        """Returns the path of this node."""
        return self.__path

    def get_action( self ):
        """Returns the action of this node.
        
            The action is one of 'add', 'change', 'delete' or 'replace'."""
        return self.__action

    def get_kind( self ):
        """Returns the kind of this node ('file', 'dir' or 'node')."""
        return self.__kind

    def get_properties( self ):
        """Returns the properties."""
        return self.__properties

    def has_text( self ):
        """Returns true when this node has text."""
        return self.__text_len >= 0

    def get_text_length( self ):
        """Returns the lenght of the text."""
        return self.__text_len

    def get_text_md5( self ):
        """Returns the MD5 hash of the text."""
        return self.__text_md5

    def get_copy_from_path( self ):
        """Returns the path the node has been copied from or an empty string."""
        return self.__copy_from_path

    def get_copy_from_rev( self ):
        """Returns the revision the node has been copied from or zero."""
        return self.__copy_from_rev

    def set_action_delete( self ):
        """Sets the action of this node to 'delete'."""
        self.__action = "delete"
        self.__kind = "node"

    def set_action_add_dir( self, properties, fromPath="", fromRev=0 ):
        """Add a directory.
            - properties: a dict containing properties (name/value pairs)
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "add"
        self.__kind = "dir"
        self.__properties = properties
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev

    def set_action_change_dir( self, properties, fromPath="", fromRev=0 ):
        """Change a directory.
            - properties: a dict containing properties (name/value pairs)
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "change"
        self.__kind = "dir"
        self.__properties = properties
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev

    def set_action_add_file_obj( self, properties, fileObj, offset, length, md5,
                             fromPath="", fromRev=0 ):
        """Change a file from the given file object.
            - properties: a dict containing properties (name/value pairs)
            - fileObj:    a file object
            - offset:     offset of the file in the file object
            - length:     length of the file
            - md5:        md5 of the file or empty string if unknown
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "add"
        self.__kind = "file"
        self.__properties = properties
        self.__file_obj = fileObj
        self.__file_offset = offset
        self.__text_len = length
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev
        if is_valid_md5_string( md5 ):
            self.__text_md5 = md5

    def set_action_add_file_name( self, properties, filename, length, md5,
                             fromPath="", fromRev=0 ):
        """Change a file from the given file object.
            - properties: a dict containing properties (name/value pairs)
            - fileObj:    a file object
            - length:     length of the file
            - md5:        md5 of the file or empty string if unknown
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "add"
        self.__kind = "file"
        self.__properties = properties
        self.__file_name = filename
        self.__file_offset = 0
        self.__text_len = length
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev
        if is_valid_md5_string( md5 ):
            self.__text_md5 = md5
        else:
            self.__calculate_md5()

    def set_action_add_file_node( self, properties, node, fromPath="", fromRev=0 ):
        """Change a file from the given file object.
            - properties: a dict containing properties (name/value pairs)
            - node:       an existing node
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "add"
        self.__kind = "file"
        self.__properties = properties
        self.__file_obj = node.fileObj
        self.__file_offset = node.fileOffset
        self.__file_name = node.fileName
        self.__text_len = node.textLen
        self.__text_md5 = node.textMD5
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev

    def set_action_change_file_obj( self, properties, fileObj, offset, length, md5,
                                fromPath="", fromRev=0 ):
        """Add a file from the given file object.
            - properties: a dict containing properties (name/value pairs)
            - fileObj:    a file object
            - offset:     offset of the file in the file object
            - length:     length of the file
            - md5:        md5 of the file or empty string if unknown
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "change"
        self.__kind = "file"
        self.__properties = properties
        self.__file_obj = fileObj
        self.__file_offset = offset
        self.__text_len = length
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev
        if is_valid_md5_string( md5 ):
            self.__text_md5 = md5

    def set_action_change_file_name( self, properties, filename, length, md5,
                                fromPath="", fromRev=0 ):
        """Add a file from the given file object.
            - properties: a dict containing properties (name/value pairs)
            - fileObj:    a file object
            - length:     length of the file
            - md5:        md5 of the file or empty string if unknown
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "change"
        self.__kind = "file"
        self.__properties = properties
        self.__file_name = filename
        self.__file_offset = 0
        self.__text_len = length
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev
        if is_valid_md5_string( md5 ):
            self.__text_md5 = md5
        else:
            self.__calculate_md5()

    def set_action_change_file_node( self, properties, node,
                                 fromPath="", fromRev=0 ):
        """Add a file from the given file object.
            - properties: a dict containing properties (name/value pairs)
            - node:       an existing node
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "change"
        self.__kind = "file"
        self.__properties = properties
        self.__file_obj = node.fileObj
        self.__file_offset = node.fileOffset
        self.__file_name = node.fileName
        self.__text_len = node.textLen
        self.__text_md5 = node.textMD5
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev

    def set_action_replace_file_obj( self, properties, fileObj, offset, length, md5,
                                fromPath="", fromRev=0 ):
        """Replace a file from the given file object.
            - properties: a dict containing properties (name/value pairs)
            - fileObj:    a file object
            - offset:     offset of the file in the file object
            - length:     length of the file
            - md5:        md5 of the file or empty string if unknown
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "replace"
        self.__kind = "file"
        self.__properties = properties
        self.__file_obj = fileObj
        self.__file_offset = offset
        self.__text_len = length
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev
        if is_valid_md5_string( md5 ):
            self.__text_md5 = md5

    def set_action_replace_file_name( self, properties, filename, length, md5,
                                fromPath="", fromRev=0 ):
        """Replace a file from the given file object.
            - properties: a dict containing properties (name/value pairs)
            - fileObj:    a file object
            - length:     length of the file
            - md5:        md5 of the file or empty string if unknown
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.__action = "replace"
        self.__kind = "file"
        self.__properties = properties
        self.__file_name = filename
        self.__file_offset = 0
        self.__text_len = length
        self.__copy_from_path = fromPath
        self.__copy_from_rev = fromRev
        if is_valid_md5_string( md5 ):
            self.__text_md5 = md5
        else:
            self.__calculate_md5()

    def write_text_to_file( self, outfile ):
        """Writes the text to the given file."""

        if self.__text_len == -1:
            raise SvnDumpException, "Node %s has no text" % self.__path
        if len(self.__file_name) > 0:
            self.__file_obj = open( self.__file_name, "r" )
        else:
            self.__file_obj.seek( self.__file_offset )
        cnt = self.__text_len
        while cnt > 0:
            bcnt = cnt
            if bcnt > 16384:
                bcnt = 16384
            outfile.write( self.__file_obj.read( bcnt ) )
            cnt = cnt - bcnt
        if len(self.__file_name) > 0:
            self.__file_obj.close()
            self.__file_obj = None

    def text_open( self ):
        """Open text.

            Returns a handle for text_read and text_close."""

        if self.__text_len == -1:
            raise SvnDumpException, "node has no text"

        # create handle
        handle = {}
        if len(self.__file_name) > 0:
            handle["file_obj"] = open( self.__file_name, "r" )
            handle["close"] = True
            handle["offset"] = 0
            handle["length"] = self.__text_len
            handle["pos"] = 0
        else:
            handle["file_obj"] = self.__file_obj
            handle["close"] = False
            handle["offset"] = self.__file_offset
            handle["length"] = self.__text_len
            handle["pos"] = 0
            self.__file_obj.seek( self.__file_offset )

        return handle

    def text_reopen( self, handle ):
        """Reopen the file."""

        handle["file_obj"].seek( handle["offset"] )
        handle["pos"] = 0

    def text_read( self, handle, count=16384 ):
        """Read some text."""

        # end of text ?
        if handle["pos"] >= handle["length"]:
            return None

        # is more text requested than remains
        if (handle["pos"] + count) > handle["length"]:
            count = handle["length"] - handle["pos"]
        # read it
        data = handle["file_obj"].read( count )
        handle["pos"] = handle["pos"] + count
        return data

    def text_close( self, handle ):
        """Close the handle."""

        if handle["close"]:
            handle["file_obj"].close()

    def __calculate_md5( self ):
        """Calculates the md5 of the text."""

        handle = self.text_open()
        md = md5.new()
        data = self.text_read( handle )
        while data != None:
            md.update( data )
            data = self.text_read( handle )
        self.__text_md5 = md.hexdigest()
        self.text_close( handle )

#    def convert_eol_hack( self, outfilename ):
#        """Writes the text to the given file and converts EOL to LF.
#        
#            This is a hack! should be redesigned!"""
#
#        # ++++ hack, delete should also have textLen -1
#        if self.__action == "delete":
#            return False
#        if self.__text_len == -1:
#            # no text so nothing to convert
#            return False
#        if len(self.__file_name) > 0:
#            # conversion allready done
#            return False
#        # check the file
#        self.__file_obj.seek( self.__file_offset )
#        cnt = self.__text_len
#        needsFix = False
#        while cnt > 0:
#            bcnt = cnt
#            if bcnt > 16384:
#                bcnt = 16384
#            str = self.__file_obj.read( bcnt )
#            if str.find( "\r" ) >= 0:
#                needsFix = True
#                break
#            cnt = cnt - bcnt
#        if not needsFix:
#            return False
#        # convert the file
#        self.__file_obj.seek( self.__file_offset )
#        cnt = self.__text_len
#        outfile = open( outfilename, "w+" )
#        md = md5.new()
#        while cnt > 0:
#            bcnt = cnt
#            if bcnt > 16384:
#                bcnt = 16384
#            str = self.__file_obj.read( bcnt ).replace( "\r\n", "\n" ).replace( "\r", "\n" )
#            md.update( str )
#            outfile.write( str )
#            cnt = cnt - bcnt
#        self.__text_len = outfile.tell()
#        self.__text_md5 = md.hexdigest()
#        self.__file_offset = 0
#        self.__file_obj = None
#        self.__file_name = outfilename
#        outfile.close()
#        return True
#
