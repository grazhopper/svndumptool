#!/usr/bin/env python
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

import os
import os.path
import zlib

import svndump
from svndump.node import SvnDumpNode
from svndump.file import SvnDumpFile

def run( cmd ):
    print "cmd <%s>" % cmd
    rc = os.system( cmd )
    print "rc: %d" % rc
    return rc

def kill_dir( dir ):
    """'rm -rf dir' in python ;-)"""
    if os.path.isdir( dir ):
        for d in os.listdir( dir ):
            d = dir + "/" + d
            if os.path.isdir( d ):
                kill_dir( d )
            else:
                os.remove( d )
        os.rmdir( dir )

def create_text( type, fileid, revnr ):
    """Create some test text."""

    lines = "line A\nline B\nline C\nline D\nline E\n"
    filerevtxt = "file %s rev %d\n" % ( fileid, revnr )
    text = lines * 3 + filerevtxt + lines * 3
    if type == "binary":
        print "gzip !?!?!"
        text = zlib.compress( text )
    elif type == "broken-eol":
        text = text.replace( "B\n", "B\r\n" )
        text = text.replace( "D\n", "D\r" )
    return text

def svn_create_dump_file( filename, fileid, data, reposdir, wcdir ):
    """Creates a svn dump file using the svn commandline."""

    # cleanup first
    kill_dir( reposdir )
    kill_dir( wcdir )

    # create repos
    run( "svnadmin create '%s'" % reposdir )

    # create wc
    run( "svn co 'file://%s' '%s'" % ( reposdir, wcdir ) )

    # now do the work
    nrev = len(data)
    irev = 1
    revnr = 0
    while irev < nrev:
        rev = data[irev]
        irev = irev + 1
        revnr = revnr + 1
        if rev.has_key( "" ):
            author = rev["author"]
        else:
            author = "t%d" % revnr
        if rev.has_key( "log" ):
            log = rev["log"]
        else:
            log = "log for file '%s' rev %d" % ( fileid, revnr )
        nodes = rev["nodes"]
        nnode = len(nodes)
        inode = 0
        while inode < nnode:
            nodedata = nodes[inode]
            inode = inode + 1
            action = nodedata["action"]
            kind = nodedata["kind"]
            path = nodedata["path"]
            nodefile = "%s/%s" % ( wcdir, path )
            if action == "delete":
                run( "svn rm '%s'" % nodefile )
            elif kind == "dir" and action == "add":
                run( "svn mkdir '%s/%s'" % ( wcdir, path ) )
            elif kind == "file" and nodedata.has_key( "text" ):
                text = create_text( nodedata["text"], fileid, revnr )
                fileobj = open( nodefile, "wb" )
                fileobj.write( text )
                fileobj.close()
                if action == "add":
                    run( "svn add '%s'" % nodefile )
            if nodedata.has_key( "props" ):
                props = nodedata["props"]
                print props
                for name, value in props.items():
                    if value == None:
                        run( "svn pd '%s' '%s'" % ( name, nodefile ) )
                    else:
                        run( "svn ps '%s' '%s' '%s'" % \
                                    ( name, value, nodefile ) )
        run( "svn ci --username '%s' -m '%s' '%s'" % ( author, log, wcdir ) )

    # dump the repos
    run( "svnadmin dump '%s' > '%s'" % ( reposdir, filename ) )

def py_create_dump_file( filename, fileid, data, tmpdir ):
    """Creates a svn dump file using the python classes."""

    lines = "line A\nline B\nline C\nline D\nline E\n"

    dump = SvnDumpFile()

    rev = data[0]
    revnr = rev["nr"]
    if revnr == 0:
        dump.create_with_rev_0( filename, rev["uuid"], rev["date"] )
    else:
        dump.create_with_rev_n( filename, rev["uuid"], revnr )
        revnr = revnr - 1
    nodeprops = {}
    nrev = len(data)
    irev = 1
    while irev < nrev:
        rev = data[irev]
        irev = irev + 1
        revnr = revnr + 1
        revprops = {}
        revprops["svn:date"] = rev["date"]
        if rev.has_key( "author" ):
            revprops["svn:author"] = rev["author"]
        else:
            revprops["svn:author"] = "t%d" % revnr
        if rev.has_key( "log" ):
            revprops["svn:log"] = rev["log"]
        else:
            revprops["svn:log"] = "log for file '%s' rev %d" % \
                                ( fileid, revnr )
        dump.add_rev( revprops )
        nodes = rev["nodes"]
        nnode = len(nodes)
        inode = 0
        while inode < nnode:
            # +++++ change handling of properties !!!
            nodedata = nodes[inode]
            inode = inode + 1
            action = nodedata["action"]
            kind = nodedata["kind"]
            path = nodedata["path"]
            node = SvnDumpNode( kind, path )
            node.set_action( action )
            if nodedata.has_key( "copyfrom" ):
                copyfrom = nodedata["copyfrom"]
                node.set_copy_from( copyfrom[0], copyfrom[1] )
            if nodedata.has_key( "text" ):
                textfile = "%s/text-%d" % ( tmpdir, inode )
                filerevtxt = "file %s rev %d\n" % ( fileid, revnr )
                text = lines * 3 + filerevtxt + lines * 3
                if nodedata["text"] == "binary":
                    print "gzip !?!?!"
                    text = zlib.compress( text )
                elif nodedata["text"] == "broken-eol":
                    text = text.replace( "B\n", "B\r\n" )
                    text = text.replace( "D\n", "D\r" )
                fileobj = open( textfile, "wb" )
                fileobj.write( text )
                fileobj.close()
                node.set_text_file( textfile )
            if action == "delete":
                del nodeprops[path]
            elif action == "add":
                if nodedata.has_key("props"):
                    props = nodedata["props"]
                else:
                    props = {}
                node.set_properties( props )
                nodeprops[path] = props
            elif nodedata.has_key("props"):
                for name, value in nodedata["props"].items():
                    if value == None:
                        del nodeprops[path][name]
                    else:
                        nodeprops[path][name] = value
                node.set_properties( nodeprops[path] )
            dump.add_node( node )
    dump.close()

