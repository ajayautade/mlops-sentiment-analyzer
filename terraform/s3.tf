# ==============================================================================
# S3 Bucket — Model Artifacts & Terraform State
# ==============================================================================
# Stores AI model artifacts and can be used as Terraform remote state backend.
# ==============================================================================

resource "aws_s3_bucket" "model_artifacts" {
  bucket        = "${var.project_name}-model-artifacts-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = {
    Name    = "${var.project_name}-model-artifacts"
    Purpose = "AI model storage and versioning"
  }
}

# Enable versioning for model artifact rollback
resource "aws_s3_bucket_versioning" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt all objects at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access (security best practice)
resource "aws_s3_bucket_public_access_block" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ──────────── Data source for AWS Account ID ────────────

data "aws_caller_identity" "current" {}
