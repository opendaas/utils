#!/bin/sh

cat > /etc/apt/sources.list << EOF
# Ubuntu repositories
deb http://archive.ubuntu.com/ubuntu hardy main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu hardy-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu hardy-security main restricted universe multiverse

# Ulteo repositories
deb http://archive.ulteo.com/ulteo/common polaris main restricted
deb http://archive.ulteo.com/ulteo/ovd ovd-polaris main

EOF

exit 0
