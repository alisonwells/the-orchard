provider "aws" {
  region = "eu-west-1"
  version = "~> 2.34"
}

terraform {
  backend "s3" {
    bucket         = "leafy-cider-terraform-state"
    key            = "restaurant"
    region         = "eu-west-1"
  }
}
