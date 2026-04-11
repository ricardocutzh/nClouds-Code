terraform {
  backend "s3" {
    bucket         = "zexialive-098072157095-us-east-1-livego-poc-tf-backend"
    key            = "poc/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "zexialive-098072157095-us-east-1-livego-poc-tf-backend"
  }
}