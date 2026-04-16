variable "identifier" {
    description = "unique identifier for resources"
    type        = string
}

variable "min_instances" {
  description = "The minimum number of instances in the autoscaling group"
  type        = number
}

variable "max_instances" {
  description = "The maximum number of instances in the autoscaling group"
  type        = number
}

variable "launch_template_id" {
  description = "The ID of the launch template to use"
  type        = string
}

variable "launch_template_version" {
  type = string
}

variable "subnets_ids" {
  description = "A list of subnet IDs to launch resources in"
  type        = list(string)
}

variable "instance_type" {
  description = "Instance type (Note: Usually defined in the Launch Template)"
  type        = string
  default     = "t3.micro"
}

variable "tags" {
    description = "tags applied to all resources of the module"
    type        = map(string)
    default     = {}
}
