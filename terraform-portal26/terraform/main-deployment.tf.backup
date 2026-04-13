# Portal 26 Integration for Vertex AI Agent Engine
# Manages agent deployment with OTEL telemetry to Portal 26

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Deploy agents with Portal 26 OTEL integration
resource "null_resource" "deploy_agents_portal26" {
  for_each = var.agents

  triggers = {
    portal26_endpoint = var.portal26_endpoint
    service_name      = var.portal26_service_name
    otel_module_hash  = filemd5("${path.module}/../otel_portal26.py")
    agent_source_hash = filemd5("${each.value.source_dir}/agent.py")
  }

  provisioner "local-exec" {
    command = <<-EOT
      python3 ${path.module}/../scripts/inject_otel_and_deploy.py \
        --agent-name "${each.key}" \
        --source-dir "${each.value.source_dir}" \
        --display-name "${each.value.display_name}" \
        --portal26-endpoint "${var.portal26_endpoint}" \
        --service-name "${var.portal26_service_name}" \
        --project-id "${var.project_id}" \
        --location "${var.region}"
    EOT
  }

  depends_on = [google_project_service.required_apis]
}

# Outputs
output "portal26_config" {
  value = {
    endpoint     = var.portal26_endpoint
    service_name = var.portal26_service_name
    agents       = keys(var.agents)
    agent_count  = length(var.agents)
  }
  description = "Portal 26 configuration summary"
}

output "deployment_status" {
  value = {
    for name, agent in var.agents : name => {
      display_name = agent.display_name
      source_dir   = agent.source_dir
    }
  }
  description = "Agent deployment details"
}
