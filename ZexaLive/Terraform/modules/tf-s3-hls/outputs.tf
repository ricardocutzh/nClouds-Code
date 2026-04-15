output "bucket_id" {
  description = "bucket name"
  value       = aws_s3_bucket.hls.id
}

output "bucket_arn" {
  description = "ARN of the bucket. Necessary for cloudfront OAC and reference bucket as origin, FORMAT: arn:aws:s3:::nombre-del-bucket"
  value = aws_s3_bucket.hls.arn
}

output "bucket_regional_domain_name" {
  description = "Regional endpoint  endpoint of the bucket. Necessary for Cloudfront origin config"
  value = aws_s3_bucket.hls.bucket_regional_domain_name
}
