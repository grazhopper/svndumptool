#!/usr/bin/env python
#===============================================================================
#
# Copyright (C) 2003 Martin Furter <mf@rola.ch>
#
# This file is part of SvnDumpMerge
#
# SvnDumpMerge is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# SvnDumpMerge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SvnDumpMerge; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#
#===============================================================================
#
# TODO:
#
# - lots of testing...
# - add automatic creation of missing directories ?
#       hmm, hard stuff, i'd have to simulate the whole svn stuff :(
# - make the code look better...
# - better documentation...
#

"""svndumpmerge.py"""
__revision__ = "svndumpmerge.py V0.1" 

import sys
import time

# OrderedDict: a class stolen from Innoconda
# http://twistedmatrix.com/~moonfallen/innoconda.html
class OrderedDict(dict):
    """A dict which you can access in order through items() or popitem().
    Supports all normal dict operations, but keep in mind that if you update()
    it from a regular (non-ordered) dict, the new items will not be in any
    order (but will follow all the old items). Updating from another
    OrderedDict will preserve the order of both dicts."""
    def __init__(self, t=()):
        self.order = []
        for k, v in t:
            self[k] = v
    def __setitem__(self, k, v):
        # Replacing items with the same value changes the order, so don't
        # replace items
        if k in self.keys() and v==self[k]:
            return
        dict.__setitem__(self, k, v)
        if k in self.order:
            self.order.remove(k)
        self.order.append(k)
    def __delitem__(self, k):
        dict.__delitem__(self, k)
        self.order.remove(k)
    def items(self):
        """Return a list with the dict's items, in order"""
        return [(k, dict.get(self, k)) for k in self.order]
    def copy(self):
        #new1 = WhinyOrderedDict()
        new1 = OrderedDict()
        for k, v in self.items():
            new1[k] = v
        return new1
    def update(self, d):
        for k,v in d.items(): self[k] = v
    def clear(self):
        r = dict.clear(self)
        self.order = []
        return r
    def popitem(self):
        k, v = self.items()[0]
        del self[k]
        return k, v
    # added by mf for getting ordered keys
    def keys(self):
        return self.order
    # comment by MFen #python@freenode
    # def values(self): return zip(*self.items())[1]
    # func( *list )  ==  func( list[0], list[1], ..., list[len(list)] )
    # that trick is sometimes called unzip.
    # if l3=zip(l1, l2) then zip(*l3) == (l1, l2)
    # sorta.  you always end up with tuples of course


class SvnDumpFileException(Exception):
    "a simple exception class"
    def __init__( self, text ):
        self.text = text
    def __str__( self ):
        return self.text

