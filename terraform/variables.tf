# variable "domain" {} # Which email domain we are provisioning the server for.  No longer used - now uses Terraform workspace name - remember!

variable "homeip" {} # Home IP address for management access.  Not stored in repo

variable "mailhub_instp" {} # Server Instance Profile/Role.  Not stored in repo

variable "jumpcloud_org" {} # JumpCloud LDAP directory Org. Used in dovecot-ldap.conf.ext and postfix equiv

variable "MS-org-long-name" {} # Mailscanner site info:

variable "mykp" {
	default = "kp_tony_eu1"
}

variable "region" {
  default = "eu-west-1"
}