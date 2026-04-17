output "ssm_parameter_name" {
  value = aws_ssm_parameter.cloudwatch_agent_config.name
}

output "alarm_arns" {
  value = {
    cpu    = aws_cloudwatch_metric_alarm.cpu_high.arn
    memory = aws_cloudwatch_metric_alarm.memory_high.arn
    disk   = aws_cloudwatch_metric_alarm.disk_high.arn
  }
}