class SvnDumpNode:
    "a node of a svn dump file"

    # action: 'add', 'change', 'delete' or 'replace'
    action = ""
    # kind: 'file', 'dir' or 'node' if not known
    kind = ""
    # list of properties name=>value pairs
    properties = None
    # length of the text (file data)
    textLen = 0
    # md5 hash of the text
    textMD5 = ""
    # the from path if copied else ""
    copyFromPath = ""
    # the from revision if copied else 0
    copyFromRev = 0
    # offset into the file
    fileOffset = -1

    def __init__( self, path ):
        """init function.
                - path: path of the node"""
        self.path = path

    def isValidMD5( self, md5 ):
        "checks a md5 string"
        if len( md5 ) != 32:
            return 0
        return 1

    def getPath( self ):
        "Returns the path of this node"
        return self.path

    def getAction( self ):
        "Returns the action of this node"
        return self.action

    def getKind( self ):
        "Returns the kind of this node ('file', 'dir' or 'node')"
        return self.kind

    def getProperties( self ):
        "Returns the properties"
        return self.properties

    def hasText( self ):
        "Returns true when this node has text"
        return self.textLen >= 0

    def getTextLength( self ):
        "Returns the lenght of the text"
        return self.textLen

    def getTextMD5( self ):
        "Returns the MD5 hash of the text"
        return self.textMD5

    def getCopyFromPath( self ):
        "Returns the path the node has been copied from or an empty string"
        return self.copyFromPath

    def getCopyFromRev( self ):
        "Returns the revision the node has been copied from or zero"
        return self.copyFromRev

    def setActionDelete( self ):
        "sets the action of this node to 'delete'"
        self.action = "delete"
        self.kind = "node"

    def setActionAddDir( self, properties, fromPath="", fromRev=0 ):
        """add a directory
            - properties: a dict containing properties (name/value pairs)
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.action = "add"
        self.kind = "dir"
        self.properties = properties
        self.textLen = -1
        self.copyFromPath = fromPath
        self.copyFromRev = fromRev

    def setActionChangeDir( self, properties, fromPath="", fromRev=0 ):
        """change a directory
            - properties: a dict containing properties (name/value pairs)
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.action = "change"
        self.kind = "dir"
        self.properties = properties
        self.textLen = -1
        self.copyFromPath = fromPath
        self.copyFromRev = fromRev

    def setActionAddFileObj( self, properties, fileObj, offset, length, md5,
                             fromPath="", fromRev=0 ):
        """change a file from the given file object
            - properties: a dict containing properties (name/value pairs)
            - fileObj:    a file object
            - offset:     offset of the file in the file object
            - length:     length of the file
            - md5:        md5 of the file or empty string if unknown
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.action = "add"
        self.kind = "file"
        self.properties = properties
        self.fileObj = fileObj
        self.fileOffset = offset
        self.textLen = length
        self.copyFromPath = fromPath
        self.copyFromRev = fromRev
        if self.isValidMD5( md5 ):
            self.textMD5 = md5

    def setActionAddFileNode( self, properties, node, fromPath="", fromRev=0 ):
        """change a file from the given file object
            - properties: a dict containing properties (name/value pairs)
            - node:       an existing node
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.action = "add"
        self.kind = "file"
        self.properties = properties
        self.fileObj = node.fileObj
        self.fileOffset = node.fileOffset
        self.textLen = node.textLen
        self.textMD5 = node.textMD5
        self.copyFromPath = fromPath
        self.copyFromRev = fromRev

    def setActionChangeFileObj( self, properties, fileObj, offset, length, md5,
                                fromPath="", fromRev=0 ):
        """add a file from the given file object
            - properties: a dict containing properties (name/value pairs)
            - fileObj:    a file object
            - offset:     offset of the file in the file object
            - length:     length of the file
            - md5:        md5 of the file or empty string if unknown
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.action = "change"
        self.kind = "file"
        self.properties = properties
        self.fileObj = fileObj
        self.fileOffset = offset
        self.textLen = length
        self.copyFromPath = fromPath
        self.copyFromRev = fromRev
        if self.isValidMD5( md5 ):
            self.textMD5 = md5

    def setActionChangeFileNode( self, properties, node,
                                 fromPath="", fromRev=0 ):
        """add a file from the given file object
            - properties: a dict containing properties (name/value pairs)
            - node:       an existing node
            - fromPath (opt): the path the node has been copied from
            - fromRev (opt): the revision the node has been copied from or zero"""

        self.action = "change"
        self.kind = "file"
        self.properties = properties
        self.fileObj = node.fileObj
        self.fileOffset = node.fileOffset
        self.textLen = node.textLen
        self.textMD5 = node.textMD5
        self.copyFromPath = fromPath
        self.copyFromRev = fromRev

    def writeToFile( self, outfile ):
        "Writes the text to the given file"

        if self.textLen == -1:
            raise SvnDumpFileException, "Node %s has no text" % self.path
        self.fileObj.seek( self.fileOffset )
        cnt = self.textLen
        while cnt > 0:
            bcnt = cnt
            if bcnt > 16384:
                bcnt = 16384
            outfile.write( self.fileObj.read( bcnt ) )
            cnt = cnt - bcnt


class SvnDump:
    "a class for reading/writing svn dump files"

    # states
    ST_NONE       = 0
    ST_READ       = 10
    ST_EOF        = 11
    ST_CREATE     = 20
    ST_WRITE      = 21

    # variables and their default value
    state = ST_NONE
    revNr = 0
    lineNr = 0
    lineCounting = 1
    fileEof = 0
    revDate = [0,0]
    nodes = []


    def readLine( self, raiseEof ):
        "read one line from teh dump file, returns (eof, line), line without LF"

        line = self.file.readline()
        if self.lineCounting != 0:
            self.lineNr = self.lineNr + 1
        if len( line ) != 0:
            return 0, line[:-1]
        self.fileEof = 1
        if raiseEof == 0:
            return 1, ""
        raise SvnDumpFileException, "unexpected end of file"

    def readBin( self, length ):
        "read LEN bytes"

        data = self.file.read( length )
        if self.lineCounting != 0:
            self.lineNr = self.lineNr + data.count( "\n" )
        return data

    def skipBin( self, length ):
        "skip LEN bytes"

        if self.lineCounting == 0:
            self.file.seek( self.file.tell() + length )
            return
        nBytes = 4096
        while length > 0:
            if length < 4096:
                nBytes = length
            data = self.file.read( nBytes )
            self.lineNr = self.lineNr + data.count( "\n" )
            length = length - nBytes

    def skipEmptyLine( self ):
        "read one line from the dump file and check that it is empty"

        eof, line = self.readLine( 0 )
        if eof != 0 or len( line ) != 0:
            raise SvnDumpFileException, "expected empty line, found '%s'" % line
        return

    def getTag( self, raiseEof ):
        "read a Tag line (name: value)"

        eof, line = self.readLine( raiseEof )
        if len( line ) == 0:
            return []
        words = line.split( " ", 1 )
        if len( words ) != 2:
            raise SvnDumpFileException, "illegal Tag line"
        return words

    def getTagList( self ):
        "get a list of tags, end is an empty line"

        tags = {}
        self.tagStartOffset = self.file.tell()
        self.tagStartLineNr = self.lineNr
        tag = self.getTag( 0 )
        while len( tag ) == 0:
            if self.fileEof:
                return tags
            self.tagStartOffset = self.file.tell()
            self.tagStartLineNr = self.lineNr
            tag = self.getTag( 0 )
        while len( tag ) == 2:
            tags[ tag[0] ] = tag[1]
            tag = self.getTag( 1 )
        return tags

    def getPropList( self ):
        "get a list of properties"

        props = OrderedDict()
        eof, line = self.readLine( 1 )
        while line != "PROPS-END":
            # key
            words = line.split()
            if len( words ) != 2 or words[0] != "K":
                raise SvnDumpFileException, "illegal proprty key ???"
            key = self.readBin( int(words[1]) )
            self.skipEmptyLine()
            # value
            eof, line = self.readLine( 1 )
            words = line.split()
            if len( words ) != 2 or words[0] != "V":
                raise SvnDumpFileException, "illegal proprty value ???"
            value = self.readBin( int(words[1]) )
            self.skipEmptyLine()
            # set property
            props[key] = value
            # next line...
            eof, line = self.readLine( 1 )
        return props


    def createPropString( self, properties ):
        "create a string from a dict containing properties"

        propStr = ""
        if properties != None:
            for key, val in properties.items():
                propStr = propStr + "K " + ("%d"%len(key)) + "\n" + key + "\n"
                propStr = propStr + "V " + ("%d"%len(val)) + "\n" + val + "\n"
            propStr = propStr + "PROPS-END\n"
        return propStr


    # perhaps some of these date functions can be replaced by
    # functions provided by the svn python bindings +++++
    # <sussman> it's our own string format, in libsvn_subr/time.c
    # <sussman> svn_time_[to|from]_cstring()
    def parseSvnDateStr( self, dateStr ):
        "parse a svn date string and return a list containing time_t and micros"
        if len(dateStr) != 27:
            return [0,0]
        if dateStr[19] != "." or dateStr[26] != "Z":
            return [0,0]
        dat = time.strptime( dateStr[:19], "%Y-%m-%dT%H:%M:%S" )
        return [ int(time.mktime(dat)), int( dateStr[20:26] ) ]

    def setRevDate( self, dateStr ):
        "check a date string and return a valid one"

        date = self.parseSvnDateStr( dateStr )
        if self.revNr > 1:
            if date[0] < self.revDate[0] or \
                    (date[0] == self.revDate[0] and date[1] <= self.revDate[1]):
                date[0] = self.revDate[0]
                date[1] = self.revDate[1] + 1
                if date[1] > 999999:
                    date[1] = 0
                    date[0] = date[0] + 1
        self.revDate[0] = date[0]
        self.revDate[1] = date[1]
        dat = time.localtime( self.revDate[0] )
        dstr = time.strftime( "%Y-%m-%dT%H:%M:%S", dat )
        mstr = ".%06dZ" % ( self.revDate[1] )
        return dstr + mstr



    ############################
    ####                    ####
    ####   PUBLIC METHODS   ####
    ####                    ####
    ############################

    ##  open / create / close

    def open( self, filename ):
        """open a dump file for reading and read the header
                - filename: name of an existing dump file"""

        # check state
        if self.state != self.ST_NONE:
            raise SvnDumpFileException, "invalid state %d (should be %d)" % \
                        ( self.state, self.ST_NONE )

        # set parameters
        self.filename = filename

        # open the file for reading
        self.file = open( filename, "r" )

        # check that it is a svn dump file
        tag = self.getTag( 1 )
        if tag[0] != "SVN-fs-dump-format-version:":
            raise SvnDumpFileException, "not a svn dump file ???"
        if tag[1] != "2":
            raise SvnDumpFileException, "wrong svn dump file version (expected 2 found %s)" % ( tag[1] )
        self.skipEmptyLine()

        # get UUID
        tag = self.getTag( 1 )
        if tag[0] != "UUID:":
            raise SvnDumpFileException, "missing UUID"
        self.uuid = tag[1]
        self.skipEmptyLine()

        # done initializing
        self.revStartOffset = self.file.tell()
        self.state = self.ST_READ

    def createWithRev0( self, filename, uuid, rev0date ):
        """create a new dump file
                - filename: name of the new dump file
                - uuid: uuid of the new dump file
                - rev0date: date of revision 0"""

        # check state
        if self.state != self.ST_NONE:
            raise SvnDumpFileException, "invalid state %d (should be %d)" % \
                        ( self.state, self.ST_NONE )

        # set parameters
        self.filename = filename
        self.uuid = uuid

        # check rev0date
        rev0date = self.setRevDate( rev0date )

        # open file for writing
        self.file = open( filename, "w" )

        # write header and uuid
        self.file.writelines( [ "SVN-fs-dump-format-version: 2\n",
                                "\n",
                                "UUID: " + uuid + "\n",
                                "\n" ] )

        # write header and uuid
        self.file.writelines( [ "Revision-number: 0\n",
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
        self.state = self.ST_CREATE

    def createWithRevN( self, filename, uuid, firstRevNr ):
        """create a new dump file
                - filename: name of the new dump file
                - uuid: uuid of the new dump file
                - firstRevNr: first revision number (>0)"""

        # check state
        if self.state != self.ST_NONE:
            raise SvnDumpFileException, "invalid state %d (should be %d)" % \
                        ( self.state, self.ST_NONE )

        # check firstRevNr
        if firstRevNr < 1:
            raise SvnDumpFileException, "invalid firstRevNr %d (should be >= 1)" % ( firstRevNr )

        # set parameters
        self.filename = filename
        self.uuid = uuid
        self.revNr = firstRevNr - 1

        # open file for writing
        self.file = open( filename, "w" )

        # write header and uuid
        self.file.writelines( [ "SVN-fs-dump-format-version: 2\n",
                                "\n",
                                "UUID: " + uuid + "\n",
                                "\n" ] )

        # done initializing
        self.state = self.ST_CREATE

    def close( self ):
        "close this svn dump file"

        # close only if state != ST_NONE
        if self.state != self.ST_NONE:
            self.file.close()
            self.lineNr = 0
            self.fileEof = 0
            del self.filename
            del self.uuid
            del self.file
            #del self.revProps
            #del self.nodes   +++ why can't i delete that ???
            self.state = self.ST_NONE

    ##  read methods
    
    def readNextRev( self ):
        "read the next revision"

        # check state
        if self.state != self.ST_READ:
            raise SvnDumpFileException, "invalid state %d (should be %d)" % \
                        ( self.state, self.ST_READ )

        # check for end of file
        if self.fileEof:
            self.state = self.ST_EOF
            return 0

        # go to start of revision
        if self.revStartOffset != self.file.tell():
            self.file.seek( self.revStartOffset )

        # get rev tags
        tags = self.getTagList()
        self.revNr = int( tags["Revision-number:"] )
        # these are not used
        #self.propContLen = int( tags["Prop-content-length:"] )
        #self.contLen = int( tags["Content-length:"] )

        # read revision properties
        self.revProps = self.getPropList()
        self.skipEmptyLine()
        if not self.revProps.has_key("svn:log"):
            self.revProps["svn:log"] = ""
        if not self.revProps.has_key("svn:author"):
            self.revProps["svn:author"] = ""
        #if self.revProps.has_key("svn:date"):
        #  self.revProps["svn:date"] = self.setRevDate( self.revProps["svn:date"] )
        #else:
        #  self.revProps["svn:date"] = self.setRevDate( self.revProps["svn:date"] )

        # read nodes (files, dirs)
        self.nodes = []
        #self.nodeList = []
        tags = self.getTagList()
        while len(tags) != 0:
            # check that it's not the next revision
            if tags.has_key( "Revision-number:" ):
                # go back to start of tag list
                self.file.seek( self.tagStartOffset )
                self.lineNr = self.tagStartLineNr
                break
            # get node properties
            if tags.has_key( "Prop-content-length:" ):
                properties = self.getPropList()
            else:
                properties = None
            # skip node data
            if tags.has_key( "Text-content-length:" ):
                tags["Text-content-length:"] = int( tags["Text-content-length:"] )
                offset = self.file.tell()
                self.skipBin( tags["Text-content-length:"] )
                self.skipEmptyLine()
            else:
                offset = 0
            # add node
            path = tags["Node-path:"]
            node = SvnDumpNode( path )
            action = tags["Node-action:"]
            if action == "delete":
                node.setActionDelete()
            elif action == "add" or action == "change":
                kind = tags["Node-kind:"]
                if tags.has_key( "Node-copyfrom-path:" ):
                    copypath = tags["Node-copyfrom-path:"]
                    copyrev = int(tags["Node-copyfrom-rev:"])
                else:
                    copypath = ""
                    copyrev = 0
                if kind == "dir":
                    if action == "add":
                        node.setActionAddDir( properties, copypath, copyrev )
                    else:
                        node.setActionChangeDir( properties, copypath, copyrev )
                elif kind == "file":
                    if tags.has_key( "Text-content-length:" ):
                        textlen = tags["Text-content-length:"]
                        textmd5 = tags["Text-content-md5:"]
                    else:
                        textlen = -1
                        textmd5 = ""
                    if action == "add":
                        node.setActionAddFileObj( properties, self.file,
                                offset, textlen, textmd5, copypath, copyrev )
                    else:
                        node.setActionChangeFileObj( properties, self.file,
                                offset, textlen, textmd5, copypath, copyrev )
                else:
                    print "unsupported node kind '%s' for action '%s'" % \
                                ( kind, action )
                    action = ""
            else:
                print "unsupported action '%s'" % ( action )
                action = ""
            if action != "":
                self.nodes = self.nodes + [ node ]
            # next one...
            tags = self.getTagList()

        self.revStartOffset = self.file.tell()
        return 1

    def hasRevision( self ):
        "Returns false when EOF occured"
        return self.state == self.ST_READ or self.state == self.ST_WRITE

    def getUUID( self ):
        "returns the UUID of this dump file"
        return self.uuid

    def getRevNr( self ):
        "Returns the current revision number"
        return self.revNr

    def getRevDate( self ):
        "Returns the date of the current revision as [ time_t, millis ]"
        return self.revDate[:]

    def getRevDateStr( self ):
        "Returns the date of the current revision as string"
        return self.revProps["svn:date"]

    def getRevAuthor( self ):
        "Returns the author of the current revision"
        return self.revProps["svn:author"]

    def getRevLog( self ):
        "Returns the log message of the current revision"
        return self.revProps["svn:log"]

    def getRevPropNames( self ):
        "Returns a list of revision property names of the current revision"
        return self.revProps.keys()

    def hasRevProp( self, name ):
        "Returns true if the current revision has a property with the specified name"
        return self.revProps.has_key(name)

    def getRevProps( self ):
        "returns a dict containing the revision properties"
        return self.revProps

    def getRevPropValue( self, name ):
        "Returns the value of the revision property with the specified name"
        return self.revProps[name]

    def getNodeCount( self ):
        "Returns the count of nodes of the current revision"
        return len( self.nodes )

    def getNode( self, index ):
        "Returns the node at the given index"
        return self.nodes[ index ]


    ##  write methods

    def addRevisionFromDump( self, dump ):
        """Add the current revision of the specified dump file to this dump file
            - dump: a dump file"""

        # check of state is done in addRevision
        # add revision and revprops
        self.addRevision( dump.getRevProps() )

        # add nodes
        index = 0
        nodeCount = dump.getNodeCount()
        while index < nodeCount:
            self.addNode( dump.getNode( index ) )
            index = index + 1

    def addRevision( self, revProps ):
        """Add a new revision to this dump file
                - revProps: a dict with revision properties"""

        # check state
        if self.state != self.ST_WRITE and self.state != self.ST_CREATE :
            raise SvnDumpFileException, "invalid state %d (should be %d or %d)" % ( self.state, self.ST_CREATE, self.ST_WRITE )
        # set rev nr and check rev props
        self.revNr = self.revNr + 1
        if not revProps.has_key("svn:date"):
            revProps["svn:date"] = self.setRevDate( "" )
        else:
            revProps["svn:date"] = self.setRevDate( revProps["svn:date"] )
        if not revProps.has_key("svn:author"):
            revProps["svn:author"] = ""
        if not revProps.has_key("svn:log"):
            revProps["svn:log"] = ""

        propStr = self.createPropString( revProps )
        # write revision
        self.file.writelines( [ "Revision-number: %d\n" % self.revNr,
                                "Prop-content-length: %d\n" % len(propStr),
                                "Content-length: %d\n" % len(propStr),
                                "\n",
                                propStr,
                                "\n" ] )

        # we have a revision now
        self.state = self.ST_WRITE

    def addNode( self, node ):
        """Add a node to the current revision
                - node: the node to add (class SvnDumpNode)"""

        # check state
        if self.state != self.ST_WRITE:
            raise SvnDumpFileException, "invalid state %d (should be %d)" % \
                        ( self.state, self.ST_WRITE )

        # write the node
        self.file.write( "Node-path: " + node.getPath() + "\n" )
        action = node.getAction()
        if action == "delete":
            # delete needs only the action
            self.file.write( "Node-action: " + action + "\n" )
        else:
            # other actions than delete always have kind and action
            self.file.write( "Node-kind: " + node.getKind() + "\n" )
            self.file.write( "Node-action: " + action + "\n" )
            # copied ?
            if node.getCopyFromRev() != 0:
                self.file.write( "Node-copyfrom-rev: %d\n" % \
                            node.getCopyFromRev() )
                self.file.write( "Node-copyfrom-path: " + \
                            node.getCopyFromPath() + "\n" )
            # calculate length's of properties text and total
            propstr = self.createPropString( node.getProperties() )
            proplen = len( propstr )
            textlen = node.getTextLength()
            if node.hasText():
                totlen = proplen + textlen
            else:
                totlen = proplen
            # write length's of properties text and total
            if proplen > 0:
                self.file.write( "Prop-content-length: %d\n" % proplen )
            if node.hasText():
                self.file.write( "Text-content-length: %d\n" % textlen )
                self.file.write( "Text-content-md5: %s\n" % node.getTextMD5() )
            if proplen > 0 or node.hasText():
                self.file.write( "Content-length: %d\n" % totlen )
            self.file.write( "\n" )
            # write properties
            if proplen > 0:
                self.file.write( propstr )
            # write text
            if node.hasText():
                node.writeToFile( self.file )
                self.file.write( "\n" )
        # CR after each node
        self.file.write( "\n" )


class SvnDumpMerge:
    "a class for merging svn dump files"

    # handle copyfrom-rev !!!

    # output file name
    outFile = ""
    # list additional directories
    outDirs = []
    # log message for directory creating revision
    outMessage = ""
    # author for the additional revision
    outAuthor = "svndumpmerge"

    # variables used for input dump files
    # file names
    inFiles = []
    # path renames [ [ ( from, to ), ... ], ... ]
    inRenames = []
    # mkdir excludes [ {}, ... ]
    inExcludes = []
    # revision number mappings [ {}, ... ]
    inRevNrMaps = []
    # dump files (class SvnDump)
    inDumps = []
    # revision dates of the dumps
    inRevDates = []

    #def __init__( self ):
    #  "no init needed atm"

    def setOutputFile( self, filename, startRev=0 ):
        """Sets the output file name and optional start revision
             - filename (string): name of the output dump file
             - startRev (int, optional): start revision number, default is 0"""

        self.outFile = filename
        self.outStartRev = startRev

    def addInputFile( self, filename ):
        """Adds an input file and returns it's index
            - filename (string): name of a input dump file
            - return (int): index of the input file"""

        index = len( self.inFiles )
        self.inFiles = self.inFiles + [ filename ]
        self.inRenames = self.inRenames + [ [] ]
        self.inExcludes = self.inExcludes + [ {} ]
        self.inRevNrMaps = self.inRevNrMaps + [ {} ]
        return index

    def addRename( self, index, prefixFrom, prefixTo ):
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
        self.inRenames[index] = self.inRenames[index] + \
                                [ (prefixFrom, prefixTo ) ]

    def addMkdirExclude( self, index, dirName ):
        """Adds a mkdir exclude.
             - index (int): index of the dump file
             - dirName (string): name of the directory"""

        # add the mkdir exclude
        self.inExcludes[index][dirName] = None

    def addDirectory( self, dirName ):
        """adds an additional directory"""
        if dirName[0:1] == "/":
            dirName = dirName[1:]
        if dirName[-1:] == "/":
            dirName = dirName[:-1]
        self.outDirs = self.outDirs + [ dirName ]

    def setLogMessage( self, msg ):
        """set log message for additional dirs revision"""
        self.outMessage = msg

    def merge( self ):
        """Executes the merge."""

        # open input dump files
        for inFile in self.inFiles:
            inDump = SvnDump()
            inDump.open( inFile )
            inDump.readNextRev();
            self.inDumps = self.inDumps + [ inDump ]

        # remove empty dumps
        dumpCount = self.removeEmptyDumps()
        if dumpCount == 0:
            return

        # open output file
        self.outDump = SvnDump()
        if self.outStartRev == 0:
            self.outDump.createWithRev0( self.outFile,
                self.inDumps[0].getUUID(), self.inDumps[0].getRevDateStr() )
        else:
            self.outDump.createWithRevN( self.outFile,
                self.inDumps[0].getUUID(), self.outStartRev )

        # skip revision 0 of all dumps
        for inDump in self.inDumps:
            if inDump.getRevNr() == 0:
                inDump.readNextRev()

        # remove empty dumps
        dumpCount = self.removeEmptyDumps()
        if dumpCount == 0:
            self.outDump.close()
            return

        # get revision dates
        oldest = None
        oldestStr = ""
        for index in range(len(self.inDumps)):
            revDat = self.inRevDates + [ self.inDumps[index].getRevDate() ]
            self.inRevDates = revDat
            if oldest == None or revDat < oldest:
                oldest = revDat
                oldestStr = self.inDumps[index].getRevDateStr()

        # add additional directories
        if len(self.outDirs) > 0:
            self.outDump.addRevision( { "svn:log" : self.outMessage,
                                        "svn:author" : self.outAuthor,
                                        "svn:date" : oldestStr } )
            for dirName in self.outDirs:
                node = SvnDumpNode( dirName )
                node.setActionAddDir( None )
                self.outDump.addNode( node )

        # loop over all revisions
        #maxrev = 3
        while dumpCount > 0:
            #print "XYX %d" % maxrev
            #maxrev = maxrev - 1
            #if maxrev == 0:
            #  break
            # find index of the oldest revision
            oldestIndex = 0
            for index in range( 1, dumpCount ):
                if self.inRevDates[index] < self.inRevDates[oldestIndex]:
                    oldestIndex = index
            # copy revision
            self.copyRevision( oldestIndex )
            print "Revision: %d" % self.outDump.getRevNr()
            # read next revision
            srcDump = self.inDumps[oldestIndex]
            if srcDump.readNextRev():
                self.inRevDates[oldestIndex] = srcDump.getRevDate()
            else:
                dumpCount = self.removeEmptyDumps()

        # close output
        print "created %d revisions" % self.outDump.getRevNr()
        self.outDump.close()
            

    def copyRevision( self, dumpIndex ):
        """INTERNAL: don't use !!!
             copies a revision from inDump[dumpIndex] to outDump"""

        srcDump = self.inDumps[dumpIndex]

        # add revision and revprops
        self.outDump.addRevision( srcDump.getRevProps() )

        # add nodes
        index = 0
        nodeCount = srcDump.getNodeCount()
        while index < nodeCount:
            node = srcDump.getNode( index )
            newNode = self.changeNode( dumpIndex, node )
            #self.addParentDirectories( newNode )
            if newNode != None:
                self.outDump.addNode( newNode )
            index = index + 1

        # add revision info
        self.inRevNrMaps[dumpIndex][srcDump.getRevNr()] = \
                    self.outDump.getRevNr()

    def changeNode( self, dumpIndex, node ):
        """INTERNAL: don't use !!!
             creates a new node if the path changed, else returns the old node"""

        path = node.getPath()
        #print "node '%s'" % path
        # mkdir exclude check
        if node.getKind() == "dir" and node.getAction() == "add":
            if path in self.inExcludes[dumpIndex]:
                #print "   --> add dir"
                return None
        fromPath = node.getCopyFromPath()
        fromRev = node.getCopyFromRev()
        change = 0
        newPath = self.renamePath( path, self.inRenames[dumpIndex] )
        newFromPath = fromPath
        newFromRev = fromRev
        if path != newPath:
            change = 1
        if fromRev > 0:
            newFromPath = self.renamePath( fromPath, self.inRenames[dumpIndex] )
            if fromPath != newFromPath:
                change = 1
            newFromRev = self.inRevNrMaps[dumpIndex][fromRev]
            if fromRev != newFromRev:
                change = 1

        if not change:
            # no change needed
            return node

        # do the rename
        newNode = SvnDumpNode( newPath )
        if node.getKind() == "dir":
            # directory
            if node.getAction() == "add":
                newNode.setActionAddDir( node.getProperties(),
                            newFromPath, newFromRev )
            elif node.getAction() == "change":
                newNode.setActionChangeDir( node.getProperties(),
                            newFromPath, newFromRev )
            else:
                newNode.setActionDelete()
        else:
            # file
            if node.getAction() == "add":
                newNode.setActionAddFileNode( node.getProperties(),
                            node, newFromPath, newFromRev )
            elif node.getAction() == "change":
                newNode.setActionChangeFileNode( node.getProperties(),
                            node, newFromPath, newFromRev )
            else:
                newNode.setActionDelete()

        return newNode

    def renamePath( self, path, renames ):
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

    def removeEmptyDumps( self ):
        """INTERNAL: don't use !!!
             removes dump files which reached EOF and returns the count of dumps"""

        index = 0
        while index < len( self.inDumps ):
            inDump = self.inDumps[index]
            if inDump.hasRevision():
                index = index + 1
            else:
                inDump.close()
                eidx = index + 1
                self.inFiles[index:eidx] = []
                self.inRenames[index:eidx] = []
                self.inRevNrMaps[index:eidx] = []
                self.inDumps[index:eidx] = []
                self.inRevDates[index:eidx] = []
        return index


def copyDumpFile( srcfile, dstfile ):
    "copy a dumpfile"

    # SvnDump classes for reading/writing dumps
    srcdmp = SvnDump()
    dstdmp = SvnDump()

    # open source file
    srcdmp.open( srcfile )

    hasrev = srcdmp.readNextRev()
    if hasrev:
        if srcdmp.getRevNr() == 0:
            # create new dump with revision 0
            dstdmp.createWithRev0( dstfile, srcdmp.getUUID(),
                        srcdmp.getRevDateStr() )
            hasrev = srcdmp.readNextRev()
        else:
            # create new dump starting with the same revNr as the original dump
            dstdmp.createWithRevN( dstfile, srcdmp.getUUID(),
                        srcdmp.getRevNr() )
        # now copy all the revisions
        while hasrev:
            dstdmp.addRevisionFromDump( srcdmp )
            hasrev = srcdmp.readNextRev()
    else:
        print "no revisions in the source dump '%s' ???" % srcfile

    # cleanup
    srcdmp.close()
    dstdmp.close()

def parseArgsAndExecute( args ):
    """Parse arguments and execute.
         - args: commandline arguments (without programname)"""

    index = 0
    argCount = len(args)
    if argCount == 0:
        usage()
        return 0
    merge = SvnDumpMerge()
    fileIndex = -1
    outFileSet = 0
    logMsgSet = 0
    while index < argCount:
        if args[index] == "-i":
            # add input file
            i = index + 1
            index = index + 2
            if index > argCount:
                print "missing parameter for option '-i filename'"
                return 1
            fileIndex = merge.addInputFile( args[i] )
        elif args[index] == "-r":
            # add rename
            i = index + 1
            index = index + 3
            if index > argCount:
                print "missing parameter(s) for option '-r from to'"
                return 1
            if fileIndex < 0:
                print "before adding renames a file must be added"
                return 1
            merge.addRename( fileIndex, args[i], args[i+1] )
        elif args[index] == "-x":
            # add exclude mkdir
            i = index + 1
            index = index + 2
            if index > argCount:
                print "missing parameter for option '-x dir'"
                return 1
            if fileIndex < 0:
                print "before adding mkdir excludes a file must be added"
                return 1
            merge.addMkdirExclude( fileIndex, args[i] )
        elif args[index] == "-o":
            # add output file
            i = index + 1
            index = index + 2
            if index > argCount:
                print "missing parameter for option '-o filename'"
                return 1
            if outFileSet:
                print "output file has allready been set"
                return 1
            merge.setOutputFile( args[i] )
            outFileSet = 1
        elif args[index] == "-d":
            # add additional directory
            i = index + 1
            index = index + 2
            if index > argCount:
                print "missing parameter for option '-d dirname'"
                return 1
            merge.addDirectory( args[i] )
        elif args[index] == "-m":
            # set log message for additional dirs revision
            i = index + 1
            index = index + 2
            if index > argCount:
                print "missing parameter for option '-m message'"
                return 1
            if logMsgSet:
                print "log message has allready been set"
                return 1
            merge.setLogMessage( args[i] )
            logMsgSet = 1
        elif args[index] == "-h" or args[index] == "--help":
            # help
            usage()
            return 0
        elif args[index] == "-v" or args[index] == "--version":
            # help
            print __revision__
            return 0
        elif args[index] == "--example":
            # show a usage example
            example()
            return 0
        else:
            # unknown option
            print "unknown option '%s'!" % args[index]
            print "use 'svndumpmerge.py -h' for help."
            return 1
    # now execute the merge
    try:
        merge.merge()
    except:
        print "caught exception while merging"
        # how to output info of the exception ? +++++
        #raise
        return 2
    return 0

def usage():
    "output usage of svndumpmerge.py"

    print ""
    print "usage: svndumpmerge.py [options]"
    print ""
    print "options:"
    print ""
    print "  -i filename      adds an input dump filename."
    print "  -r from to       adds a rename to the previously added file."
    print "                   only leading directory parts can be renamed."
    print "  -o filename      sets the output filename."
    print "  -d dirname       create an additional directory."
    print "  -m message       logmessage for the directory creating revision."
    #print "  -a author        author of the additional revision."
    print "  -v or --version  show this help."
    print "  -h or --help     show this help."
    print "  --example        show a little usage example."
    print ""

def example():
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


if __name__ == '__main__':
    returnCode = parseArgsAndExecute( sys.argv[1:] )
    sys.exit( returnCode )

