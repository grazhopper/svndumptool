#===============================================================================
#
# Copyright (C) 2003 Martin Furter <mf@rola.ch>
# Copyright (C) 2007 CommProve, Inc (Eli Carter <eli.carter@commprove.com>)
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
import re

from svndump import __version, copy_dump_file

class RevisionPropertyTransformer:
    """
    A class for transforming the revision properties of a dump file class.
    """

    def __init__( self, propertyName, regexStr, replaceTemplate ):
        """
        Creates a RevisionPropertyTransformer class.

        @type propertyName: string
        @param propertyName: Name of the property to transform.
        @type regexStr: string
        @param regexStr: The regular expression to match the value against.
        @type replaceTemplate: string
        @param replaceTemplate: The replacement string (may contain group references, e.g. \1).
        """
        self.__property_name = propertyName
        self.__pattern = re.compile(regexStr)
        self.__replace_template = replaceTemplate
        
    def transform( self, dump ):
        if dump.has_rev_prop( self.__property_name ):
            value = dump.get_rev_prop_value( self.__property_name )
            matcher = self.__pattern.match(value)
            if matcher:
                replace_str = matcher.expand( self.__replace_template )
                dump.set_rev_prop_value( self.__property_name, replace_str )

def svndump_transform_revprop_cmdline( appname, args ):
    """
    Parses the commandline and executes the transformation.

    Usage:

        >>> svndump_transform_cmdline( sys.argv[0], sys.argv[1:] )

    @type appname: string
    @param appname: Name of the application (used in help text).
    @type args: list( string )
    @param args: Commandline arguments.
    @rtype: integer
    @return: Return code (0 = OK).
    """

    usage = "usage: %s propname regex replace source destination" % appname
    parser = OptionParser( usage=usage, version="%prog "+__version )
    (options, args) = parser.parse_args( args )

    if len( args ) != 5:
        print "specify exactly one propname to transform, one regex to match the value against,\none replacement string, one source dump file and one destination dump file."
        return 1

    copy_dump_file( args[3], args[4],  RevisionPropertyTransformer( args[0], args[1], args[2] ) )
    return 0

class PropertyTransformer:
    """
    A class for transforming the properties of a dump file class.
    """

    def __init__( self, propertyName, regexStr, replaceTemplate ):
        """
        Creates a RevisionPropertyTransformer class.

        @type propertyName: string
        @param propertyName: Name of the property to transform.
        @type regexStr: string
        @param regexStr: The regular expression to match the value against.
        @type replaceTemplate: string
        @param replaceTemplate: The replacement string (may contain group references, e.g. \1).
        """
        self.__property_name = propertyName
        self.__pattern = re.compile(regexStr, re.M)
        self.__replace_template = replaceTemplate

    def transform( self, dump ):
        for node in dump.get_nodes_iter():
            value = node.get_property(self.__property_name)
            if value != None:
                newvalue = self.__pattern.sub(self.__replace_template, value)
                node.set_property( self.__property_name, newvalue )

def svndump_transform_prop_cmdline( appname, args ):
    """
    Parses the commandline and executes the transformation.

    Usage:

        >>> svndump_transform_prop_cmdline( sys.argv[0], sys.argv[1:] )

    @type appname: string
    @param appname: Name of the application (used in help text).
    @type args: list( string )
    @param args: Commandline arguments.
    @rtype: integer
    @return: Return code (0 = OK).
    """

    usage = "usage: %s propname regex replace source destination" % appname
    parser = OptionParser( usage=usage, version="%prog "+__version )
    (options, args) = parser.parse_args( args )

    if len( args ) != 5:
        print "specify exactly one propname to transform, one regex to match the value against,\none replacement string, one source dump file and one destination dump file."
        return 1

    copy_dump_file( args[3], args[4],  PropertyTransformer( args[0], args[1], args[2] ) )
    return 0


