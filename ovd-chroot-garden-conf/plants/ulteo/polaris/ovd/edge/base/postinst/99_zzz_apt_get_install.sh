#|/bin/sh
exit 0 
#cd /tmp
#export DEBIAN_FRONTEND=noninteractive
#export DEBIAN_PRIORITY=critical
#export DEBCONF_NONINTERACTIVE_SEEN=true

#if wget http://fire.ulteo.com/~nomed/germinate-smart/installable.sort;then
#	pkgs=$(cat installable.sort | awk '{print $1}')
#	for p in $pkgs;do
#		 apt-get --no-upgrade --no-remove \
#		         --allow-unauthenticated --force-yes -y install $i
#	done
#fi
#for p in apache postgres mysql app-install-data libsane; do
#	apt-get remove --force-yes -y --purge $p*
#done

#for p in ppp;do
#	apt-get remove --force-yes -y --purge $p
#done
