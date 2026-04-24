

output "file_system_id" {
  description = "S3 Files file system ID. Needed to construct the mount command on the EC2."
  value       = aws_s3files_file_system.hls.id
}

output "file_system_arn" {
  description = "ARN of the file system."
  value       = aws_s3files_file_system.hls.arn
}

output "mount_command" {
  description = <<-EOT
    Ready-to-use mount command for the EC2 instance.
    Run this on the EC2 after installing amazon-efs-utils:
      sudo mkdir -p /mnt/s3files
      sudo mount -t s3files {file_system_id}:/ /mnt/s3files
  EOT
  value = "sudo mount -t s3files ${aws_s3files_file_system.hls.id}:/ /mnt/s3files"
}