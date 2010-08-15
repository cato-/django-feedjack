#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/home/services/www/de/xenim/planet/pydjango
LOGFILE=/var/log/feedjack/update.log

function run() {
	`dirname $0`/feedjack_update.py --settings=settings
}

if [ -w "`dirname $LOGFILE`" ]; then
	echo "################################################################################" >> $LOGFILE
	echo "### Run at `date`" >> $LOGFILE
	run >> $LOGFILE 2>&1
	echo "### Run finished" >> $LOGFILE
else
	run
fi
