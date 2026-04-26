# ============================================================================
# GCP Log Sink and Pub/Sub Configuration (No OIDC Authentication)
# ============================================================================
# Purpose: Create Log Sink to forward Reasoning Engine logs to Pub/Sub
# Components:
#   - Pub/Sub Topic
#   - Pub/Sub Subscription (Push without authentication)
#   - Log Sink with filter
#   - IAM permissions
# Note: Lambda does NOT validate authentication - use for testing only
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
    environment = var.environment
  }

  message_retention_duration = "604800s" # 7 days
}

# ============================================================================
# 2. Pub/Sub Subscription (Push to AWS Lambda - No Authentication)
# ============================================================================
resource "google_pubsub_subscription" "reasoning_engine_to_lambda" {
  project = var.gcp_project_id
  name    = "reasoning-engine-to-lambda"
  topic   = google_pubsub_topic.reasoning_engine_logs.name

  ack_deadline_seconds       = 10
  message_retention_duration = "604800s" # 7 days

  push_config {
    push_endpoint = var.aws_lambda_url
    # No authentication - Lambda is public and accepts all requests
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  labels = {
    purpose     = "agent-log-forwarding"
    destination = "aws-lambda"
    environment = var.environment
  }
}

# ============================================================================
# 3. Log Sink - Forward Reasoning Engine Logs to Pub/Sub
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
    "severity>=${severity}"
  ]) : ""

  # Build resource type filter
  resource_type_filter = length(var.log_resource_types) > 0 ? join(" OR ", [
    for resource_type in var.log_resource_types :
    "resource.type=\"${resource_type}\""
  ]) : ""

  # Combine all filters with AND logic
  all_filters = compact([
    local.reasoning_engine_filter != "" ? "(${local.reasoning_engine_filter})" : "",
    local.agent_id_filter != "" ? "(${local.agent_id_filter})" : "",
    local.severity_filter != "" ? "(${local.severity_filter})" : "",
    local.resource_type_filter != "" ? "(${local.resource_type_filter})" : "",
    var.custom_log_filter != "" ? "(${var.custom_log_filter})" : ""
  ])

  # Final filter: Use custom filter only if specified, otherwise combine all filters
  log_sink_filter = var.use_custom_filter_only && var.custom_log_filter != "" ? var.custom_log_filter : (
    length(local.all_filters) > 0 ? join(" AND ", local.all_filters) : "resource.type=\"*\""
  )
}

# ============================================================================
# Variables
# ============================================================================
variable "aws_lambda_url" {
  description = "Existing AWS Lambda Function URL (where GCP logs will be pushed)"
  type        = string
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
  description = "AWS Lambda URL receiving logs"
  value       = var.aws_lambda_url
}
