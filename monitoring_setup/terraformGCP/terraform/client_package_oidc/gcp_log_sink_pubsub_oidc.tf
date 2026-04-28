# ============================================================================
# GCP Log Sink and Pub/Sub Configuration (WITH OIDC Authentication)
# ============================================================================
# Purpose: Create Log Sink to forward Reasoning Engine logs to Pub/Sub
# Components:
#   - Service Account for OIDC
#   - Pub/Sub Topic
#   - Pub/Sub Subscription (Push with OIDC authentication)
#   - Log Sink with filter
#   - IAM permissions
# Security: Lambda MUST validate OIDC JWT tokens
# ============================================================================

# ============================================================================
# 1. Service Account for OIDC Token Generation
# ============================================================================
resource "google_service_account" "pubsub_oidc_invoker" {
  project      = var.gcp_project_id
  account_id   = "pubsub-oidc-invoker"
  display_name = "Pub/Sub OIDC Token Invoker"
  description  = "Service account for generating OIDC tokens to authenticate Pub/Sub push to Lambda"
}

# Note: Token Creator role is automatically granted by GCP Pub/Sub for OIDC
# No explicit IAM binding needed - Pub/Sub manages this internally
# If you encounter OIDC token errors, a project admin can manually grant:
# gcloud projects add-iam-policy-binding PROJECT_ID \
#   --member="serviceAccount:pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com" \
#   --role="roles/iam.serviceAccountTokenCreator"

# ============================================================================
# 2. Pub/Sub Topic
# ============================================================================
resource "google_pubsub_topic" "reasoning_engine_logs" {
  project = var.gcp_project_id
  name    = "reasoning-engine-logs-topic"

  labels = {
    purpose     = "agent-observability"
    destination = "aws-lambda"
    environment = var.environment
    auth_method = "oidc"
  }

  message_retention_duration = "604800s" # 7 days
}

# ============================================================================
# 3. Pub/Sub Subscription (Push to AWS Lambda - WITH OIDC Authentication)
# ============================================================================
resource "google_pubsub_subscription" "reasoning_engine_to_lambda" {
  project = var.gcp_project_id
  name    = "reasoning-engine-to-lambda-oidc"
  topic   = google_pubsub_topic.reasoning_engine_logs.name

  ack_deadline_seconds       = 10
  message_retention_duration = "604800s" # 7 days

  push_config {
    push_endpoint = var.aws_lambda_url

    # OIDC Authentication
    oidc_token {
      service_account_email = google_service_account.pubsub_oidc_invoker.email
      audience              = var.aws_lambda_url
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  labels = {
    purpose     = "agent-log-forwarding"
    destination = "aws-lambda"
    environment = var.environment
    auth_method = "oidc"
  }

  # No explicit dependency needed - GCP Pub/Sub handles OIDC token generation
}

# ============================================================================
# 4. Log Sink - Forward Reasoning Engine Logs to Pub/Sub
# ============================================================================
resource "google_logging_project_sink" "reasoning_engine_to_pubsub" {
  project = var.gcp_project_id
  name    = "reasoning-engine-to-pubsub-oidc"

  # Destination: Pub/Sub Topic
  destination = "pubsub.googleapis.com/projects/${var.gcp_project_id}/topics/${google_pubsub_topic.reasoning_engine_logs.name}"

  # Filter: Build filter based on configuration
  filter = local.log_sink_filter

  # Use unique writer identity (creates dedicated service account)
  unique_writer_identity = true

  description = "Forward Reasoning Engine logs to Pub/Sub with OIDC authentication for AWS Lambda"
}

# Grant Log Sink writer permission to publish to Pub/Sub
resource "google_pubsub_topic_iam_member" "log_sink_publisher" {
  project = var.gcp_project_id
  topic   = google_pubsub_topic.reasoning_engine_logs.name
  role    = "roles/pubsub.publisher"
  member  = google_logging_project_sink.reasoning_engine_to_pubsub.writer_identity
}

# ============================================================================
# Local Variables - Filter Construction
# ============================================================================
locals {
  # Build reasoning engine filter
  reasoning_engine_filter = length(var.reasoning_engine_ids) > 0 ? join(" OR ", [
    for engine_id in var.reasoning_engine_ids :
    "resource.labels.reasoning_engine_id=\"${engine_id}\""
  ]) : ""

  # Build agent ID filter
  agent_id_filter = length(var.agent_ids) > 0 ? join(" OR ", [
    for agent_id in var.agent_ids :
    "resource.labels.agent_id=\"${agent_id}\""
  ]) : ""

  # Build severity filter
  severity_filter = length(var.log_severity_filter) > 0 ? join(" OR ", [
    for severity in var.log_severity_filter :
    "severity>=${severity}"
  ]) : ""

  # Combine all filters with AND logic
  all_filters = compact([
    local.reasoning_engine_filter != "" ? "(${local.reasoning_engine_filter})" : "",
    local.agent_id_filter != "" ? "(${local.agent_id_filter})" : "",
    local.severity_filter != "" ? "(${local.severity_filter})" : ""
  ])

  # Final filter: Combine all filters
  log_sink_filter = length(local.all_filters) > 0 ? join(" AND ", local.all_filters) : "resource.type=\"*\""
}

# ============================================================================
# Outputs
# ============================================================================
output "oidc_service_account_email" {
  description = "Service account email for OIDC token generation"
  value       = google_service_account.pubsub_oidc_invoker.email
}

output "pubsub_topic_name" {
  description = "Pub/Sub Topic name"
  value       = google_pubsub_topic.reasoning_engine_logs.name
}

output "pubsub_subscription_name" {
  description = "Pub/Sub Subscription name"
  value       = google_pubsub_subscription.reasoning_engine_to_lambda.name
}

output "log_sink_name" {
  description = "Log Sink name"
  value       = google_logging_project_sink.reasoning_engine_to_pubsub.name
}

output "log_sink_filter" {
  description = "Generated log filter"
  value       = local.log_sink_filter
}

output "lambda_target_url" {
  description = "AWS Lambda URL receiving logs (with OIDC authentication)"
  value       = var.aws_lambda_url
}
