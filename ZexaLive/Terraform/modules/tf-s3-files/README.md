# S3 Files — Implementation Guide
## Module: tf-s3-files

**Project:** Zexa Live — 4K HLS Streaming Infrastructure POC  
**Author:** Ricardo Chuy  
**Date:** April 2026

---

## What is S3 Files?

S3 Files is an AWS feature launched in April 2026 that exposes an S3 bucket as a mountable file system using NFS. It is built on top of Amazon EFS. Once mounted on an EC2 instance, the bucket is accessible as a regular folder — any program that reads and writes files from the operating system works against it.

The primary use case is **read access**: applications that cannot use the S3 SDK directly, can read objects from S3 as if they were local files. The file system also supports writes, but export synchronization back to S3 has a latency of approximately 1 minute (as of the initial tests), which makes it not very reliable for fast writing fastly to s3.

---

## Architecture

S3 Files introduces a network layer between the EC2 and S3. The mount target is the component that lives inside the VPC and handles NFS traffic:

```
EC2 (public subnet, AZ-a)
    │
    │ NFS v4.1, port 2049
Mount Target (public subnet, AZ-a)  <- one per AZ
    │
    │ S3 Files internal sync
S3 Bucket (global, outside VPC)
```

S3 itself does not live inside the VPC. The mount target is the bridge that makes the VPC-based EC2 talk to the global S3 service using a file system protocol.

---

## Terraform Module Structure

```
modules/tf-s3-files/
├── variables.tf   -> inputs: bucket ARN, subnet IDs, EC2 role
├── main.tf        -> all resources
└── outputs.tf     -> file system ID, mount command
```

### Resources Created

```
aws_iam_role.s3files_service            -> identity for the S3 Files service
aws_iam_role_policy.s3files_service     -> S3, EventBridge, KMS permissions
aws_s3files_file_system                 -> the file system on top of the bucket
aws_s3files_mount_target (x3)           -> one per public subnet via for_each
aws_s3files_file_system_policy          -> restricts ClientMount to EC2 role
aws_iam_role_policy.ec2_s3_read         -> ReadBypass policy on EC2 role
```

---

## IAM — Two Distinct Roles

This is the most important concept to understand before implementing. There are two completely separate IAM roles involved, with different purposes and different principals.

### Role 1 — S3 Files Service Role

This role is assumed by the **S3 Files service itself** to read and write objects in the bucket and manage EventBridge rules for change detection. It is not the EC2 role.

The trust principal is `elasticfilesystem.amazonaws.com` — this was confirmed by inspecting the role auto-created by the AWS console when creating a file system manually. AWS documentation and Terraform registry do not make this obvious.

```hcl
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
        "aws:SourceArn" = "arn:aws:s3files:${var.region}:${account_id}:file-system/*"
      }
    }
  }]
})
```

The permissions policy needs five statement groups: S3 bucket listing, S3 object operations, KMS, EventBridge rule management, and EventBridge read. The EventBridge rules are prefixed with `DO-NOT-DELETE-S3-Files`. AWS uses them internally to detect changes in the bucket. Do not delete or modify them.

### Role 2 — EC2 Instance Role

The existing EC2 role needs two additions:

**Addition 1 — Managed policy for mount access:**
```hcl
resource "aws_iam_role_policy_attachment" "s3files_client" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FilesClientFullAccess"
}

This Policy was added in the root file ´iam.tf´
```

**Addition 2 — Inline policy for ReadBypass:**

ReadBypass allows the mount client to read objects directly from S3 instead of routing everything through the NFS proxy. Without this, the proxy log shows `S3 bucket inaccessible: ReadBypass disabled` and the file system does not sync correctly.

```hcl
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
```

---

## Mount Targets and Auto Scaling

One mount target must exist per Availability Zone where EC2 instances can run. The mount command uses the **file system ID**, not the mount target ID. The `amazon-efs-utils` client automatically detects which AZ the EC2 is in and connects to the local mount target:

```
ASG launches EC2 in us-east-1a
  └── mount helper detects AZ
  └── connects to mount target in us-east-1a automatically

ASG launches EC2 in us-east-1b
  └── mount helper detects AZ
  └── connects to mount target in us-east-1b automatically
```

In Terraform, the mount targets are created with `for_each` over the list of public subnet IDs — the same subnets used by the ASG:

```hcl
resource "aws_s3files_mount_target" "hls" {
  for_each = toset(var.subnet_ids)

  file_system_id  = aws_s3files_file_system.hls.id
  subnet_id       = each.value
  security_groups = var.security_group_ids
}
```

Unlike the AWS console, which creates mount targets automatically, Terraform requires explicit declaration of each one.

---

## Networking Requirements

### Port 2049 — NFS Traffic

