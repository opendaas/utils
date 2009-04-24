#!/bin/sh

echo "" >>/etc/bash.bashrc
echo "# disable file locking for ooo" >>/etc/bash.bashrc
echo "SAL_ENABLE_FILE_LOCKING=0" >>/etc/bash.bashrc

exit 0

