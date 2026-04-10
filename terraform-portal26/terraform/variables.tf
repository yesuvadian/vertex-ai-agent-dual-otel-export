# Portal 26 Integration Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Vertex AI Agent Engine"
  type        = string
  default     = "us-central1"
}

# Portal 26 Configuration
variable "portal26_endpoint" {
  description = "Portal 26 OTEL collector endpoint"
  type        = string
  # Example: "https://portal26.example.com" or "https://portal26.example.com/client-a"
}

variable "portal26_service_name" {
  description = "Service name for Portal 26 telemetry"
  type        = string
  default     = "vertex-ai-agents"
}

# Agent Configuration
variable "agents" {
  description = "Map of agents to deploy with Portal 26 integration"
  type = map(object({
    source_dir   = string  # Path to agent source code
    display_name = string  # Agent display name
  }))

  # Example:
  # agents = {
  #   "customer-support" = {
  #     source_dir   = "/path/to/support_agent"
  #     display_name = "Customer Support Agent"
  #   }
  #   "sales-assistant" = {
  #     source_dir   = "/path/to/sales_agent"
  #     display_name = "Sales Assistant"
  #   }
  # }
}
