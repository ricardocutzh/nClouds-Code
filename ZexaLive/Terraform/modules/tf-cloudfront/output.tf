output "distribution_arn" {
    description = "ARN of cloudfront distribution"
    value = aws_cloudfront_distribution.hls.arn
}

output "distribution_domain_name" {
    description = "Public domain of the cloudfront distribution"
    value = aws_cloudfront_distribution.hls.domain_name  
}

output "distribution_id" {
  description = "CloudFont distribution id needed for cache invalidation"
  value       = aws_cloudfront_distribution.hls.id
}   