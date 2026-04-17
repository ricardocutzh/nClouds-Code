module "hls_bucket" {
  source = "./modules/tf-s3-hls"

  identifier                  = local.identifier
  hls_segment_expiration_days = local.config.s3_hls.hls_retention_days
  recording_expiration_days   = local.config.s3_hls.recording_retention_days
  cors_allowed_origins        = local.config.s3_hls.cors_origins
  
  tags = {
    Project     = local.config.tags.Project
  }

}

# TODO: Enable when the ASG resource is merged
# module "monitoring" {
#   source = "./modules/tf-monitoring"

#   identifier       = local.identifier
#   asg_name         = module.live_go_asg.autoscaling_group_name
#   cpu_threshold    = local.config.monitoring_config.cpu_threshold
#   memory_threshold = local.config.monitoring_config.memory_threshold
#   disk_threshold   = local.config.monitoring_config.disk_threshold
#   sns_topic_arn    = ""

#   log_files = [
#     {
#       file_path      = "/var/log/messages"
#       log_group_name = "/ec2/${local.identifier}/messages"
#     }
#   ]

#   tags = local.tags
# }