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

from os import stat
from stat import ST_SIZE
import md5

from common import *

class SvnDumpNode:
    """A node of a svn dump file."""

    def __init__( self, path, action, kind ):
        """Init method.

            - action: one of 'add', 'delete', 'change' or 'replace'
            - kind: kind of the node (file or dir)
            - path: path of the node"""

        # check action
        if action != "add" and action != "delete" and \
           action != "change" and action != "replace":
            raise SvnDumpException, "Unknown action '%s'." % action
        # check kind
        if action == "delete":
            if kind != "" and kind != "file" and kind != "dir":
                raise SvnDumpException, "Unknown kind '%s'" % kind
        else:
            if kind != "file" and kind != "dir":
                raise SvnDumpException, "Unknown kind '%s'" % kind
        # check path +++

        # path of this node relative to the repository root
        self.__path = path
        # action: 'add', 'change', 'delete' or 'replace'
        self.__action = action
        # kind: 'file', 'dir' or 'node' if not known
        self.__kind = kind
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
        # delete the temp file
        self.__file_delete = False
        # the file object to read from
        self.__file_obj = None

    def __del__( self ):
        """Delete method, cleanup temp file if needed."""
        if self.__file_delete and self.__file_name != "":
            # delete temp file ++++
            pass

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

    def get_property( self, name ):
        """Returns the property."""
        if self.__properties.has_key( name ):
            return self.__properties[key]
        else:
            return None

    def has_properties( self ):
        """Returns True if this node has properties."""
        return self.__properties != None

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

    def has_copy_from( self ):
        """Returns True when this node has copy-from-path and copy-from-rev."""
        return self.__copy_from_rev > 0 and self.__copy_from_path != ""

    def get_copy_from_path( self ):
        """Returns the path the node has been copied from or an empty string."""
        return self.__copy_from_path

    def get_copy_from_rev( self ):
        """Returns the revision the node has been copied from or zero."""
        return self.__copy_from_rev

    def set_copy_from( self, path, revnr ):
        """Sets copy-from-path and copy-from-rev.
        
            - path:     copy-from-path
            - revnr:    copy-from-rev"""

        if self.__action != "add" and self.__action != "replace":
            raise SvnDumpException, "Cannot set copy-from for action '%s'" \
                    % self.__action
        self.__copy_from_path = path
        self.__copy_from_rev = revnr

    def set_property( self, name, value ):
        """Sets a property for this node.

            - name:     property name
            - value:    property value"""

        if self.__action == "" or self.__action == "delete":
            raise SvnDumpException, "Cannot set properties for action '%s'" \
                    % self.__action
        if self.__properties == None:
            self.__properties = {}
        self.__properties[name] = value

    def del_property( self, name ):
        """Deletes a property for this node.

            - name:     property name"""

        if self.__action == "" or self.__action == "delete":
            raise SvnDumpException, "Cannot delete properties for action '%s'" \
                    % self.__action
        if self.__properties != None:
            if self.__properties.has_key( name ):
                del self.__properties[name]
                if len( self.__properties ) == 0:
                    self.__properties = None

    def set_properties( self, properties ):
        """Sets the properties for this node.

            - properties:   a dict containing the properties"""

        if self.__action == "" or self.__action == "delete":
            raise SvnDumpException, "Cannot set properties for action '%s'" \
                    % self.__action
        self.__properties = properties

    def set_text_file( self, filename, length=-1, md5="", delete=False ):
        """Sets the text for this node.

            The text will be read from the specified file.
            - filename:     name of the file
            - length:       length of the file
            - md5:          md5 sum of the text
            - delete:       if true delete the file"""

        if self.__action == "" or self.__action == "delete":
            raise SvnDumpException, "Cannot set text for action '%s'" \
                    % self.__action
        self.__file_name = filename
        self.__file_offset = 0
        # hmm, no destructors, how to delete that damn temp file ? +++
        self.__file_delete = delete
        if length == -1:
            length = stat( filename )[ST_SIZE]
        self.__text_len = length
        self.__text_md5 = md5
        if not is_valid_md5_string( md5 ):
            self.__calculate_md5()

    def set_text_fileobj( self, fileobj, offset, length, md5 ):
        """Sets the text for this node.

            The text will be read from the specified file.
            - fileobj:      a file object containing the text
            - offset:       offset of the text
            - length:       length of the text
            - md5:          md5 sum of the text"""

        if self.__action == "" or self.__action == "delete":
            raise SvnDumpException, "Cannot set text for action '%s'" \
                    % self.__action
        self.__file_obj = fileobj
        self.__file_offset = offset
        self.__text_len = length
        self.__text_md5 = md5
        #if !is_valid_md5_string( md5 ) or length == -1:
        #    self.__calculate_md5()

    def set_text_node( self, node ):
        """Sets the text for this node.

            The text will be set from the specified file.
            - node:         a node"""

        if self.__action == "" or self.__action == "delete":
            raise SvnDumpException, "Cannot set text for action '%s'" \
                    % self.__action
        self.__file_name = node.__file_name
        # dunno how to delete temp file so no special action here +++
        self.__file_delete = node.__file_delete
        self.__file_obj = node.__file_obj
        self.__file_offset = node.__file_offset
        self.__text_len = node.__text_len
        self.__text_md5 = node.__text_md5

    def write_text_to_file( self, outfile ):
        """Writes the text to the given file obj."""

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
            return ""

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
        n = 0
        while len(data) > 0:
            n = n + len(data)
            md.update( data )
            data = self.text_read( handle )
        self.__text_md5 = md.hexdigest()
        if self.__text_len == -1:
            self.__text_len = n
        self.text_close( handle )

