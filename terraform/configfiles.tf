# Create configfiles for various mailhub services.  Values in templates are interpolated, file created and uploaded
# to S3 bucket to be copied by userdata commands during build

data "template_file" "dovecot_ldap_conf" {
    template = "${file("../configfiles/dovecot/conf.d/dovecot-ldap.conf.ext.tpl")}"
    vars = {
        jumpcloud_org = "${var.jumpcloud_org}"
    }
}

resource "aws_s3_bucket_object" "dovecot_ldap_conf" {
    bucket = "${local.domain_name}-configfiles"
    key = "dovecot/conf.d/dovecot-ldap.conf.ext"
    content = "${data.template_file.dovecot_ldap_conf.rendered}"
}

