# Outputs for AI Agent Terraform deployment

output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.ai_agent.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.ai_agent.name
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_v2_service.ai_agent.location
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.ai_agent.email
}

output "latest_revision" {
  description = "Latest revision name"
  value       = google_cloud_run_v2_service.ai_agent.latest_ready_revision
}

output "secrets" {
  description = "Secret Manager secret IDs"
  value = {
    gemini_api_key  = google_secret_manager_secret.gemini_api_key.secret_id
    otel_auth_header = google_secret_manager_secret.otel_auth_header.secret_id
  }
}

output "test_command" {
  description = "Command to test the deployed service"
  value       = <<-EOT
    # Test with authentication
    curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
      ${google_cloud_run_v2_service.ai_agent.uri}/status

    # Test chat endpoint
    curl -X POST ${google_cloud_run_v2_service.ai_agent.uri}/chat \
      -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
      -H "Content-Type: application/json" \
      -d '{"message": "What is the weather in Tokyo?"}'
  EOT
}

output "console_links" {
  description = "Useful Google Cloud Console links"
  value = {
    service = "https://console.cloud.google.com/run/detail/${var.region}/${var.service_name}?project=${var.project_id}"
    logs    = "https://console.cloud.google.com/logs/query?project=${var.project_id}"
    metrics = "https://console.cloud.google.com/monitoring?project=${var.project_id}"
    secrets = "https://console.cloud.google.com/security/secret-manager?project=${var.project_id}"
  }
}

output "deployment_info" {
  description = "Deployment configuration summary"
  value = {
    project_id  = var.project_id
    region      = var.region
    environment = var.environment
    agent_mode  = var.agent_mode
    cpu         = var.cpu
    memory      = var.memory
    min_instances = var.min_instances
    max_instances = var.max_instances
    public_access = var.allow_unauthenticated
  }
}
