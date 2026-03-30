# Terraform configuration for AI Agent on Google Cloud Run
# This creates all necessary infrastructure for your AI agent deployment

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Optional: Store Terraform state in GCS bucket
  # Uncomment after creating a GCS bucket
  # backend "gcs" {
  #   bucket  = "agentic-ai-integration-490716-tfstate"
  #   prefix  = "ai-agent/state"
  # }
}

# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "generativelanguage.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Create Secret Manager secrets for sensitive data
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "gemini_api_key" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

resource "google_secret_manager_secret" "otel_auth_header" {
  secret_id = "otel-auth-header"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "otel_auth_header" {
  secret      = google_secret_manager_secret.otel_auth_header.id
  secret_data = var.otel_auth_header
}

# Create service account for Cloud Run
resource "google_service_account" "ai_agent" {
  account_id   = "ai-agent-sa"
  display_name = "AI Agent Service Account"
  description  = "Service account for AI Agent Cloud Run service"
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "gemini_key_access" {
  secret_id = google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ai_agent.email}"
}

resource "google_secret_manager_secret_iam_member" "otel_header_access" {
  secret_id = google_secret_manager_secret.otel_auth_header.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ai_agent.email}"
}

# Grant AI Platform User role to service account
resource "google_project_iam_member" "ai_platform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ai_agent.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "ai_agent" {
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.ai_agent.email

    containers {
      image = var.container_image

      # Environment variables (non-sensitive)
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      env {
        name  = "OTEL_SERVICE_NAME"
        value = var.otel_service_name
      }

      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = var.otel_endpoint
      }

      env {
        name  = "OTEL_EXPORTER_OTLP_PROTOCOL"
        value = "http/protobuf"
      }

      env {
        name  = "OTEL_TRACES_EXPORTER"
        value = "otlp"
      }

      env {
        name  = "OTEL_METRICS_EXPORTER"
        value = "otlp"
      }

      env {
        name  = "OTEL_LOGS_EXPORTER"
        value = "otlp"
      }

      env {
        name  = "OTEL_RESOURCE_ATTRIBUTES"
        value = "portal26.user.id=${var.portal26_user_id},portal26.tenant_id=${var.portal26_tenant_id},service.version=${var.service_version},deployment.environment=${var.environment}"
      }

      env {
        name  = "OTEL_METRIC_EXPORT_INTERVAL"
        value = "1000"
      }

      env {
        name  = "OTEL_LOGS_EXPORT_INTERVAL"
        value = "500"
      }

      env {
        name  = "AGENT_MODE"
        value = var.agent_mode
      }

      # Sensitive environment variables from Secret Manager
      env {
        name = "GOOGLE_CLOUD_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OTEL_EXPORTER_OTLP_HEADERS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.otel_auth_header.secret_id
            version = "latest"
          }
        }
      }

      # Resource limits
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      # Startup probe
      startup_probe {
        http_get {
          path = "/"
        }
        initial_delay_seconds = 0
        timeout_seconds       = 1
        period_seconds        = 3
        failure_threshold     = 3
      }

      # Liveness probe
      liveness_probe {
        http_get {
          path = "/status"
        }
        initial_delay_seconds = 0
        timeout_seconds       = 1
        period_seconds        = 10
        failure_threshold     = 3
      }
    }

    # Scaling configuration
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    # Timeout
    timeout = "${var.timeout_seconds}s"

    # Concurrency
    max_instance_request_concurrency = var.concurrency
  }

  # Traffic configuration
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_version.gemini_api_key,
    google_secret_manager_secret_version.otel_auth_header,
  ]
}

# IAM policy for public access (optional - controlled by variable)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0

  name     = google_cloud_run_v2_service.ai_agent.name
  location = google_cloud_run_v2_service.ai_agent.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
