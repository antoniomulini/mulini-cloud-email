variable "domain" {} # Which email domain we are provisioning the server for

variable "homeip" {} # Home IP address for management access.  Not stored in repo

variable "region" {
  default = "eu-west-1"
}