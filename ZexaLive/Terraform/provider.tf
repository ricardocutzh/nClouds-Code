terraform {

  required_version = "= 1.14.8"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0" 
    }
  }
}

provider "aws" {
  region = local.config.region

  default_tags {
    tags = {
      Environment = terraform.workspace
      ManagedBy   = "Terraform"
    }
  }
}