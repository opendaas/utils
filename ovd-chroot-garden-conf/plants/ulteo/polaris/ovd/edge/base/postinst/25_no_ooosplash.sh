#!/bin/sh

FILE="/usr/lib/openoffice/program/oosplash.bin"

# set oossplash.bin -x to avoid a fork which makes soffice end to soon, and
# thus close the od session
dpkg-statoverride --add root root 0644 $FILE
chmod 0644 $FILE

exit 0
