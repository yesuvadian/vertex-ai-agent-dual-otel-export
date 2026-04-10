#!/bin/bash
# verify_permissions.sh - Check if service account has required permissions
# Usage: ./verify_permissions.sh <service-account-email> <project-id>

set -e

SA_EMAIL="${1:-}"
PROJECT_ID="${2:-}"

if [ -z "$SA_EMAIL" ] || [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: Missing required arguments"
  echo ""
  echo "Usage: $0 <service-account-email> <project-id>"
  echo ""
  echo "Example:"
  echo "  $0 portal26-terraform@my-project.iam.gserviceaccount.com my-project"
  exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Portal 26 Permission Verification                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Service Account: $SA_EMAIL"
echo "Project:         $PROJECT_ID"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  echo "❌ Error: gcloud CLI not found"
  exit 1
fi

# Verify service account exists
echo "🔍 Verifying service account..."
if ! gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT_ID" &> /dev/null; then
  echo "❌ Error: Service account not found or inaccessible"
  exit 1
fi
echo "✅ Service account exists"
echo ""

# Check IAM roles
echo "🔐 Checking IAM Roles:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REQUIRED_ROLES=(
  "roles/aiplatform.admin:Vertex AI Admin"
  "roles/storage.admin:Storage Admin"
  "roles/iam.serviceAccountUser:Service Account User"
  "roles/serviceusage.serviceUsageAdmin:Service Usage Admin"
)

ALL_GRANTED=true

for ROLE_DESC in "${REQUIRED_ROLES[@]}"; do
  ROLE="${ROLE_DESC%%:*}"
  DESC="${ROLE_DESC##*:}"

  printf "  %-45s " "$DESC ($ROLE)"

  if gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SA_EMAIL AND bindings.role:$ROLE" \
    --format="value(bindings.role)" 2>/dev/null | grep -q "$ROLE"; then
    echo "✅ GRANTED"
  else
    echo "❌ MISSING"
    ALL_GRANTED=false
  fi
done

echo ""

# Check API enablement
echo "🔧 Checking Required APIs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REQUIRED_APIS=(
  "aiplatform.googleapis.com:Vertex AI API"
  "cloudbuild.googleapis.com:Cloud Build API"
  "storage.googleapis.com:Cloud Storage API"
)

ALL_ENABLED=true

for API_DESC in "${REQUIRED_APIS[@]}"; do
  API="${API_DESC%%:*}"
  DESC="${API_DESC##*:}"

  printf "  %-45s " "$DESC ($API)"

  if gcloud services list --enabled --project="$PROJECT_ID" \
    --filter="name:$API" --format="value(name)" 2>/dev/null | grep -q "$API"; then
    echo "✅ ENABLED"
  else
    echo "❌ DISABLED"
    ALL_ENABLED=false
  fi
done

echo ""

# Check service account keys
echo "🔑 Checking Service Account Keys:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

KEYS=$(gcloud iam service-accounts keys list \
  --iam-account="$SA_EMAIL" \
  --project="$PROJECT_ID" \
  --filter="keyType:USER_MANAGED" \
  --format="table[no-heading](name,validAfterTime)" 2>/dev/null)

if [ -z "$KEYS" ]; then
  echo "  ⚠️  No user-managed keys found"
  echo "  Run: gcloud iam service-accounts keys create key.json \\"
  echo "         --iam-account=$SA_EMAIL"
else
  KEY_COUNT=$(echo "$KEYS" | wc -l)
  echo "  ✅ $KEY_COUNT user-managed key(s) found:"
  echo ""
  echo "$KEYS" | while IFS= read -r line; do
    KEY_ID=$(echo "$line" | awk '{print $1}' | rev | cut -d'/' -f1 | rev)
    CREATED=$(echo "$line" | awk '{print $2}')

    # Calculate age
    if command -v date &> /dev/null; then
      if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        CREATED_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${CREATED:0:19}" +%s 2>/dev/null || echo 0)
      else
        # Linux
        CREATED_TS=$(date -d "$CREATED" +%s 2>/dev/null || echo 0)
      fi

      NOW_TS=$(date +%s)
      AGE_DAYS=$(( (NOW_TS - CREATED_TS) / 86400 ))

      if [ "$AGE_DAYS" -gt 90 ]; then
        AGE_WARN="⚠️  $AGE_DAYS days old (rotate recommended)"
      else
        AGE_WARN="$AGE_DAYS days old"
      fi
    else
      AGE_WARN="created $CREATED"
    fi

    echo "    - $KEY_ID ($AGE_WARN)"
  done
fi

echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  VERIFICATION SUMMARY                                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if [ "$ALL_GRANTED" = true ] && [ "$ALL_ENABLED" = true ]; then
  echo "✅ All checks passed!"
  echo ""
  echo "Service account is properly configured for Portal 26 deployment."
  echo ""
  echo "📋 Next Steps:"
  echo "  1. Export credentials: export GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json"
  echo "  2. Configure Terraform: cd terraform && cp terraform.tfvars.example terraform.tfvars"
  echo "  3. Deploy: terraform init && terraform apply"
  exit 0
else
  echo "❌ Configuration incomplete"
  echo ""

  if [ "$ALL_GRANTED" = false ]; then
    echo "Missing IAM roles. To fix:"
    echo ""
    echo "  # Grant missing roles"
    for ROLE_DESC in "${REQUIRED_ROLES[@]}"; do
      ROLE="${ROLE_DESC%%:*}"
      echo "  gcloud projects add-iam-policy-binding $PROJECT_ID \\"
      echo "    --member=\"serviceAccount:$SA_EMAIL\" \\"
      echo "    --role=\"$ROLE\""
    done
    echo ""
  fi

  if [ "$ALL_ENABLED" = false ]; then
    echo "Missing APIs. To fix:"
    echo ""
    echo "  # Enable missing APIs"
    echo "  gcloud services enable \\"
    for API_DESC in "${REQUIRED_APIS[@]}"; do
      API="${API_DESC%%:*}"
      echo "    $API \\"
    done
    echo "    --project=$PROJECT_ID"
    echo ""
  fi

  echo "Or run the setup script to configure everything automatically:"
  echo "  ./scripts/setup_terraform_sa.sh $PROJECT_ID"

  exit 1
fi
