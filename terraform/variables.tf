# Variables for AI Agent Terraform configuration

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "agentic-ai-integration-490716"
}

variable "region" {
  description = "GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "ai-agent"
}

variable "container_image" {
  description = "Container image to deploy (format: gcr.io/PROJECT/IMAGE:TAG)"
  type        = string
  default     = "gcr.io/agentic-ai-integration-490716/ai-agent:latest"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "service_version" {
  description = "Service version for tracking"
  type        = string
  default     = "1.0"
}

# Secrets (should be provided via terraform.tfvars or environment variables)
variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}

variable "otel_auth_header" {
  description = "OpenTelemetry authentication header (format: Authorization=Basic base64string)"
  type        = string
  sensitive   = true
}

# OpenTelemetry Configuration
variable "otel_service_name" {
  description = "Service name for OpenTelemetry"
  type        = string
  default     = "ai-agent"
}

variable "otel_endpoint" {
  description = "OpenTelemetry collector endpoint"
  type        = string
  default     = "https://otel-tenant1.portal26.in:4318"
}

variable "portal26_user_id" {
  description = "Portal26 user ID"
  type        = string
  default     = "relusys"
}

variable "portal26_tenant_id" {
  description = "Portal26 tenant ID"
  type        = string
  default     = "tenant1"
}

# Agent Configuration
variable "agent_mode" {
  description = "Agent mode: manual, adk, or both"
  type        = string
  default     = "manual"

  validation {
    condition     = contains(["manual", "adk", "both"], var.agent_mode)
    error_message = "Agent mode must be one of: manual, adk, both"
  }
}

# Resource Configuration
variable "cpu" {
  description = "CPU allocation for Cloud Run service"
  type        = string
  default     = "1"

  validation {
    condition     = contains(["1", "2", "4", "8"], var.cpu)
    error_message = "CPU must be one of: 1, 2, 4, 8"
  }
}

variable "memory" {
  description = "Memory allocation for Cloud Run service"
  type        = string
  default     = "512Mi"

  validation {
    condition     = can(regex("^[0-9]+(Mi|Gi)$", var.memory))
    error_message = "Memory must be in format like '512Mi' or '1Gi'"
  }
}

variable "timeout_seconds" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300

  validation {
    condition     = var.timeout_seconds >= 1 && var.timeout_seconds <= 3600
    error_message = "Timeout must be between 1 and 3600 seconds"
  }
}

variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 80

  validation {
    condition     = var.concurrency >= 1 && var.concurrency <= 1000
    error_message = "Concurrency must be between 1 and 1000"
  }
}

# Scaling Configuration
variable "min_instances" {
  description = "Minimum number of instances (0 = scale to zero)"
  type        = number
  default     = 0

  validation {
    condition     = var.min_instances >= 0 && var.min_instances <= 100
    error_message = "Min instances must be between 0 and 100"
  }
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10

  validation {
    condition     = var.max_instances >= 1 && var.max_instances <= 1000
    error_message = "Max instances must be between 1 and 1000"
  }
}

# Access Control
variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = false
}
