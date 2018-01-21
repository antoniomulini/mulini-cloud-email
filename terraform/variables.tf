variable "domain" {} # Which email domain we are provisioning the server for

variable "homeip" {} # Home IP address for management access.  Not stored in repo

variable "mailhub_instp" {} # Server Instance Profile/Role.  Not stored in repo

variable "mykp" {
	default = "kp_tony_eu1"
}

variable "region" {
  default = "eu-west-1"
}