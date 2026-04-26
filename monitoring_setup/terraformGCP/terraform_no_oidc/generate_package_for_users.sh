#!/bin/bash
# ============================================================================
# Generate Package for Users - Admin Script
# ============================================================================
# This script creates a package with key file for users without gcloud CLI
# Run this as admin to prepare files for distribution to users
# ============================================================================

set -e

PROJECT_ID="agentic-ai-integration-490716"
SA_EMAIL="agentic-ai-integration-490716@appspot.gserviceaccount.com"
KEY_FILE="appengine-sa-key.json"
PACKAGE_NAME="terraform-gcp-setup-$(date +%Y%m%d).zip"

echo "============================================================================"
echo "Generate Terraform Package for Users (No gcloud CLI required)"
echo "============================================================================"
echo "Project: $PROJECT_ID"
echo "Service Account: $SA_EMAIL"
echo ""

# Step 1: Check if you're authenticated
echo "[1/5] Checking authentication..."
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [ -z "$CURRENT_ACCOUNT" ]; then
    echo "[ERROR] Not authenticated to GCP"
    echo "Run: gcloud auth login"
    exit 1
fi
echo "[OK] Authenticated as: $CURRENT_ACCOUNT"

# Step 2: Create service account key
echo "[2/5] Creating service account key..."
if [ -f "$KEY_FILE" ]; then
    echo "[WARN] Key file already exists: $KEY_FILE"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Using existing key file"
    else
        rm "$KEY_FILE"
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SA_EMAIL" \
            --project="$PROJECT_ID"
        echo "[OK] New key file created"
    fi
else
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL" \
        --project="$PROJECT_ID"
    echo "[OK] Key file created: $KEY_FILE"
fi

# Step 3: Verify service account has Editor role
echo "[3/5] Verifying service account permissions..."
HAS_EDITOR=$(gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SA_EMAIL AND bindings.role:roles/editor" \
    --format="value(bindings.role)" 2>/dev/null)

if [ "$HAS_EDITOR" == "roles/editor" ]; then
    echo "[OK] Service account has Editor role"
else
    echo "[WARN] Service account may not have Editor role"
    echo "[INFO] Required role: roles/editor"
fi

# Step 4: Create package directory
echo "[4/5] Creating package..."
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/terraform_no_oidc"
mkdir -p "$PACKAGE_DIR"

# Copy necessary files
cp main.tf "$PACKAGE_DIR/"
cp gcp_log_sink_pubsub.tf "$PACKAGE_DIR/"
cp terraform.tfvars.example "$PACKAGE_DIR/"
cp "$KEY_FILE" "$PACKAGE_DIR/"
cp README_FOR_USERS.md "$PACKAGE_DIR/README.md"

# Create a quick start guide
cat > "$PACKAGE_DIR/QUICK_START.txt" << 'EOF'
========================================================================================
TERRAFORM GCP SETUP - QUICK START
========================================================================================

PREREQUISITES:
- Terraform installed (terraform --version)
- This package contains everything you need (no gcloud CLI needed)

SETUP STEPS:

1. Set Authentication (choose your OS):

   Linux/Mac:
   export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"

   Windows PowerShell:
   $env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"

   Windows CMD:
   set GOOGLE_APPLICATION_CREDENTIALS=%cd%\appengine-sa-key.json

2. Create Configuration:
   cp terraform.tfvars.example terraform.tfvars

   Edit terraform.tfvars and update:
   - aws_lambda_url (your Lambda URL)
   - reasoning_engine_ids (your reasoning engine IDs)

3. Deploy:
   terraform init
   terraform plan
   terraform apply    (type 'yes')

4. Cleanup (when done):
   terraform destroy  (type 'yes')

For detailed instructions, see README.md

IMPORTANT:
- Keep appengine-sa-key.json secure
- Never commit it to git
- Set GOOGLE_APPLICATION_CREDENTIALS every time you open a new terminal

========================================================================================
EOF

# Step 5: Create zip package
echo "[5/5] Creating zip package..."
cd "$TEMP_DIR"
zip -r "$PACKAGE_NAME" terraform_no_oidc/ >/dev/null 2>&1
mv "$PACKAGE_NAME" "$OLDPWD/"
cd "$OLDPWD"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "============================================================================"
echo "Package Created Successfully!"
echo "============================================================================"
echo ""
echo "Package: $PACKAGE_NAME"
echo "Contains:"
echo "  - Terraform configuration files"
echo "  - Service account key: $KEY_FILE"
echo "  - README.md (user instructions)"
echo "  - QUICK_START.txt (quick reference)"
echo ""
echo "Service Account Details:"
echo "  Email: $SA_EMAIL"
echo "  Role: Editor (full GCP access)"
echo "  Project: $PROJECT_ID"
echo ""
echo "Distribution:"
echo "  1. Share $PACKAGE_NAME with users"
echo "  2. Users extract and follow QUICK_START.txt"
echo "  3. No gcloud CLI needed - just Terraform!"
echo ""
echo "Security Notes:"
echo "  - Package contains sensitive key file"
echo "  - Share via secure channel (encrypted email, secure file transfer)"
echo "  - Consider password-protecting the zip:"
echo "    zip -e $PACKAGE_NAME terraform_no_oidc/"
echo "  - Rotate key periodically"
echo ""
echo "Key File Management:"
echo "  - Keep a backup of $KEY_FILE"
echo "  - To revoke: gcloud iam service-accounts keys delete KEY_ID \\"
echo "              --iam-account=$SA_EMAIL"
echo "  - To create new: gcloud iam service-accounts keys create new-key.json \\"
echo "                  --iam-account=$SA_EMAIL"
echo ""
