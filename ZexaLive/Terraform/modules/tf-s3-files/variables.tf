variable "identifier" {
  description = "Unique identifier for resource naming."
  type        = string
}

variable "region" {
  description = "AWS region. Used in IAM policy conditions and KMS resource ARNs."
  type        = string
  default     = "us-east-1"
}

variable "bucket_arn" {
  description = "ARN of the existing S3 bucket to expose as a file system."
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs where mount targets will be created. One mount target is created per subnet for high availability"
  type        = list(string)
}

variable "ec2_role_arn" {
  description = "ARN of the IAM role attached to EC2 instances. This role gets ClientMount permission."
  type        = string
}

variable "security_group_ids" {
  description = "Security group IDs attached to mount targets. Must allow NFS traffic (port 2049) from the EC2 security group."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}