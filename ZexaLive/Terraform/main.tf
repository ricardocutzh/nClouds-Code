module "hls_bucket" {
  source = "./modules/tf-s3-hls"

  identifier                  = local.identifier
  hls_segment_expiration_days = local.config.s3_hls.hls_retention_days
  recording_expiration_days   = local.config.s3_hls.recording_retention_days
  cors_allowed_origins        = local.config.s3_hls.cors_origins
  
  tags = local.tags
}

module "live_go_launch_template" {
  source = "./modules/tf-launch-template"

  identifier = local.identifier
  user_data  = local.config.server_config.user_data
  volume_size = local.config.server_config.volume_size
  volume_type = local.config.server_config.volume_type
  monitoring_enabled = local.config.server_config.monitoring_enabled
  tags = local.tags
}