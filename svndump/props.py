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
import os
import re

from svndump import __version, copy_dump_file, SvnDumpFile

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


class SvnConfigParser:

    def __init__( self, filename ):
        self._sections = {}
        ifd = open( filename, "r" )
        section = ""
        for line in ifd:
            line = line.strip()
            if len(line) == 0 or line[0] in ( ';', '#' ):
                # empty line or comment line
                pass
            elif line[0] == '[' and line[-1] == ']':
                # section
                section = line[1:-1].strip()
            else:
                parts = line.split( "=", 1 )
                key = parts[0].strip()
                if len( parts ) == 2 and len(key) > 0 and len(section) > 0:
                    if not self._sections.has_key( section ):
                        self._sections[section] = {}
                    self._sections[section][key] = parts[1].strip()

    def get( self, section, key ):
        if not self._sections.has_key( section ):
            return ""
        sdict = self._sections[section]
        if not sdict.has_key( key ):
            return ""
        return sdict[key]

    def items( self, section ):
        if not self._sections.has_key( section ):
            return []
        return self._sections[section].items()


class ApplyAutoprops:

    def __init__( self, inputfilename, outputfilename, configfile ):
        self.configfile = configfile
        self.inputfilename = inputfilename
        self.outputfilename = outputfilename
        self.autoprops = []

    def apply( self ):
        self._read_config()
        inDump = SvnDumpFile()
        outDump = SvnDumpFile()
        inDump.open( self.inputfilename )
        inDump.read_next_rev()
        outDump.create_like( self.outputfilename, inDump )
        while inDump.has_revision():
            outDump.add_rev( inDump.get_rev_props() )
            for index in range( 0, inDump.get_node_count() ):
                node = inDump.get_node( index )
                if node.get_action() == "add":
                    self._set_properties( node )
                outDump.add_node( node )
            inDump.read_next_rev()
        inDump.close()
        outDump.close()

    def _set_properties( self, node ):
        name = node.get_path().split( "/" )[-1]
        for regex, properties in self.autoprops:
            if regex.match( name ):
                for pname, pval in properties:
                    node.set_property( pname, pval )

    def _read_config( self ):
        cfg = SvnConfigParser( self.configfile )
        for key, value in cfg.items( "auto-props" ):
            regex = self._make_regex( key )
            properties = self._split_properties( value )
            self.autoprops.append( ( regex, properties ) )

    def _make_regex( self, expr ):
        expr = expr.replace( ".", "\\." )
        expr = expr.replace( "?", "." )
        expr = expr.replace( "*", ".*" )
        return re.compile( expr )

    def _split_properties( self, propstring ):
        properties = []
        for property in propstring.split( ";" ):
            namevalue = property.split( "=", 1 )
            if len(namevalue) == 1:
                namevalue.append( "" )
            name = namevalue[0].strip()
            value = namevalue[1].strip()
            if value == "" and name in ( "svn:executable", "svn:needs-lock" ):
                value = "*"
            properties.append( ( name, value ) )
        return tuple( properties )

def svndump_apply_autoprops_cmdline( appname, args ):
    """
    +++++ document me :)
    """

    usage = "usage: %s [options] inputdump outputdump" % appname
    parser = OptionParser( usage=usage, version="%prog "+__version )
    parser.add_option( "--config-file",
                       action="store", dest="configfile", default=None,
                       help="Subversion config file [default: $HOME/.subversion/config]." )

    (options, args) = parser.parse_args( args )

    if len(args) != 2:
        print "Please specify exactly one input and one output dump file."
        return 1

    configfile = options.configfile
    if configfile == None:
        home = os.environ["HOME"]
        configfile = os.path.join( home, ".subversion", "config" )

    aa = ApplyAutoprops( args[0], args[1], configfile )
    return aa.apply()

