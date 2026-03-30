variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "agentic-ai-integration-490716"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "portal26_ngrok_agent_id" {
  description = "Reasoning Engine ID for portal26_ngrok_agent"
  type        = string
  default     = "2658127084508938240"
}

variable "portal26_otel_agent_id" {
  description = "Reasoning Engine ID for portal26_otel_agent"
  type        = string
  default     = "7483734085236424704"
}

variable "portal26_ngrok_agent_env_vars" {
  description = "Environment variables for portal26_ngrok_agent"
  type = object({
    telemetry_enabled   = string
    otel_endpoint       = string
    service_name        = string
    resource_attributes = string
  })
  default = {
    telemetry_enabled   = "true"
    otel_endpoint       = "https://tabetha-unelemental-bibulously.ngrok-free.dev"
    service_name        = "portal26_ngrok_agent"
    resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local"
  }
}

variable "portal26_otel_agent_env_vars" {
  description = "Environment variables for portal26_otel_agent"
  type = object({
    telemetry_enabled   = string
    otel_endpoint       = string
    service_name        = string
    resource_attributes = string
  })
  default = {
    telemetry_enabled   = "true"
    otel_endpoint       = "https://otel-tenant1.portal26.in:4318"
    service_name        = "portal26_otel_agent"
    resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=otel-direct"
  }
}

variable "trigger_redeploy" {
  description = "Set to true to trigger agent redeployment when env vars change"
  type        = bool
  default     = false
}
