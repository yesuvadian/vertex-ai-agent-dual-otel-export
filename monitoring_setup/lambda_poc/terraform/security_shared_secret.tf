# ============================================================================
# Security Configuration - Shared Secret Authentication
# ============================================================================
# Purpose: Implement shared secret authentication between GCP and AWS
# Method: Shared secret stored in AWS Secrets Manager and GCP Secret Manager
# Note: GCP Pub/Sub does NOT support custom headers, so shared secret
#       will be embedded in message attributes or payload
# ============================================================================

# ============================================================================
# AWS Secrets Manager - Store Shared Secret
# ============================================================================
resource "aws_secretsmanager_secret" "gcp_shared_secret" {
  name        = "gcp-pubsub-shared-secret"
  description = "Shared secret for authenticating GCP Pub/Sub messages"

  tags = {
    Purpose     = "gcp-authentication"
    Environment = "production"
  }
}

resource "aws_secretsmanager_secret_version" "gcp_shared_secret_value" {
  secret_id = aws_secretsmanager_secret.gcp_shared_secret.id
  secret_string = jsonencode({
    secret_key = random_password.shared_secret.result
    created_at = timestamp()
  })
}

# Generate secure random shared secret
resource "random_password" "shared_secret" {
  length  = 64
  special = true
}

# ============================================================================
# GCP Secret Manager - Store Shared Secret
# ============================================================================
resource "google_secret_manager_secret" "aws_shared_secret" {
  project   = var.gcp_project_id
  secret_id = "aws-lambda-shared-secret"

  replication {
    auto {}
  }

  labels = {
    purpose     = "aws-authentication"
    environment = "production"
  }
}

resource "google_secret_manager_secret_version" "aws_shared_secret_value" {
  secret = google_secret_manager_secret.aws_shared_secret.id

  secret_data = random_password.shared_secret.result
}

# Grant Pub/Sub service account access to secret
resource "google_secret_manager_secret_iam_member" "pubsub_secret_accessor" {
  project   = var.gcp_project_id
  secret_id = google_secret_manager_secret.aws_shared_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pubsub_oidc_invoker.email}"
}

# ============================================================================
# Lambda IAM Policy - Access Secrets Manager
# ============================================================================
resource "aws_iam_role_policy" "lambda_secrets_access" {
  name = "${var.lambda_function_name}-secrets-access"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.gcp_shared_secret.arn
      }
    ]
  })
}

# ============================================================================
# Update Lambda Environment Variables
# ============================================================================
# Note: Shared secret verification will be done in Lambda code
# The secret will be retrieved from AWS Secrets Manager at runtime

# ============================================================================
# Outputs
# ============================================================================
output "shared_secret_aws_arn" {
  description = "AWS Secrets Manager ARN for shared secret"
  value       = aws_secretsmanager_secret.gcp_shared_secret.arn
  sensitive   = true
}

output "shared_secret_gcp_name" {
  description = "GCP Secret Manager name for shared secret"
  value       = google_secret_manager_secret.aws_shared_secret.secret_id
  sensitive   = true
}

output "shared_secret_value" {
  description = "Generated shared secret (DO NOT expose in production)"
  value       = random_password.shared_secret.result
  sensitive   = true
}

# ============================================================================
# Security Notes
# ============================================================================
# 1. GCP Pub/Sub does NOT support custom HTTP headers
# 2. Shared secret must be included in message payload or attributes
# 3. Lambda will verify shared secret from message data
# 4. Secrets are rotatable via Terraform
# 5. Use AWS Secrets Manager rotation for production
# ============================================================================
