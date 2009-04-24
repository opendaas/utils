#!/bin/sh
exit 0

#!/usr/bin/python

FILE = "/root/vulteo/etc/ulteo-sessions"

f = open(FILE, "w")
for i in range(10, 21):
	f.write("%d\n" % i)
f.close()

