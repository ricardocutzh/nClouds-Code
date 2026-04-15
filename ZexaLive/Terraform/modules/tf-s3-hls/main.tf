resource "aws_s3_bucket" "hls" {
  bucket = "${var.identifier}-hls-segments"

  tags = merge(var.tags, {
    Name    = "${var.identifier}-hls-segments"
    Purpose = "HLS live streaming segments and recordings"
  })
}

# resource "aws_s3_bucket_ownership_controls" "hls" {
#   bucket = aws_s3_bucket.hls.id

#   rule {
#     object_ownership = "BucketOwnerEnforced"
#   }
# }

resource "aws_s3_bucket_public_access_block" "hls" {

  bucket = aws_s3_bucket.hls.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "hls" {
  bucket = aws_s3_bucket.hls.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_cors_configuration" "hls" {
  bucket = aws_s3_bucket.hls.id

  cors_rule {
    allowed_origins = var.cors_allowed_origins
    allowed_methods = ["GET", "HEAD"]
    allowed_headers = ["*"]
    expose_headers = ["ETag"]
    max_age_seconds = 3600
  }
}


resource "aws_s3_bucket_lifecycle_configuration" "hls" {
  bucket = aws_s3_bucket.hls.id

  rule {
    id     = "expire-live-segments"
    status = "Enabled"

    filter {
      prefix = "live/"
    }

    expiration {
      days = var.hls_segment_expiration_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }

  rule {
    id     = "expire-recordings"
    status = "Enabled"

    filter {
      prefix = "recordings/"
    }

    expiration {
      days = var.recording_expiration_days
    }
  }
}

resource "aws_s3_bucket_policy" "hls" {
  bucket = aws_s3_bucket.hls.id

  depends_on = [aws_s3_bucket_public_access_block.hls]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [

      # Statement 1: CloudFront can read objects from bucket
      {
        Sid    = "AllowCloudFrontOACRead"
        Effect = var.cloudfront_distribution_arn != null ? "Allow" : "Deny"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.hls.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = var.cloudfront_distribution_arn != null ? var.cloudfront_distribution_arn : "arn:aws:cloudfront::000000000000:distribution/placeholder"
          }
        }
      },

      # Statement 2: deny any requests that don't use https
      {
        Sid       = "DenyNonHTTPS"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.hls.arn,
          "${aws_s3_bucket.hls.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
