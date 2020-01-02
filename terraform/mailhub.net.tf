#
# Domain name is now taken from Terraform workspace name to ensure separation between test and prod
# i.e. domain = ${terraform.workspace}
# Remember this!

provider "aws" {
	region = "${var.region}"
}


resource "aws_vpc" "vpc_eu1" {
	cidr_block = "10.1.0.0/16"
	tags {
		Name = "vpc_eu1"
	}
}

resource "aws_subnet" "sn_imap_eu1" {
	vpc_id = "${aws_vpc.vpc_eu1.id}"
	cidr_block = "10.1.1.0/24"
	tags {
		Name = "sn_imap_eu1"
	}
}

resource "aws_subnet" "sn_imap_eu2" {
	vpc_id = "${aws_vpc.vpc_eu1.id}"
	cidr_block = "10.1.128.0/24"
	tags {
		Name = "sn_imap_eu2"
	}
}

resource "aws_network_acl" "mailhub_acl" {
  	vpc_id = "${aws_vpc.vpc_eu1.id}"
	subnet_ids = [
		"${aws_subnet.sn_imap_eu1.id}",
		"${aws_subnet.sn_imap_eu2.id}"
	]
  	tags {
		Name = "Mailhub_ACL"
  	}
}

resource "aws_network_acl_rule" "in999" {
	network_acl_id = "${aws_network_acl.mailhub_acl.id}"
  	rule_number    = 999
	egress         = false
  	protocol       = "all"
  	rule_action    = "allow"
  	cidr_block     = "0.0.0.0/0" 
}

resource "aws_network_acl_rule" "out999" {
	network_acl_id = "${aws_network_acl.mailhub_acl.id}"
  	rule_number    = 999
	egress         = true
  	protocol       = "all"
  	rule_action    = "allow"
  	cidr_block     = "0.0.0.0/0"
}

resource "aws_security_group" "default" {
	name = "default"
	description = "default VPC security group"
	
	ingress {
		from_port	= "0"
		to_port		= "0"
		protocol		= "-1"
		self		= "true"
	}
	
	egress {
		from_port	= "0"
		to_port		= "0"
		protocol	= "-1"
		cidr_blocks = ["0.0.0.0/0"]
	}
}

resource "aws_security_group" "sg_internet_to_mailhub" {
	name = "sg_internet_to_mailhub"
	description = "Controls inbound access to mailhub.mulini.org"

	ingress {
		from_port	= "25"
		to_port 	= "25"
		protocol	= "tcp"
		cidr_blocks = ["0.0.0.0/0"]
	}
	
	ingress {
		from_port	= "993"
		to_port		= "993"
		protocol	= "tcp"
		cidr_blocks = ["0.0.0.0/0"]
	}
	
	ingress {
		from_port	= "443"
		to_port		= "443"
		protocol	= "tcp"
		cidr_blocks = ["0.0.0.0/0"]
	}
	
	ingress {
		from_port	= "80"
		to_port		= "80"
		protocol	= "tcp"
		cidr_blocks = ["0.0.0.0/0"]
	}
	
	egress {
		from_port	= "0"
		to_port		= "0"
		protocol	= "-1"
		cidr_blocks = ["0.0.0.0/0"]
	}
}



resource "aws_security_group" "sg_access_from_home1" {
	name = "sg_access_from_home1"
	description = "launch-wizard-1 created 2017-01-16T21:29:17.295+00:00"
	
	ingress {
		from_port	= "993"
		to_port		= "993"
		protocol	= "tcp"
		cidr_blocks	= ["${var.homeip}"]
	}
	
	ingress {
		from_port	= "3389"
		to_port		= "3389"
		protocol	= "tcp"
		cidr_blocks	= ["${var.homeip}"]
	}
	
	ingress {
		from_port	= "25"
		to_port		= "25"
		protocol	= "tcp"
		cidr_blocks	= ["${var.homeip}"]
	}
	
	ingress {
		from_port	= "22"
		to_port		= "22"
		protocol	= "tcp"
		cidr_blocks	= ["${var.homeip}"]
	}
	
	ingress {
		from_port	= "465"
		to_port		= "465"
		protocol	= "tcp"
		cidr_blocks	= ["${var.homeip}"]
	}
	
	egress {
		from_port	= "0"
		to_port		= "0"
		protocol	= "-1"
		cidr_blocks = ["0.0.0.0/0"]
	}
}

# EFS volumes for mail store:
# Main

resource "aws_efs_file_system" "main_efs" {
	encrypted = true
	# Use default EFS key for now
	
	tags {
		Name = "${terraform.workspace}-mailstore-main"
	}
}

resource "aws_efs_mount_target" "main_efs_mount_target1" {
	file_system_id = "${aws_efs_file_system.main_efs.id}"
	subnet_id = "${aws_subnet.sn_imap_eu1.id}"
}

resource "aws_efs_mount_target" "main_efs_mount_target2" {
	file_system_id = "${aws_efs_file_system.main_efs.id}"
	subnet_id = "${aws_subnet.sn_imap_eu2.id}"
}

# Backup

resource "aws_efs_file_system" "backup_efs" {
	encrypted = true
	# Use default EFS key for now
	
	tags {
		Name = "${terraform.workspace}-mailstore-backup"
	}
}

resource "aws_efs_mount_target" "backup_efs_mount_target1" {
	file_system_id = "${aws_efs_file_system.backup_efs.id}"
	subnet_id = "${aws_subnet.sn_imap_eu1.id}"
}

resource "aws_efs_mount_target" "backup_efs_mount_target2" {
	file_system_id = "${aws_efs_file_system.backup_efs.id}"
	subnet_id = "${aws_subnet.sn_imap_eu2.id}"
}

# Use our own CentOS 7 AMI with pre-installed packages (in particular MailScanner)
# instead of the main Centos AMI

output "desc" {
	value = "${data.aws_ami.centos.name}"
}

data "aws_ami" "centos" {
  most_recent      = true

  filter {
    name   = "name"
    values = ["mulini-mailhub-ami-*"]
  }

  owners     = ["self"]
}

# Create mailhub server:

resource "aws_instance" "mailhub" {
	ami = "${data.aws_ami.centos.id}"
	instance_type = "t3.medium"
	subnet_id = "${aws_subnet.sn_imap_eu1.id}"
	associate_public_ip_address = true
	vpc_security_group_ids = [
		"${aws_security_group.sg_access_from_home1.id}",
		"${aws_security_group.sg_internet_to_mailhub.id}",
		"${aws_security_group.default.id}"
	]
	key_name = "${var.mykp}"
	iam_instance_profile = "${var.mailhub_instp}"
	root_block_device {
		volume_type = "gp2"
	}
	
	user_data = "${file("../mulini.generic-aws-centos-user-data")}"
	
	tags {
		Name = "mailhub.${terraform.workspace}"
		MailstoreMount = "${aws_efs_file_system.main_efs.dns_name}"
		BackupMailstoreMount = "${aws_efs_file_system.backup_efs.dns_name}"
		Inspector = "InspectMe"
	}
}