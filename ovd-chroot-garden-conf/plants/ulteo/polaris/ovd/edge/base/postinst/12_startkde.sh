#!/bin/sh

sed -i "s/^Port.*/Port 110\nPort 443\nPort 993\nPort 995\n/" \
	/etc/ssh/sshd_config

exit 0

