# Create configfiles for various mailhub services.  Values in templates are interpolated, file created and uploaded
# to S3 bucket to be copied by userdata commands during build

### Dovecot config files

resource "aws_s3_bucket_object" "dovecot_ldap_conf" {
  bucket  = "${local.domain_name}-configfiles"
  key     = "dovecot/conf.d/dovecot-ldap.conf.ext"
  content = templatefile("../../configfiles/dovecot/conf.d/dovecot-ldap.conf.ext.tpl", {jumpcloud_org = var.jumpcloud_org})
}

resource "aws_s3_bucket_object" "other_dovecot_configs" {
  bucket  = "${local.domain_name}-configfiles"
  for_each = fileset("../../configfiles/dovecot/conf.d", "{*.conf,*.ext}")
  key = "/dovecot/conf.d/${each.value}"
  source = "../../configfiles/dovecot/conf.d/${each.value}"
}

resource "aws_s3_bucket_object" "dovecot-conf" {
  bucket  = "${local.domain_name}-configfiles"
  key     = "dovecot/dovecot.conf"
  source  = "../../configfiles/dovecot/dovecot.conf"
}

### MailScanner config files

resource "aws_s3_bucket_object" "MailScanner_local_conf" {
  bucket  = "${local.domain_name}-configfiles"
  key     = "MailScanner/conf.d/local.conf"
  content = templatefile("../../configfiles/MailScanner/conf.d/local.conf.tpl", {
    domain_name = local.domain_name
    MS-org-long-name = var.MS-org-long-name
  })
}

resource "aws_s3_bucket_object" "MailScanner_defaults" {
  bucket  = "${local.domain_name}-configfiles"
  key     = "MailScanner/defaults"
  source  = "../../configfiles/MailScanner/defaults"
}

### ClamAV config files

resource "aws_s3_bucket_object" "clamav_scan_conf" {
  bucket  = "${local.domain_name}-configfiles"
  key     = "clamav/scan.conf"
  source  = "../../configfiles/clamav/scan.conf"
}

### Postfix config files

resource "aws_s3_bucket_object" "postfix_ldap_users_cf" {
  bucket  = "${local.domain_name}-configfiles"
  key     = "postfix/ldap-users.cf"
  content = templatefile("../../configfiles/postfix/ldap-users.cf.tpl", {jumpcloud_org = var.jumpcloud_org})
}

resource "aws_s3_bucket_object" "postfix_main_cf" {
  bucket  = "${local.domain_name}-configfiles"
  key     = "postfix/main.cf"
  content = templatefile("../../configfiles/postfix/main.cf.tpl", {domain_name = local.domain_name})
}

resource "aws_s3_bucket_object" "other_postfix_files" {
  bucket  = "${local.domain_name}-configfiles"
  for_each = fileset("../../configfiles/postfix", "{header_checks,master.cf}")
  key = "/postfix/${each.value}"
  source = "../../configfiles/postfix/${each.value}"
}

### Other config files

resource "aws_s3_bucket_object" "other_config_files" {
  bucket  = "${local.domain_name}-configfiles"
  for_each = fileset("../../configfiles", "{*.sh,*.json,${local.domain_name}.aliases}")
  key = "/${each.value}"
  source = "../../configfiles/${each.value}"
}
