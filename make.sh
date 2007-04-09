#!/bin/sh

MAKE_DOC=1
MAKE_PKG=1

if [ -n "$1" ]; then
    MAKE_DOC=0
    MAKE_PKG=0
    while [ -n "$1" ]; do
        case "$1" in
            doc)
                MAKE_DOC=1
                ;;
            pkg)
                MAKE_PKG=1
                ;;
            *)
                echo "unknown command '$1'"
                exit 1
                ;;
        esac
    done
fi

VERSION=`./svndumptool.py --version | awk '/^svndumptool.py/{print $2}'`
if [ -z "$VERSION" ]; then
    echo "Couldn't determine svndumptool's version."
    exit 1
fi

if [ $MAKE_DOC = 1 ]; then
    if [ -d doc ]; then
        rm -rf doc
    fi
    mkdir doc
    epydoc --html -o doc -n "SvnDump $VERSION" svndump
fi

if [ $MAKE_PKG = 1 ]; then
    if [ -d dist ]; then
        rm -rf dist
    fi
    ./setup.py sdist --formats gztar
fi

