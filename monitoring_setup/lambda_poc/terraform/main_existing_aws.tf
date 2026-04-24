# ============================================================================
# Terraform Configuration - Integration with Existing AWS Infrastructure
# ============================================================================
# This configuration creates GCP Log Sink and Pub/Sub infrastructure to
# forward logs from existing Vertex AI Reasoning Engines to your existing
# AWS Lambda or API Gateway endpoint.
#
# DOES NOT CREATE:
# - Vertex AI agents (they already exist)
# - Lambda function (you already have it)
# - API Gateway (you already have it)
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# ============================================================================
# Providers
# ============================================================================

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "aws" {
  region = var.aws_region
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

variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "reasoning_engine_ids" {
  description = "List of existing Vertex AI Reasoning Engine IDs to monitor"
  type        = list(string)
}

variable "aws_endpoint_type" {
  description = "Type of AWS endpoint (lambda_url, api_gateway, https)"
  type        = string
  default     = "lambda_url"

  validation {
    condition     = contains(["lambda_url", "api_gateway", "https"], var.aws_endpoint_type)
    error_message = "Must be one of: lambda_url, api_gateway, https"
  }
}

variable "aws_endpoint_url" {
  description = "Existing AWS Lambda URL or API Gateway endpoint"
  type        = string
}

variable "existing_lambda_function_name" {
  description = "Name of existing Lambda function (optional, for IAM updates)"
  type        = string
  default     = ""
}

variable "authentication_method" {
  description = "Authentication method (shared_secret_attribute, shared_secret_header, none)"
  type        = string
  default     = "shared_secret_attribute"

  validation {
    condition     = contains(["shared_secret_attribute", "shared_secret_header", "none"], var.authentication_method)
    error_message = "Must be one of: shared_secret_attribute, shared_secret_header, none"
  }
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
}

variable "pubsub_topic_name" {
  description = "Name of Pub/Sub topic"
  type        = string
  default     = "reasoning-engine-logs-topic"
}

variable "pubsub_subscription_name" {
  description = "Name of Pub/Sub subscription"
  type        = string
  default     = "reasoning-engine-to-existing-endpoint"
}

variable "log_sink_name" {
  description = "Name of Log Sink"
  type        = string
  default     = "reasoning-engine-to-pubsub"
}

# ============================================================================
# Outputs
# ============================================================================

output "gcp_project_id" {
  description = "GCP Project ID"
  value       = var.gcp_project_id
}

output "pubsub_topic_name" {
  description = "Pub/Sub Topic name"
  value       = google_pubsub_topic.reasoning_engine_logs.name
}

output "pubsub_topic_id" {
  description = "Pub/Sub Topic full ID"
  value       = google_pubsub_topic.reasoning_engine_logs.id
}

output "pubsub_subscription_name" {
  description = "Pub/Sub Subscription name"
  value       = google_pubsub_subscription.reasoning_engine_to_existing.name
}

output "log_sink_name" {
  description = "Log Sink name"
  value       = google_logging_project_sink.reasoning_engine_to_pubsub.name
}

output "log_sink_writer_identity" {
  description = "Log Sink service account"
  value       = google_logging_project_sink.reasoning_engine_to_pubsub.writer_identity
}

output "aws_endpoint_url" {
  description = "Target AWS endpoint URL"
  value       = var.aws_endpoint_url
}

output "shared_secret_value" {
  description = "Generated shared secret (sensitive)"
  value       = random_password.shared_secret.result
  sensitive   = true
}

output "aws_secret_arn" {
  description = "AWS Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.gcp_shared_secret.arn
}

output "gcp_secret_id" {
  description = "GCP Secret Manager secret ID"
  value       = google_secret_manager_secret.aws_shared_secret.id
}

output "deployment_summary" {
  description = "Deployment summary"
  value       = <<-EOT

  ✅ Deployment Complete!

  GCP Resources Created:
  ├─ Log Sink: ${google_logging_project_sink.reasoning_engine_to_pubsub.name}
  ├─ Pub/Sub Topic: ${google_pubsub_topic.reasoning_engine_logs.name}
  ├─ Pub/Sub Subscription: ${google_pubsub_subscription.reasoning_engine_to_existing.name}
  ├─ Service Account: ${google_service_account.pubsub_invoker.email}
  └─ Secret: ${google_secret_manager_secret.aws_shared_secret.secret_id}

  AWS Resources Created:
  └─ Secret: ${aws_secretsmanager_secret.gcp_shared_secret.name}

  Target Endpoint: ${var.aws_endpoint_url}

  Next Steps:
  1. Test with: gcloud pubsub topics publish ${google_pubsub_topic.reasoning_engine_logs.name} --message='{"test": "data"}'
  2. Check your Lambda/API Gateway logs
  3. Verify shared secret: terraform output shared_secret_value

  EOT
}