The security group attached to both the EC2 instances and the mount targets must allow inbound TCP port 2049 using a **self-referencing rule**. A self-reference means "allow traffic from other resources that share this same security group." This allows the EC2 and mount targets to communicate over NFS without opening the port to external IPs.

In the project YAML configuration:

```yaml
security_groups:
  - name: server
    ingress_self:
      - from_port: 2049
        to_port: 2049
        protocol: tcp
        description: NFS for S3 Files mount targets
```

In `networking.tf`, this requires using `ingress_with_self` as a separate input from `ingress_with_cidr_blocks`. The terraform-aws-modules/security-group module treats them differently.

### VPC Endpoint for S3

The project already has a Gateway VPC Endpoint for S3 in `networking.tf`. This routes S3 API traffic through AWS's internal network. S3 Files traffic goes through the mount target, which is a separate network path. Both coexist without conflict.

---

## S3 Bucket Prerequisites

The S3 bucket must have **versioning enabled** before creating the file system. S3 Files uses versioning to track and synchronize changes between the file system and the bucket. Attempting to create a file system on a bucket without versioning results in:

```
File systems require Bucket Versioning to be enabled for the bucket.
```

```hcl
resource "aws_s3_bucket_versioning" "hls" {
  bucket = aws_s3_bucket.hls.id

  versioning_configuration {
    status = "Enabled"
  }
}
```

---

## Mounting on the EC2

After running terraform apply all the infraestructure, access policies and configurations are ready and the only thing left to do is connect to an EC2 instance and run the following commands.

```bash
# 1. Install the client (version 3.0.0 or above required for S3 Files)
sudo yum install -y amazon-efs-utils

# 2. Verify version
mount.s3files --version

# 3. Create the mount point directory
sudo mkdir /mnt/s3files

# 4. Mount using the file system ID (not the mount target ID)
sudo mount -t s3files fs-xxxxxxxxxxxxxxxxx:/ /mnt/s3files

# 5. Verify the mount is active
df -h | grep s3files

# 6. Write a test file
echo "hello from EC2" | sudo tee /mnt/s3files/test.txt

# 7. Verify it appears in S3 (may take 1 minute)
aws s3 ls s3://your-bucket-name/
```

The file system ID is available as a Terraform output after apply:

```bash
terraform output mount_command
```

### Persisting the mount across reboots

Add this line to `/etc/fstab` so the file system remounts automatically if the EC2 restarts:

```
fs-xxxxxxxxxxxxxxxxx:/ /mnt/s3files s3files _netdev 0 0
```

For Auto Scaling Group deployments, the mount command should be in the EC2 launch template user data so every new instance mounts automatically on boot — this has not been automated yet and is listed as an open item.

---

## Troubleshooting

### Mount times out (Connection timed out)

```
b'mount.nfs4: Connection timed out'
```

The security group is missing the inbound rule for TCP port 2049. Add a self-referencing inbound rule for port 2049 as described in the Networking Requirements section.

### ReadBypass disabled

```
S3 bucket inaccessible: bucket='...', prefix=''. ReadBypass disabled.
```

The EC2 role is missing the inline policy with `s3:GetObject` and `s3:ListBucket`. Add the `ec2_s3_read` inline policy described in the IAM section.

### botocore import error

```
Failed to import botocore, please install botocore first.
```

This is a warning, not a blocking error. botocore is only required for CloudWatch monitoring of the file system. For basic mount and sync functionality it can be ignored. To resolve it:

```bash
sudo pip3 install botocore
```

---

## Export Latency — Known Limitation

During POC validation, a consistent ~1 minute delay was measured between writing a file to the mount point and it appearing in the S3 bucket. This is the export path: file system -> S3.

The `aws_s3files_synchronization_configuration` resource controls the import path (S3 -> file system) and does not expose tuning parameters for export speed. Export synchronization is managed internally by S3 Files and is not configurable.

**Impact on live HLS streaming:**

```
LiveGo generates .ts segments every 6-10 seconds
S3 Files exports to S3 with ~1 minute delay
CloudFront cannot serve segments not yet in S3

Observed latency:  ~60s export + ~20s HLS = ~80 seconds
Target (SOW):      ≤ 20 seconds
```

**Note:** S3 Files may not be suitable as the write path for live HLS segments. The recommended alternative for the live streaming use case is writing directly to S3 via the AWS SDK (`s3:PutObject`), which has millisecond write latency.

S3 Files remains useful in this project for post-event recording access, where the ~1 minute delay is acceptable and the ability to browse recordings as a file system from the EC2 has operational value.

## Important References:
* https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-files.html
* https://aws.amazon.com/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/
* https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3files_file_system
* https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-files-security-iam-awsmanpol.html
* https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-files-synchronization.html