data_test1 = [
    {
        "nr":       0,
        "uuid":     "70e73ab9-a1e8-0310-b250-e777cff18a12",
        "date":     "2004-01-01T10:00:00.000000Z"
    },
    {
        "date":     "2004-01-01T12:00:00.000000Z",
        "nodes":    [
            # create a few dirs
            {
                "path":     "testdir1",
                "kind":     "dir",
                "action":   "add",
                "props":    {
                    "svn:ignore":   "*.tmp"
                }
            },
            {
                "path":     "testdir2",
                "kind":     "dir",
                "action":   "add",
                "props":    {
                    "svn:ignore":   "*.tmp",
                    "broken":       "false"
                }
            },
            {
                "path":     "testdir4",
                "kind":     "dir",
                "action":   "add"
            },
            {
                "path":     "testdir3",
                "kind":     "dir",
                "action":   "add"
            },
            # add some files to testdir1
            {
                "path":     "testdir1/ok1.txt",
                "kind":     "file",
                "action":   "add",
                "text":     "text",
                "props":    {
                    "broken":       "false",
                    "ok":           "true",
                    "test":         "true"
                }
            },
            {
                "path":     "testdir1/ok2.txt",
                "kind":     "file",
                "action":   "add",
                "text":     "text"
            },
            {
                "path":     "testdir1/ok3.txt",
                "kind":     "file",
                "action":   "add",
                "text":     "text",
                "props":    {
                    "broken":       "false",
                    "ok":           "true",
                    "test":         "true"
                }
            },
            {
                "path":     "testdir1/broken1.txt",
                "kind":     "file",
                "action":   "add",
                "text":     "broken-eol"
            },
            {
                "path":     "testdir1/broken2.txt",
                "kind":     "file",
                "action":   "add",
                "text":     "broken-eol",
                "props":    {
                    "broken":       "true",
                    "test":         "true"
                }
            }
        ]
    },
    {
        "date":     "2004-01-02T12:00:00.000000Z",
        "nodes":    [
            # change text
            {
                "path":     "testdir1/ok1.txt",
                "kind":     "file",
                "action":   "change",
                "text":     "text"
            }
        ]
    },
    {
        "date":     "2004-01-03T12:00:00.000000Z",
        "nodes":    [
            # add property
            {
                "path":     "testdir1/ok2.txt",
                "kind":     "file",
                "action":   "change",
                "props":    {
                    "broken":       "false"
                }
            }
        ]
    },
    {
        "date":     "2004-01-04T12:00:00.000000Z",
        "nodes":    [
            # change text
            {
                "path":     "testdir1/broken1.txt",
                "kind":     "file",
                "action":   "change",
                "text":     "broken-eol"
            }
        ]
    },
    {
        "date":     "2004-01-05T12:00:00.000000Z",
        "nodes":    [
            # remove property
            {
                "path":     "testdir1/ok3.txt",
                "kind":     "file",
                "action":   "change",
                "props":    {
                    "broken":       None
                }
            },
            {
                "path":     "testdir1/broken2.txt",
                "kind":     "file",
                "action":   "change",
                "props":    {
                    "broken":       None
                }
            }
        ]
    }
]

def write_test_file( tmpdir ):
    """Just testing py_create_dump_file."""
    filename = tmpdir + "/test.svndmp"
    py_create_dump_file( filename, data, tmpdir )

if __name__ == '__main__':
    tempdir = os.path.abspath( "testtmp" )
    tempfiles = tempdir + "/files"
    temprepos = tempdir + "/repos"
    tempwc = tempdir + "/wc"
    if not os.path.isdir( tempdir ):
        os.mkdir( tempdir )
    if not os.path.isdir( tempfiles ):
        os.mkdir( tempfiles )
    #write_test_file( tmpfiles )
    svndmp = tempdir + "/testdump1svn"
    pydmp = tempdir + "/testdump1py"
    #svn_create_dump_file( svndmp, "test1", data_test1, temprepos, tempwc )
    py_create_dump_file( pydmp, "test1", data_test1, tempfiles )
    svndump.copy_dump_file( svndmp, pydmp + "2" )

# def svn_create_dump_file( filename, fileid, reposdir, wcdir, data ):
#  def py_create_dump_file( filename, fileid, data, tmpdir ):
