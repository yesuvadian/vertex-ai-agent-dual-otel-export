# ============================================================================
# GCP Log Sink and Pub/Sub Configuration
# ============================================================================
# Purpose: Create Log Sink to forward Reasoning Engine logs to Pub/Sub
# Components:
#   - Pub/Sub Topic
#   - Pub/Sub Subscription (Push with OIDC)
#   - Service Account for OIDC authentication
#   - Log Sink with filter
#   - IAM permissions
# ============================================================================

# ============================================================================
# 1. Pub/Sub Topic
# ============================================================================
resource "google_pubsub_topic" "reasoning_engine_logs" {
  project = var.gcp_project_id
  name    = "reasoning-engine-logs-topic"

  labels = {
    purpose     = "agent-observability"
    destination = "aws-lambda"
    environment = "production"
  }

  message_retention_duration = "604800s" # 7 days
}

# ============================================================================
# 2. Service Account for OIDC Authentication
# ============================================================================
resource "google_service_account" "pubsub_oidc_invoker" {
  project      = var.gcp_project_id
  account_id   = "pubsub-oidc-invoker"
  display_name = "Pub/Sub OIDC Token Generator"
  description  = "Service account for generating OIDC tokens for Pub/Sub push subscriptions to AWS Lambda"
}

# Grant Token Creator role to service account
resource "google_project_iam_member" "pubsub_token_creator" {
  project = var.gcp_project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.pubsub_oidc_invoker.email}"
}

# ============================================================================
# 3. Pub/Sub Subscription with OIDC (Push to AWS Lambda)
# ============================================================================
resource "google_pubsub_subscription" "reasoning_engine_to_oidc" {
  project = var.gcp_project_id
  name    = "reasoning-engine-to-oidc"
  topic   = google_pubsub_topic.reasoning_engine_logs.name

  ack_deadline_seconds       = 10
  message_retention_duration = "604800s" # 7 days

  push_config {
    push_endpoint = var.aws_lambda_url

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
    environment = "production"
  }

  depends_on = [
    google_service_account.pubsub_oidc_invoker,
    google_project_iam_member.pubsub_token_creator
  ]
}

# ============================================================================
# 4. Log Sink - Forward Reasoning Engine Logs to Pub/Sub
# ============================================================================
resource "google_logging_project_sink" "reasoning_engine_to_pubsub" {
  project = var.gcp_project_id
  name    = "reasoning-engine-to-pubsub"

  # Destination: Pub/Sub Topic
  destination = "pubsub.googleapis.com/projects/${var.gcp_project_id}/topics/${google_pubsub_topic.reasoning_engine_logs.name}"

  # Filter: Build filter based on configuration
  filter = local.log_sink_filter

  # Use unique writer identity (creates dedicated service account)
  unique_writer_identity = true

  description = "Forward Reasoning Engine logs to Pub/Sub for AWS Lambda processing"
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
    "severity=\"${severity}\""
  ]) : ""

  # Build resource type filter
  resource_type_filter = length(var.log_resource_types) > 0 ? join(" OR ", [
    for resource_type in var.log_resource_types :
    "resource.type=\"${resource_type}\""
  ]) : ""

  # Combine all filters
  all_filters = compact([
    local.reasoning_engine_filter != "" ? "(${local.reasoning_engine_filter})" : "",
    local.agent_id_filter != "" ? "(${local.agent_id_filter})" : "",
    local.severity_filter != "" ? "(${local.severity_filter})" : "",
    local.resource_type_filter != "" ? "(${local.resource_type_filter})" : "",
    var.custom_log_filter != "" ? "(${var.custom_log_filter})" : ""
  ])

  # Final filter - use custom filter if provided, otherwise combine all filters
  log_sink_filter = var.use_custom_filter_only && var.custom_log_filter != "" ? var.custom_log_filter : (
    length(local.all_filters) > 0 ? join(" AND ", local.all_filters) : "resource.type=\"*\""
  )
}

# ============================================================================
# Variables
# ============================================================================
variable "aws_lambda_url" {
  description = "AWS Lambda Function URL for receiving logs"
  type        = string
  # Will be provided after Lambda is created
}

variable "agent_ids" {
  description = "List of Agent IDs to monitor (filters by resource.labels.agent_id)"
  type        = list(string)
  default     = []
  # Example: ["agent-001", "agent-002", "my-custom-agent"]
}

variable "log_severity_filter" {
  description = "List of log severities to filter (DEFAULT, DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL, ALERT, EMERGENCY)"
  type        = list(string)
  default     = []
  # Example: ["ERROR", "CRITICAL", "ALERT"]
}

variable "log_resource_types" {
  description = "List of GCP resource types to filter (e.g., 'gce_instance', 'cloud_function', 'k8s_container')"
  type        = list(string)
  default     = []
  # Example: ["gce_instance", "cloud_run_revision"]
}

variable "custom_log_filter" {
  description = "Custom log filter expression (Advanced Logging Query Language)"
  type        = string
  default     = ""
  # Example: "jsonPayload.message=~\"error\" AND timestamp>\"2024-01-01T00:00:00Z\""
}

variable "use_custom_filter_only" {
  description = "If true, only use custom_log_filter and ignore other filter variables"
  type        = bool
  default     = false
}

# ============================================================================
# Outputs
# ============================================================================
output "pubsub_topic_name" {
  description = "Pub/Sub Topic name"
  value       = google_pubsub_topic.reasoning_engine_logs.name
}

output "pubsub_subscription_name" {
  description = "Pub/Sub Subscription name"
  value       = google_pubsub_subscription.reasoning_engine_to_oidc.name
}

output "oidc_service_account_email" {
  description = "Service Account email for OIDC authentication"
  value       = google_service_account.pubsub_oidc_invoker.email
}

output "log_sink_name" {
  description = "Log Sink name"
  value       = google_logging_project_sink.reasoning_engine_to_pubsub.name
}

output "log_sink_writer_identity" {
  description = "Log Sink writer identity (service account)"
  value       = google_logging_project_sink.reasoning_engine_to_pubsub.writer_identity
}

output "log_sink_filter" {
  description = "Log Sink filter expression"
  value       = google_logging_project_sink.reasoning_engine_to_pubsub.filter
}
