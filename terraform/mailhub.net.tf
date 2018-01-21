

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

# Get latest CentOS AMI to build from

output "desc" {
	value = "${data.aws_ami.centos.description}"
}

data "aws_ami" "centos" {
  most_recent      = true

  filter {
    name   = "name"
    values = ["CentOS Linux 7 x86_64 HVM EBS*"]
  }

  owners     = ["679593333241"]
}

# Create mailhub server:

resource "aws_instance" "mailhub" {
	ami = "${data.aws_ami.centos.id}"
	instance_type = "t2.small"
	subnet_id = "${aws_subnet.sn_imap_eu1.id}"
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
	tags {
		Name = "mailhub.${var.domain}"
	}
}