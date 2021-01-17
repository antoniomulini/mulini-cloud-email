# Mailhub server module


# Use our own ALIN2 AMI with pre-installed packages (in particular MailScanner)

data "aws_ami" "mailhub_ami" {
  most_recent = true

  filter {
    name   = "name"
    values = ["mulini-mailhub-ami-*"]
  }

  owners = ["self"]
}

resource "aws_instance" "mailhub" {
  ami                         = data.aws_ami.mailhub_ami.id
  instance_type               = var.instance_type
  subnet_id                   = var.mailhub_subnet_id
  associate_public_ip_address = true
  vpc_security_group_ids = var.mailhub_sg_list
  key_name             = var.mykp
  iam_instance_profile = var.mailhub_instp
  root_block_device {
    volume_type = "gp2"
  }

  user_data = file("${path.module}/mailhub-aws-alin2-user-data")

  tags = {
    Name                 = "mailhub.${var.domain_name}"
    MailstoreMount       = var.main_efs_fqdn
    BackupMailstoreMount = var.backup_efs_fqdn
    Inspector            = "InspectMe"
  }
}