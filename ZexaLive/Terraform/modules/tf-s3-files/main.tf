resource "aws_iam_role" "s3files_service" {
  name = "${var.identifier}-s3files-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "s3files.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_s3files_file_system" "hls" {
  bucket   = var.bucket_arn
  role_arn = aws_iam_role.s3files_service.arn

  tags = merge(var.tags, {
    Name = "${var.identifier}-hls-fs"
  })
}

resource "aws_s3files_mount_target" "hls" {
  for_each = toset(var.subnet_ids)

  file_system_id     = aws_s3files_file_system.hls.id
  subnet_id          = each.value
  security_groups    = var.security_group_ids
}

resource "aws_s3files_file_system_policy" "hls" {
  file_system_id = aws_s3files_file_system.hls.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowEC2Mount"
      Effect = "Allow"
      Principal = {
        AWS = var.ec2_role_arn
      }
      Action   = "s3files:ClientMount"
      Resource = "*"
    }]
  })
}
