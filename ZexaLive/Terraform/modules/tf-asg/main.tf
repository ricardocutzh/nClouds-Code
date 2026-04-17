resource "aws_autoscaling_group" "server_asg" {

  name_prefix = "${var.identifier}-server-asg"

  min_size = var.min_instances
  max_size = var.max_instances

  
  vpc_zone_identifier = var.subnets_ids

#   launch_template {
#     id      = var.launch_template_id
#     version = "$Latest"
#   }

  wait_for_capacity_timeout = "10m"

  dynamic "tag" {
    # Loop over every key-value pair in the map
    for_each = var.tags
    
    # 'content' represents the configuration for a single iteration
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true # Ensures instances get these tags when booting
    }
  }
  
  mixed_instances_policy {
    launch_template {
      launch_template_specification {
        launch_template_id = var.launch_template_id
        version            = var.launch_template_version
      }
      override {
        instance_type = var.instance_type
      }
    }
  }

  # instance_refresh {
  #   strategy = "Rolling"
    
  #   preferences {
  #     # Ensures you don't take down all your servers at once.
  #     # If set to 50, and you have 2 instances, it will replace 1 at a time.
  #     min_healthy_percentage = 50 
      
  #     # Optional: How long to wait before moving to the next instance
  #     # instance_warmup = 300 
  #   }
    
  #   # Optional: You can trigger a refresh if other specific attributes change
  #   triggers = ["mixed_instances_policy"] 
  # }
}