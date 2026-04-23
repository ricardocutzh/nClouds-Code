variable "identifier" {
    description = "Unique identifier for resource"
    type = string

    validation {
      condition     = can(regex("^[a-z0-9-]+$", var.identifier))
      error_message = "Identifier can only contain lowercase letters, numbers and dashes."
    }
}

variable "tags" {
  description = "Tags applied to all resources in the module"
  type = map(string)
  default = {}
}

variable "bucket_regional_domain_name" {
    description = "Regional domain name of he S3 bucket used as cloudfront origin"
    type = string
}

variable "bucket_arn" {
  description = "ARN from the S3 bucket, used for the OAC permission"
  type = string
}

# cache behavior
variable "cache_min_ttl" {
  description = "Minimum TTL in seconds for HLS files"
  type = number
  default = 1
}

variable "cache_default_ttl" {
  description = "Default TTL in seconds for HLS files"
  type = number
  default = 86400
}

variable "cache_max_ttl" {
  description = "Maximum TTL in seconds for HLS files"
  type        = number
  default     = 31536000
}


# distribution
variable "price_class" {
    description = "Cloudfront proce class that determines which edge locations sreve content. Impacts cost"
    type = string
    default = "PriceClass_100"

  validation {
    condition = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.price_class)
    error_message = "price_class must be PriceClass_100, PriceClass_200 or PriceClass_All."
  }
  
}

variable "comment" {
  description = "Description shown in the AWS console for this distribution."
  type        = string
  default     = "HLS live streaming distribution"
}