#!/bin/sh

APTCMD="apt-get --no-upgrade \
                --no-remove \
                --allow-unauthenticated \
                --force-yes \
                -y install"

$APTCMD language-pack-kde-fr
$APTCMD language-pack-kde-fr-base
$APTCMD language-pack-fr
$APTCMD language-support-fr

locale-gen

exit 0
