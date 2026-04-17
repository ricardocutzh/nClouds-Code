resource "aws_launch_template" "server_launch_template" {
  name          = "${var.identifier}-server"
  image_id      = data.aws_ami.al2023_specific_release.image_id
  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = var.volume_size
      volume_type           = var.volume_type
      delete_on_termination = true  
    }
  }

  user_data = base64encode("#cloud-config\n${yamlencode(var.user_data)}")

  iam_instance_profile {
    name = var.instance_profile
  }

  vpc_security_group_ids = var.security_group_ids

  monitoring {
    enabled = var.monitoring_enabled
  }

  tags = var.tags
}
