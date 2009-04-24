#!/bin/sh

echo "Group www-data" >> /etc/cups/cups2all.conf

adduser cupsys www-data
mkdir -p /var/spool/cups2all
chown -R cupsys:www-data /var/spool/cups2all
chmod -R 2770 /var/spool/cups2all

# Don't try to load lp dirvers, we only have a virtual printer
sed -i "s/^LOAD_LP_MODULE.*/LOAD_LP_MODULE=no/" /etc/default/cupsys

CUPSCONF="/etc/cups/cups2all.conf"
sed -i "s/^Umask.*/Umask 027/" $CUPSCONF
sed -i "s/.Group.*/Group www-data/" $CUPSCONF

# restore start-stop-daemon
cp /sbin/start-stop-daemon.garden /sbin/start-stop-daemon
chmod 755 /sbin/start-stop-daemon

# install the printer
mount -t proc none /proc
/etc/init.d/cupsys start
sleep 5 # cups needs time to start
# Make sure than cups2all is usable
chmod a+x /usr/lib/cups/backend/cups2all
lpadmin -p UlteoPrinter -E -v cups2all:/ -m lsb/usr/PostscriptColor.ppd
lpadmin -d UlteoPrinter
/etc/init.d/cupsys stop
umount /proc
chown -R lp /var/spool/cups2all

exit 0
