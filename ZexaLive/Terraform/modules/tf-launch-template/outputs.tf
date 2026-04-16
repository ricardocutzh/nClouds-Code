output "amazon_ami" {
  value = data.aws_ami.al2023_specific_release
}

output "launch_template" {
  value = aws_launch_template.server_launch_template
}