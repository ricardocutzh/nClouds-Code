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
variable "m3u8_min_ttl" {
  description = "Minimum TTLT in seconds for .m3u8 playlist files"
  type = number
  default = 1
}

variable "m3u8_max_ttl" {
  description = "Maximum TTL in seconds for .m3u8 playlist files"
  type        = number
  default     = 5
}

variable "ts_min_ttl" {
  description = "Minimum TTL in seconds for .ts segment files"
  type = number
  default = 30
}

variable "ts_max_ttl" {
  description = "Maximum TTL in seconds for .ts segment files"
  type = number
  default = 86400
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