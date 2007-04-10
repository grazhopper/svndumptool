
SvnDumpTool
===========

SvnDumpTool is a tool for processing Subversion dump files (Subversion is a
version control system available from http://subversion.tigris.org/). It's
written in python (tested with python 2.4.4 on linux, though 2.3 should
work fine too).

It has the following commands:

 * check                check a dumpfile
 * copy                 copy a dumpfile
 * cvs2svnfix           fix a cvs2svn created dumpfile
 * diff                 show differences between two dump files
 * eolfix               fix EOL of text files in a dump
 * export               export files from a dumpfile
 * join                 join dumpfiles
 * log                  show the log of a dumpfile
 * ls                   list files of a given revision
 * merge                merge dump files
 * sanitize             sanitize dump files
 * split                split dump files
 * transform-revprop    transform a revision property
 * transform-prop       transform a node property


It's homepage is:

  http://svn.borg.ch/svndumptool/



Installing
==========

Unpack the tarball, cd into the directory and run the following command:

./setup.py install



Usage
=====

svndumptool.py command [options] [dumpfiles...]

Only Version 2 dump files can be processed with this tool!
(Version 2 dumps are those created without the --deltas option)



Check
-----

Checks a dumpfile.

svndumptool.py check [options] dumpfiles...

options:
  --version            show program's version number and exit
  -h, --help           show this help message and exit
  -a, --check-actions  check actions like add/change/delete
  -d, --check-dates    check that svn:date increases
  -m, --check-md5      check md5 sums of the files
  -A, --all-checks     do all checks

Known bugs:
 * cvs2svn created dumps may cause false negatives.



Copy
----

Copies a dump file. Doesn't sound like that makes sense but it's a useful
test of svndump classes (and sometimes it's able to fix broken dump files).

svndumptool.py copy [options] source destination

options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit

Known bugs:
 * None



Cvs2svnfix
----------

Fixes a cvs2svn created dumpfile. Some (all?) versions of cvs2svn do not
create 100% valid dumpfiles according to subversions specification of the
dumpfile format. It omits the node kind for copied nodes. This command
repairs those nodes.

svndumptool.py cvs2svnfix [options] inputfile outputfile

options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit

Known bugs:
 * None



Diff
----

Shows differences between two subversion dump files.

svndumptool.py diff [options] dumpfile1 dumpfile2

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -e, --check-eol       check for EOL differences
  -q, --quiet           quiet output
  -v, --verbose         verbose output
  -IIGNORES, --ignore=IGNORES
                        Ignore types of differences. This option can be
                        specified more than once. Valid types are 'UUID',
                        'RevNr', 'RevDate', 'RevDateStr', 'NodeCount', 'Path',
                        'Action', 'Kind', 'CopyFromPath', 'CopyFromRev',
                        'HasText', 'TextLen', 'TextMD5', 'EOL', 'Text',
                        'PropDiff', 'PropMissing', 'RevPropDiff' and
                        'RevPropMissing'
  --ignore-revprop=IGNOREREVPROP
                        ignore a differing/missing revision property
  --ignore-property=IGNOREPROPERTY
                        ignore a differing/missing property

Known bugs:
 * cvs2svn created dumps may cause false negatives.



Eolfix
------

Textfiles normally contain only one kind of 'end-of-line' characters
(LF, CRLF or CR). This command fixes the EOL's in text files, it converts
all EOL's to LF.

svndumptool.py eolfix [options] sourcedump destinationdump

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -EEOLSTYLE, --eol-style=EOLSTYLE
                        add svn:eol-style property to text files, the value can
                        be 'native', 'LF', 'CRLF' or 'CR'
  -fFIX, --fix=FIX      a comma separated list of what (and how) to fix, can be
                        a combination of 'CRLF', 'CR' and 'RemCR'. If 'CR' and
                        'RemCR' both specified 'RemCR' is ignored. 'CRLF' and
                        'CR' mean replace them by LF, 'RemCR' means remove
                        CR's.
  -FFIXREVPATH, --fix-rev-path=FIXREVPATH
                        a colon separated list of fix option, revision number
                        and path of a file.
  -mMODE, --mode=MODE   text file detection mode: one of 'prop' [default],
                        'regexp'
  -rREGEXP, --regexp=REGEXP
                        regexp for matching text file names
  -tTMPDIR, --temp-dir=TMPDIR
                        directory for temporary files.
  -wWARNFILE, --warn-file=WARNFILE
                        file for storing the warnings.
  --dry-run             just show what would be done but don't do it

Known bugs:
 * EOL's aren't fixed in a file which was copied and the old file was not a
   text file.
 * Produces temp files in the current directory (named tmpnodeN).
 * Diff shows a few Text changes after eolfix !?!
   


Export
------

Exports files from a dumpfile.

svndumptool.py export [options] dumpfile

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -e REV REPOSPATH FILENAME, --export= REV REPOSPATH FILENAME
                        adds a file to export.
  -dDIR, --directory=DIR
                        set the directory for the exported files.

Known bugs:
 * None



Join
----

Concatenates two or more dumpfiles.

svndumptool.py join -o outputfile dumpfiles...

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -o OUTFILE, --output-file=OUTFILE
                        set the name of the output dumpfile.

Known bugs:
 * None



Log
---

Shows the log of a dumpfile in (almost) the same format as "svn log".

svndumptool.py log [options] dumpfiles...

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -r REVISION, --revision=REVISION
                        revision number or range (X:Y)
  -v, --verbose         verbose output

Known bugs:
 * None



Ls
--

Lists all files and dirs in the given revision or HEAD.

svndumptool.py ls [options] dumpfiles...

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -r REVNR, --revision=REVNR
                        revision number

Known bugs:
 * None



Merge
-----

Merges multiple dumpfiles into one. It does this by reading all dumpfiles
at the same time and always adding the revision with the oldest revision
date to the output dumpfile.
Use 'svndumptool.py check -a -d dumpfile' to check that actions and dates
in the merged file make sense.

svndumptool.py merge [options]

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -iINFILE, --input-file=INFILE
                        adds an input dump filename.
  -r FROM TO, --rename= FROM TO
                        adds a rename to the previously added file.
  -xDIR, --mkdir-exclude=DIR
                        exclude mkdir from the previously added file.
  -oOUTFILE, --output-file=OUTFILE
                        sets the output filename.
  -dDIR, --mkdir=DIR    create an additional directory.
  -mMSG, --message=MSG  logmessage for the directory creating revision.
  --example             show a little usage example.

Known bugs:
 * There's no warning when a dumpfile does not have monotonic increasing
   revision dates. Use 'svndumptool.py check -d dumpfile' to check the
   revision dates of a dumpfile.
 * mkdir-exclude may fail in some cases in cvs2svn created dumps.



Sanitize
--------

Replaces data and/or metadata of a dumpfile with md5 hashes.

svndumptool.py sanitize [options] source destination

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -f, --no-file-data    Do not sanitize file data.  (Equivalent to --file-
                        data=none.)
  -m FILE_DATA_METHOD, --file-data=FILE_DATA_METHOD
                        Method to sanitize file data: whole, line, none.
                        Default is whole.
  -n, --no-filenames    Do not sanitize filenames
  -e FILENAME_EXCLUDES, --exclude-filename=FILENAME_EXCLUDES
                        Do not sanitize this filename.  May be used multiple
                        times.
  -u, --no-usernames    Do not sanitize usernames
  -l, --no-logs         Do not sanitize log messages
  -s SALT, --salt=SALT  Specify the salt to use in hex

Known bugs:
 * None



Split
-----

Splits a dumpfile into multiple smaller dumpfiles.

svndumptool.py split inputfile [startrev endrev filename]...

options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit

Known bugs:
 * None



Transform-revprop
-----------------

Transforms a revision property using a regular expression and a
replacement string.

svndumptool.py transform-revprop propname regex replace source destination

options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit

Known bugs:
 * None



Transform-prop
--------------

Transforms a property using a regular expression and a replacement string.

svndumptool.py transform-prop propname regex replace source destination

options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit

Known bugs:
 * None




Some tips
=========

While testing with real data i found some weird stuff in these files.

The safest way to convert EOL's is:

1. Do a test conversion (without --dry-run) converting CRLF only and
   generate a warnings file.

   svndumptool.py  eolfix -Enative -fCRLF -wwarnings.log \
     -mregexp -r '*.txt' input.svndmp output.svndmp

2. Check all files mentioned in warnings.log and decide how to convert
   each of them. Also choose a set of default fix options to minimize the
   list of special fix options.
   Maybe it's possible to choose a better set of regular expressions.

2.1 Binary files: set empty fix option for that rev/file pair.

   svndumptool.py ... -F :12:binary_file.txt ...

2.2 Textfiles containing CR EOL's: convert these

   svndumptool.py ... -F CRLF,CR:12:cr_file.txt ...

2.3 Textfiles containing CR which aren't EOL's: remove these

   svndumptool.py ... -F CRLF,RemCR:12:weird_file.txt ...

3. Do the real conversion.

4. Use 'svndumptool.py diff [options] input.svndmp output.svndmp' to
   compare the dump files. svnadmin load will do another check.



Python classes
==============

The python classes are documented using epydoc
(http://epydoc.sourceforge.net/).
To generate the HTML docs just enter the followin commands:

   mkdir doc
   epydoc --html -o doc -n "SvnDump 0.4.0" svndump

