#!/bin/bash
# One-command deployment script
# Automatically sets credentials and deploys infrastructure

set -e

KEY_FILE="appengine-sa-key.json"

echo "============================================"
echo "GCP Log Sink Deployment"
echo "============================================"
echo ""

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "ERROR: $KEY_FILE not found!"
    echo "Please generate your service account key first."
    echo "See CLIENT_GUIDE.md Step 1"
    exit 1
fi

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "ERROR: terraform.tfvars not found!"
    echo "Please copy and configure terraform.tfvars.example"
    echo "See CLIENT_GUIDE.md Step 3"
    exit 1
fi

# Set credentials automatically
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/$KEY_FILE"
echo "[1/3] ✓ Credentials set"

# Initialize Terraform
echo "[2/3] Initializing Terraform..."
terraform init

# Deploy
echo "[3/3] Deploying infrastructure..."
terraform apply

echo ""
echo "============================================"
echo "Deployment Complete!"
echo "============================================"
