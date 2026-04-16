resource "aws_cloudfront_origin_access_control" "hls" {
  name = "${var.identifier}-hls-oac"
  description = "OAC for HLS live streaming bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# resource "aws_cloudfront_distribution" "hls" {
  
# }