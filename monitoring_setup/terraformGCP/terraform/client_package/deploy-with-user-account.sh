#!/bin/bash
# Deployment script using USER account credentials (not service account)
# Run this when you want to use your own GCP login instead of service account

set -e

echo "============================================"
echo "GCP Log Sink Deployment (User Account)"
echo "============================================"
echo ""

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "ERROR: terraform.tfvars not found!"
    echo "Please copy and configure terraform.tfvars.example"
    echo "See CLIENT_GUIDE.md Step 2"
    exit 1
fi

# Use user's gcloud credentials (not service account key)
echo "[1/4] Authenticating with your GCP account..."
gcloud auth application-default login --no-launch-browser

echo "[2/4] Credentials set from your GCP login"

# Initialize Terraform
echo "[3/4] Initializing Terraform..."
terraform init

# Deploy
echo "[4/4] Deploying infrastructure..."
terraform apply

echo ""
echo "============================================"
echo "Deployment Complete!"
echo "============================================"
