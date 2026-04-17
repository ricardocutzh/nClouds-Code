variable "identifier" {
  type = string
}

variable "asg_name" {
  type = string
}

variable "cpu_threshold" {
  type    = number
  default = 80
}

variable "memory_threshold" {
  type    = number
  default = 80
}

variable "disk_threshold" {
  type    = number
  default = 80
}

variable "evaluation_periods" {
  type    = number
  default = 2
}

variable "period" {
  type    = number
  default = 300
}

variable "metrics_collection_interval" {
  type    = number
  default = 60
}

variable "sns_topic_arn" {
  type    = string
  default = ""
}

variable "log_files" {
  type = list(object({
    file_path       = string
    log_group_name  = string
    log_stream_name = optional(string, "{instance_id}")
    retention_days  = optional(number, 60)
  }))
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}