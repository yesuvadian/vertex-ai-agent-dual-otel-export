#!/bin/bash
# ============================================================================
# Setup Script - Using Existing App Engine Service Account
# ============================================================================
# Uses: agentic-ai-integration-490716@appspot.gserviceaccount.com (Editor role)
# No need to create new service account!
# ============================================================================

set -e

PROJECT_ID="agentic-ai-integration-490716"
SA_EMAIL="agentic-ai-integration-490716@appspot.gserviceaccount.com"
KEY_FILE="appengine-sa-key.json"

echo "============================================================================"
echo "Terraform Setup - Using Existing App Engine Service Account"
echo "============================================================================"
echo "Project: $PROJECT_ID"
echo "Service Account: $SA_EMAIL"
echo ""

# Step 1: Check if key file already exists
if [ -f "$KEY_FILE" ]; then
    echo "[1/5] ✓ Key file already exists: $KEY_FILE"
else
    echo "[1/5] Creating service account key..."
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL" \
        --project="$PROJECT_ID"
    echo "[OK] Key file created: $KEY_FILE"
fi

# Step 2: Set authentication
echo "[2/5] Setting authentication..."
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/$KEY_FILE"
echo "[OK] GOOGLE_APPLICATION_CREDENTIALS set"

# Step 3: Verify authentication
echo "[3/5] Verifying authentication..."
AUTH_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [[ "$AUTH_ACCOUNT" == *"appspot"* ]]; then
    echo "[OK] Authenticated as: $AUTH_ACCOUNT"
else
    echo "[WARN] Active account: $AUTH_ACCOUNT"
    echo "[INFO] Activating service account..."
    gcloud auth activate-service-account --key-file="$KEY_FILE"
fi

# Step 4: Create terraform.tfvars if needed
echo "[4/5] Checking terraform.tfvars..."
if [ ! -f "terraform.tfvars" ]; then
    cp terraform.tfvars.example terraform.tfvars
    echo "[OK] Created terraform.tfvars from example"
    echo ""
    echo "⚠️  IMPORTANT: Edit terraform.tfvars before running terraform apply!"
    echo ""
    echo "Update these values:"
    echo "  - aws_lambda_url         (your Lambda URL)"
    echo "  - reasoning_engine_ids   (your reasoning engine IDs)"
    echo "  - log_severity_filter    (optional, for cost savings)"
    echo ""
    echo "Then run:"
    echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"\$(pwd)/$KEY_FILE\""
    echo "  terraform init"
    echo "  terraform plan"
    echo "  terraform apply"
    echo ""
    exit 0
else
    echo "[OK] terraform.tfvars already exists"
fi

# Step 5: Check if Terraform is initialized
echo "[5/5] Checking Terraform initialization..."
if [ ! -d ".terraform" ]; then
    echo "[INFO] Terraform not initialized. Run: terraform init"
else
    echo "[OK] Terraform already initialized"
fi

echo ""
echo "============================================================================"
echo "Setup Complete!"
echo "============================================================================"
echo ""
echo "Service Account: $SA_EMAIL"
echo "Key File: $KEY_FILE"
echo "Authentication: GOOGLE_APPLICATION_CREDENTIALS is set"
echo ""
echo "Next Steps:"
echo "  1. Edit terraform.tfvars (if not done)"
echo "  2. Run: export GOOGLE_APPLICATION_CREDENTIALS=\"\$(pwd)/$KEY_FILE\""
echo "  3. Run: terraform init"
echo "  4. Run: terraform plan"
echo "  5. Run: terraform apply"
echo ""
echo "To use this authentication in future sessions:"
echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"$(pwd)/$KEY_FILE\""
echo ""
