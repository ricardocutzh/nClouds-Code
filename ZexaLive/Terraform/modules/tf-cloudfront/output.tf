output "distribution_arn" {
    description = "ARN of cloudfront distribution"
    value = aws_cloudfront_origin_access_control.hls  
}

output "distribution_domain_name" {
    description = "Public domain of the cloudfront distribution"
    value = aws_cloudfront_origin_access_control.hls.domain_name  
}

output "distribution_id" {
  description = "CloudFont distribution id needed for cache invalidation"
  value       = aws_cloudfront_origin_access_control.hls.id
}   