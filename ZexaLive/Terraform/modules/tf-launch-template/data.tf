data "aws_ami" "al2023_specific_release" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = [var.amazon_linux_2023_ami] 
  }
}