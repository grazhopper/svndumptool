
SvnDumpTool
===========

SvnDumpTool is a tool for processing Subversion dump files (Subversion is a
version control system available from http://subversion.tigris.org/). It's
written in python (tested with python 2.3.4 on linux).

It has the following commands:

 * diff         show differences between two dump files
 * eolfix       fix EOL of text files in a dump
 * merge        merge dump files

Currently it's homepage is (I hope that it gets included into the main
subversion repository):

  http://queen.borg.ch:81/svn/repos/trunk/svn/svndumptool/




Usage
=====

svndumptool.py command [options] [dumpfiles...]

Only Version 2 dump files can be processed with this tool!
(Version 2 dumps are those created with svn 1.0 or with svn 1.1 without
 the --deltas option)



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
 * None



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
   



Merge
-----

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
 * None



Some tips
=========

While testing with real data i found some weird stuff in these files.

The safest way to convert EOL's is:

1. Do a test conversion (without --dry-run) converting CRLF only and
   gereate a warnings file.

   svndumptool.py  eolfix -Enative -fCRLF -wwarnings.log \
     -mregexp -r '*.txt' input.svndmp output.svndmp

2. Check all files mentioned in warnings.log and decide how to convert
   each of them. Also choose a set default fix options to minimize the
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

