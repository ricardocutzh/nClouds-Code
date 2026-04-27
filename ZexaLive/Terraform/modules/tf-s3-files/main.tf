data "aws_caller_identity" "current" {}

# trust policy
resource "aws_iam_role" "s3files_service" {
  name = "${var.identifier}-s3files-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowS3FilesAssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "elasticfilesystem.amazonaws.com"
      }
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
        ArnLike = {
          "aws:SourceArn" = "arn:aws:s3files:${var.region}:${data.aws_caller_identity.current.account_id}:file-system/*"
        }
      }
    }]
  })

  tags = var.tags
}

# necessary permissions for s3 read 
resource "aws_iam_role_policy" "ec2_s3_read" {
  name = "${var.identifier}-ec2-s3-read-policy"
  role = var.ec2_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "S3ObjectReadAccess"
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket"
      ]
      Resource = [
        var.bucket_arn,
        "${var.bucket_arn}/*"
      ]
    }]
  })
}

# policies necesarry when creating a s3 file system
resource "aws_iam_role_policy" "s3files_service" {
  name = "${var.identifier}-s3files-service-policy"
  role = aws_iam_role.s3files_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3BucketPermissions"
        Effect = "Allow"
        Action = ["s3:ListBucket*"]
        Resource = var.bucket_arn
        Condition = {
          StringEquals = {
            "aws:ResourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "S3ObjectPermissions"
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:DeleteObject*",
          "s3:GetObject*",
          "s3:List*",
          "s3:PutObject*"
        ]
        Resource = "${var.bucket_arn}/*"
        Condition = {
          StringEquals = {
            "aws:ResourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "UseKmsKeyWithS3Files"
        Effect = "Allow"
        Action = [
          "kms:GenerateDataKey",
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncryptFrom",
          "kms:ReEncryptTo"
        ]
        Condition = {
          StringLike = {
            "kms:ViaService" = "s3.${var.region}.amazonaws.com"
            "kms:EncryptionContext:aws:s3:arn" = [
              var.bucket_arn,
              "${var.bucket_arn}/*"
            ]
          }
        }
        Resource = "arn:aws:kms:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Sid    = "EventBridgeManage"
        Effect = "Allow"
        Action = [
          "events:DeleteRule",
          "events:DisableRule",
          "events:EnableRule",
          "events:PutRule",
          "events:PutTargets",
          "events:RemoveTargets"
        ]
        Condition = {
          StringEquals = {
            "events:ManagedBy" = "elasticfilesystem.amazonaws.com"
          }
        }
        Resource = ["arn:aws:events:*:*:rule/DO-NOT-DELETE-S3-Files*"]
      },
      {
        Sid    = "EventBridgeRead"
        Effect = "Allow"
        Action = [
          "events:DescribeRule",
          "events:ListRuleNamesByTarget",
          "events:ListRules",
          "events:ListTargetsByRule"
        ]
        Resource = ["arn:aws:events:*:*:rule/*"]
      }
    ]
  })
}

resource "aws_s3files_file_system" "hls" {
  bucket   = var.bucket_arn
  role_arn = aws_iam_role.s3files_service.arn

  tags = merge(var.tags, {
    Name = "${var.identifier}-hls-fs"
  })
}

# mount target for each subnet_ids
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
