# ============================================================================
# Terraform Bootstrap - GCP Service Account Setup
# ============================================================================
# Purpose: Create service account with required permissions for main Terraform
# Run this ONCE before deploying main infrastructure
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# Provider Configuration
# ============================================================================
# NOTE: This initial run requires your personal user credentials (Owner role)
# After creating the service account, you'll use it for main infrastructure

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ============================================================================
# Variables
# ============================================================================

variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "service_account_id" {
  description = "Service Account ID"
  type        = string
  default     = "terraform-deployer"
}

# ============================================================================
# Service Account Creation
# ============================================================================

resource "google_service_account" "terraform_deployer" {
  account_id   = var.service_account_id
  display_name = "Terraform Deployment Service Account"
  description  = "Service account for deploying observability infrastructure via Terraform"
  project      = var.gcp_project_id
}

# ============================================================================
# IAM Role Bindings - Grant Required Permissions
# ============================================================================

# 1. Logging Admin - Create and manage log sinks
resource "google_project_iam_member" "logging_admin" {
  project = var.gcp_project_id
  role    = "roles/logging.admin"
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

# 2. Pub/Sub Admin - Create and manage Pub/Sub resources
resource "google_project_iam_member" "pubsub_admin" {
  project = var.gcp_project_id
  role    = "roles/pubsub.admin"
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

# 3. Service Account Admin - Create service accounts for OIDC
resource "google_project_iam_member" "service_account_admin" {
  project = var.gcp_project_id
  role    = "roles/iam.serviceAccountAdmin"
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

# 4. Service Account User - Use service accounts
resource "google_project_iam_member" "service_account_user" {
  project = var.gcp_project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

# 5. Secret Manager Admin - Manage secrets
resource "google_project_iam_member" "secret_manager_admin" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

# 6. Project IAM Admin - Grant IAM permissions
resource "google_project_iam_member" "project_iam_admin" {
  project = var.gcp_project_id
  role    = "roles/resourcemanager.projectIamAdmin"
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

# ============================================================================
# Service Account Key Creation
# ============================================================================

resource "google_service_account_key" "terraform_deployer_key" {
  service_account_id = google_service_account.terraform_deployer.name

  # Key will be base64 encoded in terraform state
  # We'll decode and save it in the output
}

# ============================================================================
# Outputs
# ============================================================================

output "service_account_email" {
  description = "Service Account Email"
  value       = google_service_account.terraform_deployer.email
}

output "service_account_id" {
  description = "Service Account ID"
  value       = google_service_account.terraform_deployer.account_id
}

output "service_account_key_file_content" {
  description = "Service Account Key (JSON) - SENSITIVE! Save this to a file"
  value       = base64decode(google_service_account_key.terraform_deployer_key.private_key)
  sensitive   = true
}

output "instructions" {
  description = "Next steps"
  value = <<-EOT
    ============================================================================
    Service Account Created Successfully!
    ============================================================================

    Service Account: ${google_service_account.terraform_deployer.email}

    NEXT STEPS:

    1. Save the service account key to a file:

       terraform output -raw service_account_key_file_content > terraform-sa-key.json

    2. Set environment variable:

       # Windows (PowerShell)
       $env:GOOGLE_APPLICATION_CREDENTIALS="$(pwd)\terraform-sa-key.json"

       # Linux/Mac
       export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"

    3. Navigate to main terraform directory and deploy:

       cd ../
       terraform init
       terraform apply

    ============================================================================
    SECURITY WARNING:
    - Keep terraform-sa-key.json secure and private
    - Add *.json to .gitignore
    - Do NOT commit this file to Git
    ============================================================================
  EOT
}

output "roles_granted" {
  description = "IAM Roles granted to service account"
  value = [
    "roles/logging.admin",
    "roles/pubsub.admin",
    "roles/iam.serviceAccountAdmin",
    "roles/iam.serviceAccountUser",
    "roles/secretmanager.admin",
    "roles/resourcemanager.projectIamAdmin"
  ]
}
