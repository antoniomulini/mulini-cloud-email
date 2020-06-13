# MailScanner config file for mailhub

%org-name% = ${domain_name}
%org-long-name% = ${MS-org-long-name}
%web-site% = www.${domain_name}
Run As User = postfix
Run As Group = postfix
Incoming Queue Dir = /var/spool/postfix/hold
Outgoing Queue Dir = /var/spool/postfix/incoming
MTA = postfix
Incoming Work Group = clamscan
Incoming Work Permissions = 0640
Virus Scanners = clamd
Clamd Socket = /var/run/clamd.scan/clamd.sock
Use SpamAssassin = yes
SpamAssassin User State Dir = /var/spool/MailScanner/spamassassin

Spam Actions = store notify

# MailScanner's default of adding sig to scanned email breaks DKIM:
Sign Clean Messages = no
