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