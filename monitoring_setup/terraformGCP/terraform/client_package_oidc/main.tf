# ============================================================================
# Main Terraform Configuration (WITH OIDC Authentication)
# GCP Log Sink and Pub/Sub Infrastructure → AWS Lambda with OIDC
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Recommended: Use remote backend
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "observability-infrastructure-oidc"
  # }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ============================================================================
# Variables
# ============================================================================

variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "aws_lambda_url" {
  description = "AWS Lambda Function URL with OIDC support (where GCP logs will be pushed)"
  type        = string
}

variable "reasoning_engine_ids" {
  description = "List of Reasoning Engine IDs to monitor"
  type        = list(string)
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "agent_ids" {
  description = "List of Agent IDs to monitor (leave empty for all)"
  type        = list(string)
  default     = []
}

variable "log_severity_filter" {
  description = "List of log severities to export (DEBUG, INFO, WARNING, ERROR, CRITICAL). Empty list exports all."
  type        = list(string)
  default     = []
}

variable "log_resource_types" {
  description = "List of resource types to filter (e.g., cloud_run_revision, cloud_function). Empty list includes all."
  type        = list(string)
  default     = []
}

variable "custom_log_filter" {
  description = "Custom log filter expression. If use_custom_filter_only=true, this overrides all other filters."
  type        = string
  default     = ""
}

variable "use_custom_filter_only" {
  description = "If true, only use custom_log_filter and ignore all other filter settings"
  type        = bool
  default     = false
}

# ============================================================================
# Outputs
# ============================================================================

output "setup_complete" {
  description = "Setup completion message"
  value = <<-EOT
    ============================================================================
    GCP Log Sink Deployment Complete! (WITH OIDC AUTHENTICATION)
    ============================================================================

    GCP Resources Created:
    - Service Account: ${google_service_account.pubsub_oidc_invoker.email}
    - Pub/Sub Topic: ${google_pubsub_topic.reasoning_engine_logs.name}
    - Pub/Sub Subscription: ${google_pubsub_subscription.reasoning_engine_to_lambda.name}
    - Log Sink: ${google_logging_project_sink.reasoning_engine_to_pubsub.name}

    Target Endpoint:
    - Your AWS Lambda: ${var.aws_lambda_url}

    Security:
    - Authentication: OIDC (OpenID Connect)
    - OIDC Service Account: ${google_service_account.pubsub_oidc_invoker.email}
    - Token Audience: ${var.aws_lambda_url}
    - ✅ SECURE: Lambda MUST validate JWT tokens!

    IMPORTANT - Lambda Requirements:
    1. Lambda MUST validate OIDC tokens in Authorization header
    2. Token issuer: https://accounts.google.com
    3. Token audience: ${var.aws_lambda_url}
    4. Required Python packages: google-auth, cryptography

    See LAMBDA_OIDC_GUIDE.md for Lambda implementation

    Next Steps:
    1. Verify Lambda has OIDC validation logic
    2. Test: Generate a log in your Reasoning Engine
    3. Check Lambda logs for authenticated requests
    4. Monitor for authentication failures

    ============================================================================
  EOT
}

output "oidc_configuration" {
  description = "OIDC configuration details for Lambda"
  value = {
    service_account_email = google_service_account.pubsub_oidc_invoker.email
    token_audience        = var.aws_lambda_url
    token_issuer          = "https://accounts.google.com"
    expected_header       = "Authorization: Bearer <JWT_TOKEN>"
  }
}

output "pubsub_target_url" {
  description = "AWS Lambda URL (where logs are pushed with OIDC)"
  value       = var.aws_lambda_url
}

output "gcp_console_links" {
  description = "GCP Console links"
  value = {
    service_account     = "https://console.cloud.google.com/iam-admin/serviceaccounts/details/${google_service_account.pubsub_oidc_invoker.unique_id}?project=${var.gcp_project_id}"
    pubsub_topic        = "https://console.cloud.google.com/cloudpubsub/topic/detail/${google_pubsub_topic.reasoning_engine_logs.name}?project=${var.gcp_project_id}"
    pubsub_subscription = "https://console.cloud.google.com/cloudpubsub/subscription/detail/${google_pubsub_subscription.reasoning_engine_to_lambda.name}?project=${var.gcp_project_id}"
    log_sink            = "https://console.cloud.google.com/logs/router?project=${var.gcp_project_id}"
  }
}
