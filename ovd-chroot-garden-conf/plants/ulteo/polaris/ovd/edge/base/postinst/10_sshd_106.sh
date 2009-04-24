#!/bin/sh

PASSWD=/etc/passwd
SSHID=$(grep "^sshd:" $PASSWD | cut -d: -f3)

[ "$SSHID" = "106" ] && exit 0

OWNER=$(egrep "^[1-9a-Z]+:[^:]*:106" $PASSWD | cut -d: -f1)

if [ -n $OWNER ]; then
  sed -ri "s/^($OWNER:[^:]*):106:/\1:$SSHID:/" $PASSWD
fi
sed -ri "s/^(sshd:[^:]*):$SSHID:/\1:106:/" $PASSWD

exit 0
