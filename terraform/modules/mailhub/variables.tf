variable "instance_type" {
    description = "Instance type for mailhub server"
    type = string
    default = "t4g.medium"
}

variable "domain_name" {
    description = "TLD name for mailhub server"
    type = string
}

variable "mailhub_subnet_id" {
    description = "Subnet ID for mailhub server"
    type = string
}

variable "mailhub_sg_list" {
    description = "List of Security Group ids to apply to mailhub"
    type = list(string)
}

variable "mykp" {
    description = "SSH key pair name for mailhub"
    type = string
}

variable "mailhub_instp" {
    description = "Instance Profile to be attached to mailhub"
    type = string
}

variable "main_efs_fqdn" {
    description = "FQDN of EFS mount for mailboxes"
    type = string
}

variable "backup_efs_fqdn" {
    description = "FQDN of EFS mount for mailbox backups"
    type = string
}