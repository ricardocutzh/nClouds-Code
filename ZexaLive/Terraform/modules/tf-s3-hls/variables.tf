variable "identifier" {
  description = "unique identifier for resources"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.identifier))
    error_message = "Identifier can only have lower case letters, numbers and dashes"
  }
}

variable "tags" {
  description = "tags applied to all resources of the module"
  type        = map(string)
  default     = {}
}

variable "cloudfront_distribution_arn" {
  description = "ARN of the cloudfront distribution that will have reading acces to the bucket via OAC"
  type        = string
  default     = null
}

variable "hls_segment_expiration_days" {
  description = "days before S3 deletes the HLS segements on the address with the prefix /live/" 

  type        = number
  default     = 1

  validation {
    condition     = var.hls_segment_expiration_days >= 1
    error_message = "Minimum retention is 1 day"
  }
}

variable "recording_expiration_days" {
  description = "days before S3 deletes the HLS segements on the address with the prefix /recordings/" 
  type        = number
  default     = 30

  validation {
    condition     = var.recording_expiration_days >= 1
    error_message = "Minimum retention is 1 day"
  }
}

variable "cors_allowed_origins" {
  description = "allowed origins that can connect" 
  type        = list(string)
  default     = ["*"]
}