# ──────────────────────────────────────
# CW Agent config
# ──────────────────────────────────────
resource "aws_ssm_parameter" "cloudwatch_agent_config" {
  name = "/cloudwatch-agent/${var.identifier}/config"
  type = "String"
  value = jsonencode({
    agent = {
      metrics_collection_interval = var.metrics_collection_interval
      run_as_user                 = "root"
    }
    metrics = {
      namespace = "CWAgent"
      append_dimensions = {
        AutoScalingGroupName = "$${aws:AutoScalingGroupName}"
        InstanceId           = "$${aws:InstanceId}"
      }
      metrics_collected = {
        mem = {
          measurement                 = ["mem_used_percent"]
          metrics_collection_interval = var.metrics_collection_interval
        }
        disk = {
          measurement                 = ["disk_used_percent"]
          resources                   = ["/"]
          metrics_collection_interval = var.metrics_collection_interval
        }
      }
    }
    logs = {
      logs_collected = {
        files = {
          collect_list = [
            for log in var.log_files : {
              file_path         = log.file_path
              log_group_name    = log.log_group_name
              log_stream_name   = log.log_stream_name
              retention_in_days = log.retention_days
            }
          ]
        }
      }
    }
  })
  tags = var.tags
}

# ──────────────────────────────────────
# Log Groups
# ──────────────────────────────────────
resource "aws_cloudwatch_log_group" "logs" {
  for_each          = { for log in var.log_files : log.log_group_name => log }
  name              = each.value.log_group_name
  retention_in_days = each.value.retention_days
  tags              = var.tags
}

# ──────────────────────────────────────
# Alarms
# ──────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.identifier}-high-cpu"
  alarm_description   = "CPU exceeds ${var.cpu_threshold}%"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.evaluation_periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = var.period
  statistic           = "Maximum"
  threshold           = var.cpu_threshold
  treat_missing_data  = "missing"
  dimensions          = { AutoScalingGroupName = var.asg_name }
  actions_enabled     = var.sns_topic_arn != ""
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []
  tags                = var.tags
}

resource "aws_cloudwatch_metric_alarm" "memory_high" {
  alarm_name          = "${var.identifier}-high-memory"
  alarm_description   = "Memory exceeds ${var.memory_threshold}%"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.evaluation_periods
  metric_name         = "mem_used_percent"
  namespace           = "CWAgent"
  period              = var.period
  statistic           = "Maximum"
  threshold           = var.memory_threshold
  treat_missing_data  = "missing"
  dimensions          = { AutoScalingGroupName = var.asg_name }
  actions_enabled     = var.sns_topic_arn != ""
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []
  tags                = var.tags
}

resource "aws_cloudwatch_metric_alarm" "disk_high" {
  alarm_name          = "${var.identifier}-high-disk"
  alarm_description   = "Disk exceeds ${var.disk_threshold}%"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.evaluation_periods
  metric_name         = "disk_used_percent"
  namespace           = "CWAgent"
  period              = var.period
  statistic           = "Maximum"
  threshold           = var.disk_threshold
  treat_missing_data  = "missing"
  dimensions = {
    AutoScalingGroupName = var.asg_name
    path                 = "/"
    fstype               = "xfs"
  }
  actions_enabled = var.sns_topic_arn != ""
  alarm_actions   = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []
  tags            = var.tags
}