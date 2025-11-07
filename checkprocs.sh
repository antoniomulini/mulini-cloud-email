#!/bin/bash

systemctl show dovecot mailscanner postfix opendkim clamd@scan -p "ActiveState,StatusErrno,Result"