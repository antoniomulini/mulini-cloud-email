# JumpCloud config
server_host = ldaps://ldap.jumpcloud.com
search_base = ou=Users,o=${jumpcloud_org},dc=jumpcloud,dc=com
version = 3
query_filter = (&(objectclass=person)(mail=%s))
result_attribute = uid
result_format = %s/Maildir/

bind = yes
bind_dn = uid=_svcMailhub,ou=Users,o=${jumpcloud_org},dc=jumpcloud,dc=com
# bind_pw = Moved to Secrets Manager