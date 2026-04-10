# Portal26 Telemetry Infrastructure
# This file manages the complete Portal26 telemetry stack infrastructure

# ============================================================================
# SERVICE ACCOUNTS
# ============================================================================

resource "google_service_account" "telemetry_worker" {
  account_id   = "telemetry-worker"
  display_name = "Telemetry Worker Service Account"
  description  = "Service account for telemetry worker to read traces and process logs"
  project      = var.project_id
}

# Grant Cloud Trace User role to read traces
resource "google_project_iam_member" "telemetry_worker_trace_reader" {
  project = var.project_id
  role    = "roles/cloudtrace.user"
  member  = "serviceAccount:${google_service_account.telemetry_worker.email}"
}

# Grant Logging Writer role (if worker needs to write logs)
resource "google_project_iam_member" "telemetry_worker_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.telemetry_worker.email}"
}

# ============================================================================
# PUB/SUB TOPIC & SUBSCRIPTION
# ============================================================================

resource "google_pubsub_topic" "telemetry_logs" {
  name    = "telemetry-logs"
  project = var.project_id

  labels = {
    purpose     = "portal26-telemetry"
    environment = var.environment
  }

  message_retention_duration = "604800s" # 7 days
}

resource "google_pubsub_subscription" "telemetry_processor" {
  name    = "telemetry-processor"
  topic   = google_pubsub_topic.telemetry_logs.id
  project = var.project_id

  # Acknowledge messages within 10 minutes
  ack_deadline_seconds = 600

  # Retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  # Dead letter policy (optional)
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.telemetry_dead_letter.id
    max_delivery_attempts = 5
  }

  labels = {
    purpose     = "portal26-telemetry"
    environment = var.environment
  }
}

# Dead letter topic for failed messages
resource "google_pubsub_topic" "telemetry_dead_letter" {
  name    = "telemetry-logs-dead-letter"
  project = var.project_id

  labels = {
    purpose     = "portal26-telemetry-dlq"
    environment = var.environment
  }
}

# Grant Pub/Sub Publisher role to telemetry worker
resource "google_pubsub_topic_iam_member" "telemetry_worker_publisher" {
  topic   = google_pubsub_topic.telemetry_logs.id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.telemetry_worker.email}"
  project = var.project_id
}

# Grant Pub/Sub Subscriber role to telemetry worker
resource "google_pubsub_subscription_iam_member" "telemetry_worker_subscriber" {
  subscription = google_pubsub_subscription.telemetry_processor.id
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.telemetry_worker.email}"
  project      = var.project_id
}

# ============================================================================
# LOG SINK
# ============================================================================

resource "google_logging_project_sink" "telemetry_sink" {
  name        = "telemetry-sink"
  project     = var.project_id
  destination = "pubsub.googleapis.com/${google_pubsub_topic.telemetry_logs.id}"

  # Filter for Vertex AI Reasoning Engine logs
  filter = var.log_sink_filter

  # This will create a unique writer identity (service account)
  unique_writer_identity = true
}

# Grant the log sink's service account permission to publish to Pub/Sub
resource "google_pubsub_topic_iam_member" "log_sink_publisher" {
  topic   = google_pubsub_topic.telemetry_logs.id
  role    = "roles/pubsub.publisher"
  member  = google_logging_project_sink.telemetry_sink.writer_identity
  project = var.project_id
}

# ============================================================================
# CLOUD RUN SERVICE (Optional - for production deployment)
# ============================================================================

resource "google_cloud_run_v2_service" "telemetry_worker" {
  count    = var.deploy_cloud_run ? 1 : 0
  name     = "telemetry-worker"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.telemetry_worker.email

    containers {
      image = var.telemetry_worker_image

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "PUBSUB_SUBSCRIPTION"
        value = google_pubsub_subscription.telemetry_processor.id
      }

      env {
        name  = "OTEL_ENDPOINT"
        value = var.portal26_otel_endpoint
      }

      env {
        name  = "OTEL_HEADERS"
        value = var.portal26_otel_headers
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = {
    purpose     = "portal26-telemetry"
    environment = var.environment
  }
}

# Allow Pub/Sub to invoke Cloud Run
resource "google_cloud_run_service_iam_member" "pubsub_invoker" {
  count    = var.deploy_cloud_run ? 1 : 0
  service  = google_cloud_run_v2_service.telemetry_worker[0].name
  location = google_cloud_run_v2_service.telemetry_worker[0].location
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# ============================================================================
# CLOUD STORAGE (for agent packages)
# ============================================================================

resource "google_storage_bucket" "agent_packages" {
  name          = "${var.project_id}-adk-staging"
  location      = var.region
  project       = var.project_id
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  labels = {
    purpose     = "vertex-ai-agents"
    environment = var.environment
  }
}

# Grant Storage Object Admin to service accounts
resource "google_storage_bucket_iam_member" "telemetry_worker_storage" {
  bucket = google_storage_bucket.agent_packages.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.telemetry_worker.email}"
}

# ============================================================================
# DATA SOURCES
# ============================================================================

data "google_project" "current" {
  project_id = var.project_id
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "telemetry_worker_service_account" {
  description = "Email of the telemetry worker service account"
  value       = google_service_account.telemetry_worker.email
}

output "pubsub_topic_name" {
  description = "Name of the Pub/Sub topic for telemetry logs"
  value       = google_pubsub_topic.telemetry_logs.name
}

output "pubsub_subscription_name" {
  description = "Name of the Pub/Sub subscription"
  value       = google_pubsub_subscription.telemetry_processor.name
}

output "log_sink_name" {
  description = "Name of the Cloud Logging sink"
  value       = google_logging_project_sink.telemetry_sink.name
}

output "log_sink_writer_identity" {
  description = "Service account created for the log sink"
  value       = google_logging_project_sink.telemetry_sink.writer_identity
}

output "cloud_run_url" {
  description = "URL of the Cloud Run service (if deployed)"
  value       = var.deploy_cloud_run ? google_cloud_run_v2_service.telemetry_worker[0].uri : "Not deployed"
}

output "storage_bucket_name" {
  description = "Name of the GCS bucket for agent packages"
  value       = google_storage_bucket.agent_packages.name
}
