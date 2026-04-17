variable "identifier" {
    description = "unique identifier for resources"
    type        = string
}

variable "tags" {
    description = "tags applied to all resources of the module"
    type        = map(string)
    default     = {}
}

variable "amazon_linux_2023_ami" {
    type = string
    default = "al2023-ami-2023.11.20260413.0-kernel-6.18-x86_64"
}

variable "volume_size" {
    description = "The size of the EBS root volume in GB"
    type        = number
    default     = 20
}

variable "volume_type" {
    type = string
    default = "gp3"
}

variable "monitoring_enabled" {
    type = bool
    default = true
}

variable "instance_profile" {
    type = string
}

variable "user_data" {
    type = any
    default = {}
}

variable "security_group_ids" {
  description = "Security Groups Associated"
  type        = list(string)
  default     = []
}
# variable "security_group_id" {
#     description = "server security group"
# }

