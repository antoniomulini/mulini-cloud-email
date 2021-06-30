
terraform {
  required_version = ">= 0.13"
  required_providers {
    aws = {
      source = "registry.terraform.io/-/aws"
      version = ">= 2.7.0"
    }
  }

}
