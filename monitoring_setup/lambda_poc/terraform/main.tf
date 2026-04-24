# ============================================================================
# Main Terraform Configuration
# Cross-Cloud Observability Infrastructure: GCP → AWS
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
    Terraform Deployment Complete!
    ============================================================================

    GCP Resources:
    - Pub/Sub Topic: ${google_pubsub_topic.reasoning_engine_logs.name}
    - Pub/Sub Subscription: ${google_pubsub_subscription.reasoning_engine_to_oidc.name}
    - Log Sink: ${google_logging_project_sink.reasoning_engine_to_pubsub.name}
    - OIDC Service Account: ${google_service_account.pubsub_oidc_invoker.email}

    AWS Resources:
    - Lambda Function: ${aws_lambda_function.multi_customer_processor.function_name}
    - Lambda URL: ${aws_lambda_function_url.multi_customer_url.function_url}
    - S3 Buckets: ${join(", ", [for k, v in aws_s3_bucket.customer_traces : v.bucket])}
    - Kinesis Streams: ${join(", ", [for k, v in aws_kinesis_stream.customer_streams : v.name])}

    Security:
    - Authentication: Shared Secret (stored in Secrets Manager)
    - GCP Secret: ${google_secret_manager_secret.aws_shared_secret.secret_id}
    - AWS Secret: ${aws_secretsmanager_secret.gcp_shared_secret.name}

    Next Steps:
    1. Update GCP Pub/Sub subscription with Lambda URL (if not auto-updated)
    2. Test end-to-end flow: publish test message to Pub/Sub
    3. Check Lambda logs: aws logs tail /aws/lambda/${aws_lambda_function.multi_customer_processor.function_name}
    4. Monitor CloudWatch metrics

    ============================================================================
  EOT
}

output "lambda_function_url" {
  description = "Lambda Function URL (use in GCP Pub/Sub subscription)"
  value       = aws_lambda_function_url.multi_customer_url.function_url
}

output "gcp_console_links" {
  description = "GCP Console links"
  value = {
    pubsub_topic        = "https://console.cloud.google.com/cloudpubsub/topic/detail/${google_pubsub_topic.reasoning_engine_logs.name}?project=${var.gcp_project_id}"
    pubsub_subscription = "https://console.cloud.google.com/cloudpubsub/subscription/detail/${google_pubsub_subscription.reasoning_engine_to_oidc.name}?project=${var.gcp_project_id}"
    log_sink            = "https://console.cloud.google.com/logs/router?project=${var.gcp_project_id}"
  }
}

output "aws_console_links" {
  description = "AWS Console links"
  value = {
    lambda_function = "https://${var.aws_region}.console.aws.amazon.com/lambda/home?region=${var.aws_region}#/functions/${aws_lambda_function.multi_customer_processor.function_name}"
    cloudwatch_logs = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.lambda_logs.name, "/", "$252F")}"
  }
}
