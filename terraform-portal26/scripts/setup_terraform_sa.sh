#!/bin/bash
# setup_terraform_sa.sh - Create Portal 26 Terraform service account
# Usage: ./setup_terraform_sa.sh <project-id>

set -e

PROJECT_ID="${1:-}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: Project ID required"
  echo "Usage: $0 <project-id>"
  echo ""
  echo "Example:"
  echo "  $0 my-gcp-project"
  exit 1
fi

SA_NAME="portal26-terraform"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="terraform-sa-key.json"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Portal 26 Terraform Service Account Setup                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Project ID:      $PROJECT_ID"
echo "Service Account: $SA_EMAIL"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  echo "❌ Error: gcloud CLI not found"
  echo "Please install: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 &> /dev/null; then
  echo "❌ Error: Not authenticated with gcloud"
  echo "Run: gcloud auth login"
  exit 1
fi

# Verify project exists
echo "🔍 Verifying project..."
if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
  echo "❌ Error: Project '$PROJECT_ID' not found or you don't have access"
  exit 1
fi

echo "✅ Project verified"
echo ""

# Check if service account already exists
if gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT_ID" &> /dev/null; then
  echo "⚠️  Service account already exists: $SA_EMAIL"
  read -p "Continue to update permissions? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
else
  # Create service account
  echo "📝 Creating service account: $SA_NAME"
  gcloud iam service-accounts create "$SA_NAME" \
    --project="$PROJECT_ID" \
    --display-name="Portal 26 Terraform" \
    --description="Deploys agents with Portal 26 telemetry"

  echo "✅ Service account created"
fi

echo ""

# Grant IAM roles
echo "🔐 Granting IAM roles..."
ROLES=(
  "roles/aiplatform.admin"
  "roles/storage.admin"
  "roles/serviceusage.serviceUsageAdmin"
  "roles/iam.serviceAccountUser"
)

for ROLE in "${ROLES[@]}"; do
  echo "  - Granting $ROLE"

  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE" \
    --condition=None \
    --quiet \
    > /dev/null 2>&1

  echo "    ✅ Granted"
done

echo ""

# Check if key file already exists
if [ -f "$KEY_FILE" ]; then
  echo "⚠️  Key file already exists: $KEY_FILE"
  read -p "Overwrite with new key? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Keeping existing key file."
    SKIP_KEY=true
  else
    rm "$KEY_FILE"
  fi
fi

if [ "$SKIP_KEY" != true ]; then
  # Create key file
  echo "🔑 Creating service account key..."
  gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID"

  echo "✅ Key created: $KEY_FILE"

  # Set secure permissions
  chmod 600 "$KEY_FILE"
  echo "✅ Key file permissions set to 600"
fi

echo ""

# Enable required APIs
echo "🔧 Enabling required APIs..."
APIS=(
  "aiplatform.googleapis.com"
  "cloudbuild.googleapis.com"
  "storage.googleapis.com"
)

for API in "${APIS[@]}"; do
  echo "  - Enabling $API"

  if gcloud services list --enabled --project="$PROJECT_ID" \
    --filter="name:$API" --format="value(name)" 2>/dev/null | grep -q "$API"; then
    echo "    ✅ Already enabled"
  else
    gcloud services enable "$API" --project="$PROJECT_ID" --quiet
    echo "    ✅ Enabled"
  fi
done

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ SERVICE ACCOUNT SETUP COMPLETE                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Service Account: $SA_EMAIL"
echo "Key File:        $KEY_FILE"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Set environment variable:"
echo "   export GOOGLE_APPLICATION_CREDENTIALS=\"\$(pwd)/$KEY_FILE\""
echo ""
echo "2. Configure Terraform:"
echo "   cd terraform"
echo "   cp terraform.tfvars.example terraform.tfvars"
echo "   nano terraform.tfvars  # Edit configuration"
echo ""
echo "3. Initialize and deploy:"
echo "   terraform init"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "⚠️  SECURITY REMINDERS:"
echo "  - Store $KEY_FILE securely (DO NOT commit to git)"
echo "  - Add to .gitignore: echo '$KEY_FILE' >> .gitignore"
echo "  - Rotate key every 90 days"
echo "  - Delete key when no longer needed"
echo ""
