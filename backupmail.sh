#!/bin/bash

LOGFILE="/var/log/backupmail";
SOURCEDIR="/home/vmail";
DESTDIR="/mail-backup";

echo "`/bin/date` Backing up from ${SOURCEDIR} to ${DESTDIR}..." >> $LOGFILE;

rsync -rva --delete ${SOURCEDIR}/ ${DESTDIR} >> $LOGFILE 2>&1;

echo "`/bin/date` <---------------Finished----------------->" >> $LOGFILE;
