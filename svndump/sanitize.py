#!/usr/bin/env python
#===============================================================================
#
# Copyright (C) 2003 Martin Furter <mf@rola.ch>
# Copyright (C) 2007 CommProve, Inc. (Eli Carter <eli.carter@commprove.com>)
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
import sys
import tempfile
import md5
import random
import string

from svndump import __version
from optparse import OptionParser
from file import SvnDumpFile

options = None

def generate_salthex():
    salt = ''.join(["%02x" % (random.randrange(0,256), ) for x in range(8)])
    return salt

def salthex_to_salt(salthex):
    bytehex = []
    for i in range(0,len(salthex),2):
        bytehex.append(salthex[i:i+2])
    bytes = [chr(string.atoi(h, 16)) for h in bytehex]
    return ''.join(bytes)

def svndump_sanitize_cmdline( appname, args ):
    """
    Parses the commandline and executes the sanitization.

    Usage:

        >>> svndump_sanitize_cmdline( sys.argv[0], sys.argv[1:] )

    @type appname: string
    @param appname: Name of the application (used in help text).
    @type args: list( string )
    @param args: Commandline arguments.
    @rtype: integer
    @return: Return code (0 = OK).
    """

    usage = "usage: %s [options] source destination" % appname
    parser = OptionParser( usage=usage, version="%prog "+__version )
    parser.add_option("-f", "--no-file-data",
        help="Do not sanitize file data.  (Equivalent to --file-data=none.)",
        action="store_const", const="none", dest="file_data_method", default=True)
    parser.add_option("-m", "--file-data",
        help="Method to sanitize file data: whole, line, none.  Default is whole.",
        type="choice", choices=["whole", "line", "none"],
        action="store", dest="file_data_method", default="whole")
    parser.add_option("-n", "--no-filenames",
        help="Do not sanitize filenames",
        action="store_false", dest="filenames", default=True)
    parser.add_option("-e", "--exclude-filename",
        help="Do not sanitize this filename.  May be used multiple times.",
        action="append", dest="filename_excludes", default=None)
    parser.add_option("-u", "--no-usernames",
        help="Do not sanitize usernames",
        action="store_false", dest="usernames", default=True)
    parser.add_option("-l", "--no-logs",
        help="Do not sanitize log messages",
        action="store_false", dest="logs", default=True)
    random_salt = ''.join(["%02x" % (random.randrange(0,256), ) for x in range(8)])
    parser.add_option("-s", "--salt",
        help="Specify the salt to use in hex",
        dest="salt", default=random_salt)

    global options
    (options, args) = parser.parse_args( args )

    if len( args ) != 2:
        print "specify exactly one source and one destination dumpfile."
        return 1

    global sanitize_salt
    sanitize_salt = salthex_to_salt(options.salt)

    sanitize_dump_file( args[0], args[1] )
    return 0

sanitized_authors = []
def sanitize_rev_props( rev_props ):
    for k in rev_props.iterkeys():
        if options.logs and k == 'svn:log':
            rev_props['svn:log'] = hash(rev_props['svn:log'])
        elif options.usernames and k == 'svn:author':
            author = rev_props['svn:author']
            try:
                i = sanitized_authors.index(author)
            except ValueError:
                i = len(sanitized_authors)
                sanitized_authors.append(author)
            rev_props['svn:author'] = "author%s" % (i, )
        elif k == 'svn:date':
            pass # leave this for now.
        else:
            print "Couldn't sanitize %s: \"%s\"" % (k, rev_props[k])
    return rev_props

# Sanitize the data using a salted md5sum
def hash( data ):
    return md5.new(sanitize_salt+data).hexdigest()

def sanitize_path( path ):
    parts = path.split('/')
    sparts = []
    for part in parts:
        if part in options.filename_excludes:
            spart = part
        else:
            spart = hash(part)
        sparts.append(spart)
    spath = '/'.join(sparts)
    return spath

def sanitize_node( node ):
    if options.file_data_method != "none" and node.has_text():
        # Write the original data to a temp file
        (fd, origname) = tempfile.mkstemp(prefix="svndumptool")
        origdatafile = os.fdopen(fd, "wb+")
        node.write_text_to_file(origdatafile)
        origdatafile.seek(0)
        # New data tempfile
        (fd, newname) = tempfile.mkstemp(prefix="svndumptool")
        newdatafile = os.fdopen(fd, "wb+")
        if options.file_data_method == "whole":
            # Calculate the salted md5sum
            md5sum = md5.new()
            md5sum.update(sanitize_salt)
            while True:
                data = origdatafile.read(1024**2)
                if not len(data):
                    break
                md5sum.update(data)
            # Write the sanitized data to another temp file.
            newdatafile.write("%s\n" % md5sum.hexdigest())
        elif options.file_data_method == "line":
            # Write the sanitized data to another temp file.
            newdatafile.writelines(["%s\n" % hash(line) for line in origdatafile.readlines()])
        else:
            assert False, "options.file_data_method has impossible value \"%s\"" % (options.file_data_method, )
        # clean up new tempfile handle
        newdatafile.close()
        # clean up the original tempfile
        origdatafile.close()
        os.remove(origname)
        # Set the new content.
        node.set_text_file(newname, delete=True)

    if options.filenames and node.get_path():
        node.set_path(sanitize_path(node.get_path()))
    if options.filenames and node.has_copy_from():
        path = node.get_copy_from_path()
        rev = node.get_copy_from_rev()
        path = sanitize_path(path)
        node.set_copy_from(path, rev)
    # TODO: Properties?
    return node

def sanitize_dump_file( srcfile, dstfile ):
    print "Using salt %s" % (options.salt,)
    # SvnDumpFile classes for reading/writing dumps
    srcdmp = SvnDumpFile()
    dstdmp = SvnDumpFile()

    # open source file
    srcdmp.open( srcfile )

    hasrev = srcdmp.read_next_rev()
    if hasrev:
        # create the dumpfile
        dstdmp.create_like( dstfile, srcdmp )
        # now copy all the revisions
        while hasrev:
            rev_props = srcdmp.get_rev_props()
            #print rev_props # DEBUG
            rev_props = sanitize_rev_props(rev_props)
            dstdmp.add_rev(rev_props)
            for node in srcdmp.get_nodes_iter():
                node = sanitize_node(node)
                dstdmp.add_node(node)

            # Next revision
            hasrev = srcdmp.read_next_rev()
    else:
        print "no revisions in the source dump '%s' ???" % srcfile

    # cleanup
    srcdmp.close()
    dstdmp.close()

