PIDFILE=/var/run/ovdeb.pid
DAEMONDIR=$1

ssh-add
python $DAEMONDIR/ovdaemon.py &
echo $! > $PIDFILE
