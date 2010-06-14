PIDFILE=/var/run/ovdeb.pid

python /home/packaging/ovd-deb/ovdaemon.py &
echo $! > $PIDFILE
