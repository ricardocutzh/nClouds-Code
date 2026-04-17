resource "aws_cloudfront_origin_access_control" "hls" {
  name = "${var.identifier}-hls-oac"
  description = "OAC for HLS live streaming bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# cache policy
resource "aws_cloudfront_cache_policy" "hls" {
  name    = "${var.identifier}-hls-cache-policy"
  comment = "Cache policy for HLS streaming (m3u8 and segments)"

  min_ttl = var.cache_min_ttl
  default_ttl = var.cache_default_ttl
  max_ttl = var.cache_max_ttl

  parameters_in_cache_key_and_forwarded_to_origin {
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
    enable_accept_encoding_gzip = true
    enable_accept_encoding_brotli = true
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

      s3_origin_config {
        origin_access_identity = ""  # required to be empty with OAC
      }
    }

    default_cache_behavior {
        target_origin_id = "S3-${var.identifier}-hls"
        allowed_methods = ["GET", "HEAD", "OPTIONS"]
        cached_methods  = ["GET", "HEAD"]

        cache_policy_id          = aws_cloudfront_cache_policy.hls.id
        origin_request_policy_id = aws_cloudfront_origin_request_policy.hls.id

        viewer_protocol_policy = "redirect-to-https"
        compress               = true
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