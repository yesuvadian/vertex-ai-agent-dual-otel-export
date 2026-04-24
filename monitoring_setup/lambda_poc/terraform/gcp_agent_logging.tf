# ============================================================================
# GCP Agent Logging and Tracing Configuration
# ============================================================================
# Purpose: Enable logging for Vertex AI Reasoning Engines
# Note: Vertex AI automatically logs to Cloud Logging, no explicit enable needed
#       This file documents the logging configuration
# ============================================================================

# Variables for Agent Configuration
variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "agentic-ai-integration-490716"
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "reasoning_engine_ids" {
  description = "List of Reasoning Engine IDs to monitor"
  type        = list(string)
  default = [
    "8213677864684355584",
    "6010661182900273152",
    "8019460130754002944"
  ]
}

# ============================================================================
# Data Source: Verify Reasoning Engines Exist
# ============================================================================
# Note: This is a validation step - actual logging is automatic
# Vertex AI Reasoning Engines automatically send logs to Cloud Logging

data "google_project" "current" {
  project_id = var.gcp_project_id
}

# ============================================================================
# Logging Configuration
# ============================================================================
# Vertex AI Reasoning Engine logs are automatically captured with:
# - Resource type: aiplatform.googleapis.com/ReasoningEngine
# - Labels: reasoning_engine_id, project_id, location
# - Log levels: INFO, WARNING, ERROR, CRITICAL
# - Retention: 30 days (default Cloud Logging)
#
# No explicit Terraform resource needed - logging is automatic
# ============================================================================

# Output information about logging configuration
output "reasoning_engine_log_filter" {
  description = "Filter to use in Log Sink for these engines"
  value = join(" OR ", [
    for engine_id in var.reasoning_engine_ids :
    "resource.labels.reasoning_engine_id=\"${engine_id}\""
  ])
}

output "logging_info" {
  description = "Information about automatic logging"
  value = {
    message          = "Vertex AI Reasoning Engines automatically log to Cloud Logging"
    resource_type    = "aiplatform.googleapis.com/ReasoningEngine"
    default_retention = "30 days"
    log_location     = "https://console.cloud.google.com/logs/query?project=${var.gcp_project_id}"
  }
}
