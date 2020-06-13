# JumpCloud SaaS LDAP directory service configuration for Dovecot

uris = ldaps://ldap.jumpcloud.com 
base = ou=Users,o=${jumpcloud_org},dc=jumpcloud,dc=com
auth_bind_userdn = uid=%u,ou=Users,o=${jumpcloud_org},dc=jumpcloud,dc=com
auth_bind = yes
