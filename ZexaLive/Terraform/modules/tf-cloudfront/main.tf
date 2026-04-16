resource "aws_cloudfront_origin_access_control" "hls" {
  name = "${var.identifier}-hls-oac"
  description = "OAC for HLS live streaming bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# cache policy
resource "aws_cloudfront_cache_policy" "m3u8" {
  name    = "${var.identifier}-hls-m3u8-cache-policy"
  comment = "Short TTL cache policy for HLS playlist files (.m3mu8)"

  min_ttl = var.m3u8_min_ttl
  default_ttl = var.m3u8_min_ttl
  max_ttl = var.m3u8_max_ttl

  parameters_in_cache_key_and_forwarded_to_origin {
    headers_config {
      header_behavior = "none"
    }

    query_strings_config {
      query_string_behavior = "none"
    }
    cookies_config {
      cookie_behavior = "none"
    }
    enable_accept_encoding_gzip = true
    enable_accept_encoding_brotli = true
  }
}

resource "aws_cloudfront_cache_policy" "ts" {
  name = "${var.identifier}-hls-ts-cache-policy"
  comment = "Long TTL cache policy for HLS segment files (.ts)"

  min_ttl = var.ts_min_ttl
  default_ttl = var.ts_min_ttl
  max_ttl = var.ts_max_ttl

  parameters_in_cache_key_and_forwarded_to_origin {
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }

    cookies_config {
      cookie_behavior = "none"
    }

    enable_accept_encoding_gzip = false
    enable_accept_encoding_brotli = false
  }
}

resource "aws_cloudfront_origin_request_policy" "hls" {
  name = "${var.identifier}-hls-origin-request-policy"
  comment = "Forwards CORS header to S3 for HLS streaming"

  headers_config {
    header_behavior = "whitelist"
    headers {
        items = [
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers"
        ]
    }
  }
  query_strings_config {
    query_string_behavior = "none"
  }

  cookies_config {
    cookie_behavior = "none"
  }
}

resource "aws_cloudfront_distribution" "hls" {
    comment = var.comment
    enabled = true

    price_class = var.price_class

    tags = merge(var.tags, {
        Name = "${var.identifier}-hls-distribution"
    })

    origin {
      origin_id = "S3-${var.identifier}-hls"
      domain_name = var.bucket_regional_domain_name
      origin_access_control_id = aws_cloudfront_origin_access_control.hls.id
    }

    ordered_cache_behavior {
      path_pattern = "*.m3u8"
      target_origin_id = "S3-${var.identifier}-hls"

      allowed_methods = [ "GET", "HEAD" ]
      cached_methods = [ "GET", "HEAD" ]

      cache_policy_id = aws_cloudfront_cache_policy.m3u8.id
      origin_request_policy_id = aws_cloudfront_origin_request_policy.hls.id

      viewer_protocol_policy = "redirect-to-https"

      compress = true
    }

    ordered_cache_behavior {
      path_pattern = "*.ts"
      target_origin_id = "S3-${var.identifier}-hls"

      allowed_methods = [ "GET", "HEAD" ]
      cached_methods = [ "GET", "HEAD" ]

      cache_policy_id = aws_cloudfront_cache_policy.ts.id
      origin_request_policy_id = aws_cloudfront_origin_request_policy.hls.id

      viewer_protocol_policy = "redirect-to-https"
      compress = false
    }

    default_cache_behavior {
      target_origin_id = "S3-${var.identifier}-hls"

      allowed_methods = ["GET", "HEAD"]
      cached_methods  = ["GET", "HEAD"]

      # "CachingDisabled" managed policy by AWS
      # its a safe fallback
      cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
      viewer_protocol_policy = "redirect-to-https"
      compress = true
    }

    restrictions {
      geo_restriction {
        restriction_type = "none"
      }
    }

    viewer_certificate {
      cloudfront_default_certificate = true
    }
}