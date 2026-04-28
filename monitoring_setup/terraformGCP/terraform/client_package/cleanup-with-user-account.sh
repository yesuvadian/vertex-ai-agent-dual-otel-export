#!/bin/bash
# Cleanup script using USER account credentials (not service account)
# Deletes GCP resources created by deploy-with-user-account.sh

set -e

echo "============================================"
echo "GCP Log Sink Cleanup (User Account)"
echo "============================================"
echo ""

# Extract GCP Project ID from terraform.tfvars
PROJECT_ID=""
if [ -f "terraform.tfvars" ]; then
    PROJECT_ID=$(grep -oP 'gcp_project_id\s*=\s*"\K[^"]+' terraform.tfvars 2>/dev/null || true)
    if [ -n "$PROJECT_ID" ]; then
        echo "Using project: $PROJECT_ID"
        echo ""
    fi
fi

# Fallback: ask user if not found
if [ -z "$PROJECT_ID" ]; then
    echo "Could not find gcp_project_id in terraform.tfvars"
    read -p "Enter your GCP Project ID: " PROJECT_ID
    echo ""
fi

# Check authentication
echo "[1/5] Checking GCP authentication..."
if ! gcloud auth application-default print-access-token &>/dev/null; then
    echo "Not authenticated. Logging in..."
    gcloud auth application-default login --no-launch-browser
fi
echo "  ✓ Authenticated"

# Delete Pub/Sub Subscription
echo "[2/5] Deleting Pub/Sub subscription..."
if gcloud pubsub subscriptions delete reasoning-engine-to-lambda --project="$PROJECT_ID" --quiet 2>/dev/null; then
    echo "  ✓ Deleted"
else
    echo "  ⚠ Not found or already deleted"
fi

# Delete Pub/Sub Topic
echo "[3/5] Deleting Pub/Sub topic..."
if gcloud pubsub topics delete reasoning-engine-logs-topic --project="$PROJECT_ID" --quiet 2>/dev/null; then
    echo "  ✓ Deleted"
else
    echo "  ⚠ Not found or already deleted"
fi

# Delete Log Sink
echo "[4/5] Deleting Log Sink..."
if gcloud logging sinks delete reasoning-engine-to-pubsub --project="$PROJECT_ID" --quiet 2>/dev/null; then
    echo "  ✓ Deleted"
else
    echo "  ⚠ Not found or already deleted"
fi

# Optional: Clean Terraform state
echo "[5/5] Cleaning Terraform state..."
if [ -f "terraform.tfstate" ]; then
    echo "  Found terraform.tfstate"
    read -p "Do you want to delete Terraform state files? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f terraform.tfstate terraform.tfstate.backup
        echo "  ✓ Terraform state deleted"
    else
        echo "  ⚠ Keeping Terraform state"
    fi
else
    echo "  ⚠ No Terraform state found"
fi

echo ""
echo "============================================"
echo "Cleanup Complete!"
echo "============================================"
echo ""
echo "You can now run deploy-with-user-account.sh to redeploy"
