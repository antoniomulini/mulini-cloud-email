
terraform {
  required_version = ">= 0.13"
  required_providers {
    archive = {
      source = "hashicorp/archive"
    }
    aws = {
      source = "registry.terraform.io/-/aws"
      version = ">= 2.7.0"
    }
    template = {
      source = "hashicorp/template"
    }
  }
}
