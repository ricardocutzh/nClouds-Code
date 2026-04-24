module "hls_bucket" {
  source = "./modules/tf-s3-hls"

  identifier                  = local.identifier
  hls_segment_expiration_days = local.config.s3_hls.hls_retention_days
  recording_expiration_days   = local.config.s3_hls.recording_retention_days
  cors_allowed_origins        = local.config.s3_hls.cors_origins
  cloudfront_distribution_arn = module.cdn.distribution_arn

  tags = {
    Project     = local.config.tags.Project
  }
}

module "cdn" {
    source = "./modules/tf-cloudfront"
    bucket_regional_domain_name = module.hls_bucket.bucket_regional_domain_name
    bucket_arn = module.hls_bucket.bucket_arn
    cache_default_ttl = local.config.cloudfront.cache_default_ttl
    cache_min_ttl = local.config.cloudfront.cache_min_ttl
    cache_max_ttl = local.config.cloudfront.cache_max_ttl

    identifier = local.identifier
    price_class = local.config.cloudfront.price_class
    tags = {
      Project = local.config.tags.Project
    }
}

output "hls_bucket_name" {
  description = "HLS bucket name. Should be used in Livego upload target."
  value       = module.hls_bucket.bucket_id
}

output "stream_url_template" {
  description = "Base URL to test the stream."
  value       = "https://${module.cdn.distribution_domain_name}/live/{stream-id}/index.m3u8"
}
  

module "live_go_launch_template" {
  source = "./modules/tf-launch-template"

  identifier = local.identifier
  # user_data  = local.config.server_config.user_data
  user_data  = yamldecode(templatefile("${path.module}/templates/${local.config.server_config.user_data1}", {}))
  volume_size = local.config.server_config.volume_size
  volume_type = local.config.server_config.volume_type
  monitoring_enabled = local.config.server_config.monitoring_enabled
  instance_profile = aws_iam_instance_profile.server_role.name
  security_group_ids = [module.vpc_sgs["server"].security_group_id]
  tags = local.tags
}

module "live_go_asg" {
  source = "./modules/tf-asg"

  identifier = local.identifier
  min_instances = local.config.server_config.min_instances
  max_instances = local.config.server_config.max_instances
  launch_template_id = module.live_go_launch_template.launch_template.id
  launch_template_version = module.live_go_launch_template.launch_template.latest_version
  subnets_ids = module.vpc[0].public_subnets
  instance_type =local.config.server_config.instance_type
  tags = local.tags
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
