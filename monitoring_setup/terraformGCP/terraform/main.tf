# ============================================================================
# Main Terraform Configuration
# GCP Log Sink and Pub/Sub Infrastructure → Existing AWS Lambda
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
  #   prefix = "observability-infrastructure"
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
  description = "Existing AWS Lambda Function URL (where GCP logs will be pushed)"
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

# ============================================================================
# Outputs
# ============================================================================

output "setup_complete" {
  description = "Setup completion message"
  value = <<-EOT
    ============================================================================
    GCP Log Sink Deployment Complete!
    ============================================================================

    GCP Resources Created:
    - Pub/Sub Topic: ${google_pubsub_topic.reasoning_engine_logs.name}
    - Pub/Sub Subscription: ${google_pubsub_subscription.reasoning_engine_to_oidc.name}
    - Log Sink: ${google_logging_project_sink.reasoning_engine_to_pubsub.name}
    - OIDC Service Account: ${google_service_account.pubsub_oidc_invoker.email}

    Target Endpoint:
    - Your AWS Lambda: ${var.aws_lambda_url}

    Security:
    - Authentication: OIDC (JWT tokens from GCP)
    - Service Account: ${google_service_account.pubsub_oidc_invoker.email}

    Next Steps:
    1. Verify Pub/Sub subscription is pushing to your Lambda
    2. Test: Generate a log in your Reasoning Engine
    3. Check your existing Lambda logs for incoming GCP messages
    4. Ensure your Lambda validates OIDC JWT tokens

    ============================================================================
  EOT
}

output "pubsub_target_url" {
  description = "Your existing AWS Lambda URL (where logs are pushed)"
  value       = var.aws_lambda_url
}

output "gcp_console_links" {
  description = "GCP Console links"
  value = {
    pubsub_topic        = "https://console.cloud.google.com/cloudpubsub/topic/detail/${google_pubsub_topic.reasoning_engine_logs.name}?project=${var.gcp_project_id}"
    pubsub_subscription = "https://console.cloud.google.com/cloudpubsub/subscription/detail/${google_pubsub_subscription.reasoning_engine_to_oidc.name}?project=${var.gcp_project_id}"
    log_sink            = "https://console.cloud.google.com/logs/router?project=${var.gcp_project_id}"
  }
}
