variable "identifier" {
  description = "Unique identifier for resource naming."
  type        = string
}

variable "bucket_arn" {
  description = "ARN of the existing S3 bucket to expose as a file system."
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs where mount targets will be created. One mount target is created per subnet for high availability"
  type        = list(string)
}

# still reviweing what type of role s3fiels needs
# variable "ec2_role_arn" {
#   description = "ARN of the IAM role attached to the EC2 instances via instance profile. This role will be allowed to mount the file system."
#   type        = string
# }

# variable "security_group_ids" {
#   description = "Security group IDs to attach to the mount targets. Should allow NFS traffic (port 2049) from the EC2 security group."
#   type        = list(string)
#   default     = []
# }

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}