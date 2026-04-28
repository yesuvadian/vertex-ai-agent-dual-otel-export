#!/bin/bash
# ============================================================================
# GCP Log Sink Deployment Script - User Account Authentication
# ============================================================================
# This script deploys the GCP log forwarding infrastructure using your
# user account credentials instead of a service account key file.
# ============================================================================

set -e

echo "========================================"
echo "GCP Log Sink Deployment - User Account"
echo "========================================"
echo ""

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "ERROR: terraform.tfvars not found!"
    echo "Please copy terraform.tfvars.example to terraform.tfvars and configure it."
    exit 1
fi

# Extract project ID from terraform.tfvars
PROJECT_ID=$(grep 'gcp_project_id' terraform.tfvars | sed 's/.*"\(.*\)".*/\1/')

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "YOUR-GCP-PROJECT-ID" ]; then
    echo "ERROR: Please configure gcp_project_id in terraform.tfvars"
    exit 1
fi

echo "Project ID: $PROJECT_ID"
echo ""

# Check if gcloud is installed
echo "Checking gcloud CLI..."
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI not found!"
    echo "Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo "✓ gcloud CLI found"
echo ""

# Authenticate with user account
echo "Authenticating with Google Cloud..."
echo "A browser window will open for authentication."
echo ""

gcloud auth application-default login --project="$PROJECT_ID"

echo "✓ Authentication successful"
echo ""

# Set the project
echo "Setting GCP project to: $PROJECT_ID"
gcloud config set project "$PROJECT_ID" > /dev/null 2>&1

echo "✓ Project set"
echo ""

# Temporarily rename service account key file if it exists
KEY_FILE_RENAMED=false
if [ -f "appengine-sa-key.json" ]; then
    echo "Temporarily renaming appengine-sa-key.json..."
    mv appengine-sa-key.json appengine-sa-key.json.backup
    KEY_FILE_RENAMED=true
fi

# Backup main.tf
echo "Updating main.tf to use user account credentials..."
cp main.tf main.tf.backup

# Comment out the credentials line
sed -i.tmp 's/^\(\s*credentials\s*=\s*file("appengine-sa-key\.json")\)/  # credentials = file("appengine-sa-key.json")  # Using user account/' main.tf
rm -f main.tf.tmp

echo "✓ main.tf updated"
echo ""

# Function to restore files on error
restore_files() {
    echo "Restoring original files..."
    if [ -f "main.tf.backup" ]; then
        mv main.tf.backup main.tf
    fi
    if [ "$KEY_FILE_RENAMED" = true ]; then
        mv appengine-sa-key.json.backup appengine-sa-key.json
    fi
}

# Set trap to restore files on error
trap restore_files EXIT

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

echo "✓ Terraform initialized"
echo ""

# Plan deployment
echo "Planning deployment..."
terraform plan

echo ""
echo "========================================"
echo "Ready to deploy!"
echo "========================================"
echo ""
echo -n "Review the plan above. Do you want to proceed? (yes/no): "
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    restore_files
    trap - EXIT
    exit 0
fi

# Apply deployment
echo ""
echo "Deploying infrastructure..."
terraform apply -auto-approve

# Restore main.tf
echo ""
echo "Restoring main.tf..."
mv main.tf.backup main.tf

# Restore key file if it was renamed
if [ "$KEY_FILE_RENAMED" = true ]; then
    mv appengine-sa-key.json.backup appengine-sa-key.json
fi

# Clear trap
trap - EXIT

echo ""
echo "========================================"
echo "✓ Deployment Complete!"
echo "========================================"
echo ""
echo "Next Steps:"
echo "1. Check the outputs above for resource details"
echo "2. Test by generating logs in your Reasoning Engine"
echo "3. Verify logs are flowing to your destination endpoint"
echo ""
