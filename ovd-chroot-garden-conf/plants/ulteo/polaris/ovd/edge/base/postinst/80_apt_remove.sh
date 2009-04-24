#!/bin/sh
#DISABLED
exit 0
# remove some packages
PACKAGES="at"

apt-get remove --force-yes -y --purge $PACKAGES

exit 0

