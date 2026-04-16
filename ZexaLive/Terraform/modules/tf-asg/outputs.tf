output "autoscaling_group_id" {
  description = "The ID of the Auto Scaling Group"
  value       = aws_autoscaling_group.server_asg.id
}

output "autoscaling_group_arn" {
  description = "The ARN for this Auto Scaling Group"
  value       = aws_autoscaling_group.server_asg.arn
}

output "autoscaling_group_name" {
  description = "The name of the Auto Scaling Group"
  value       = aws_autoscaling_group.server_asg.name
}