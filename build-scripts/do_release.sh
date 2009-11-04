#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Missing version argument"
    exit 1
fi

VERSION=$1
DIR=/home/gauvain/releases/ovd/$VERSION
TMPDIR=$DIR/tmp
PUBLISHDIR=$DIR/publish
TRUNK=$TMPDIR/trunk
TRUNKURI="https://svn.ulteo.com/ovd/trunk"

mkdir -p $PUBLISHDIR $TMPDIR
svn checkout $TRUNKURI $TRUNK

# autotools packages
for module in ApplicationServer SessionManager chroot-apps; do
    cd $TRUNK/$module
    ./autogen.sh
    make
    make distclean
    ./configure
    make distcheck
done

# ant packages
cd $TRUNK/client/java
./bootstrap
ant dist

# Makefile packages
cd $TRUNK/docs
make tarball

mkdir -p $PUBLISHDIR/ulteo-ovd-$VERSION
cp $TRUNK/{ApplicationServer,SessionManager,chroot-apps,docs,client/java}/*-$VERSION.tar.gz \
    $PUBLISHDIR/ulteo-ovd-$VERSION
tar cjf $PUBLISHDIR/ulteo-ovd-$VERSION.tar.bz2 -C $PUBLISHDIR ulteo-ovd-$VERSION

rm -rf $TMPDIR

echo "Tarballs releasead in $PUBLISHDIR"

exit 0
