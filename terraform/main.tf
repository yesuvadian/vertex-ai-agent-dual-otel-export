terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Data source to get existing agents (for reference)
# Note: As of now, there's no direct Terraform resource for Reasoning Engine
# We'll use google_cloud_run_v2_service since Agent Engine deploys as Cloud Run

# For now, we'll use null_resource with gcloud commands to update env vars
# This is a workaround until Terraform adds native support for Reasoning Engine

resource "null_resource" "update_portal26_ngrok_agent_env" {
  triggers = {
    env_vars = jsonencode(var.portal26_ngrok_agent_env_vars)
  }

  provisioner "local-exec" {
    command = <<-EOT
      # Get the current agent configuration
      gcloud ai reasoning-engines describe ${var.portal26_ngrok_agent_id} \
        --location=${var.region} \
        --project=${var.project_id} \
        --format=json > temp_ngrok_config.json

      # Note: Direct update of env vars requires redeployment
      # Environment variables are set during deployment and stored in the package spec
    EOT
  }
}

resource "null_resource" "update_portal26_otel_agent_env" {
  triggers = {
    env_vars = jsonencode(var.portal26_otel_agent_env_vars)
  }

  provisioner "local-exec" {
    command = <<-EOT
      gcloud ai reasoning-engines describe ${var.portal26_otel_agent_id} \
        --location=${var.region} \
        --project=${var.project_id} \
        --format=json > temp_otel_config.json
    EOT
  }
}

# Create .env files for agents with Terraform variables
resource "local_file" "portal26_ngrok_agent_env" {
  filename = "${path.module}/../portal26_ngrok_agent/.env"
  content  = <<-EOF
GOOGLE_CLOUD_PROJECT=${var.project_id}
GOOGLE_CLOUD_LOCATION=${var.region}
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=${var.portal26_ngrok_agent_env_vars.telemetry_enabled}
OTEL_EXPORTER_OTLP_ENDPOINT=${var.portal26_ngrok_agent_env_vars.otel_endpoint}
OTEL_SERVICE_NAME=${var.portal26_ngrok_agent_env_vars.service_name}
OTEL_RESOURCE_ATTRIBUTES=${var.portal26_ngrok_agent_env_vars.resource_attributes}
EOF
}

resource "local_file" "portal26_otel_agent_env" {
  filename = "${path.module}/../portal26_otel_agent/.env"
  content  = <<-EOF
GOOGLE_CLOUD_PROJECT=${var.project_id}
GOOGLE_CLOUD_LOCATION=${var.region}
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=${var.portal26_otel_agent_env_vars.telemetry_enabled}
OTEL_EXPORTER_OTLP_ENDPOINT=${var.portal26_otel_agent_env_vars.otel_endpoint}
OTEL_SERVICE_NAME=${var.portal26_otel_agent_env_vars.service_name}
OTEL_RESOURCE_ATTRIBUTES=${var.portal26_otel_agent_env_vars.resource_attributes}
EOF
}

# Trigger redeployment when env vars change
resource "null_resource" "redeploy_portal26_ngrok_agent" {
  depends_on = [local_file.portal26_ngrok_agent_env]

  triggers = {
    env_file_content = local_file.portal26_ngrok_agent_env.content
  }

  provisioner "local-exec" {
    command     = <<-EOT
      cd ${path.module}/..
      python -m google.adk.cli deploy agent_engine portal26_ngrok_agent \
        --project ${var.project_id} \
        --region ${var.region} \
        --agent_engine_id ${var.portal26_ngrok_agent_id}
    EOT
    interpreter = ["bash", "-c"]
  }

  # Only run when explicitly triggered
  count = var.trigger_redeploy ? 1 : 0
}

resource "null_resource" "redeploy_portal26_otel_agent" {
  depends_on = [local_file.portal26_otel_agent_env]

  triggers = {
    env_file_content = local_file.portal26_otel_agent_env.content
  }

  provisioner "local-exec" {
    command     = <<-EOT
      cd ${path.module}/..
      python -m google.adk.cli deploy agent_engine portal26_otel_agent \
        --project ${var.project_id} \
        --region ${var.region} \
        --agent_engine_id ${var.portal26_otel_agent_id}
    EOT
    interpreter = ["bash", "-c"]
  }

  # Only run when explicitly triggered
  count = var.trigger_redeploy ? 1 : 0
}

output "portal26_ngrok_agent_env_file" {
  value = local_file.portal26_ngrok_agent_env.filename
}

output "portal26_otel_agent_env_file" {
  value = local_file.portal26_otel_agent_env.filename
}

output "portal26_ngrok_agent_id" {
  value = var.portal26_ngrok_agent_id
}

output "portal26_otel_agent_id" {
  value = var.portal26_otel_agent_id
}
