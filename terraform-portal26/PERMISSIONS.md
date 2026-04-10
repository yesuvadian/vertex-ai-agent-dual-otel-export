# Permission Requirements

Complete guide to GCP IAM permissions required for Portal 26 integration.

## Table of Contents

- [Overview](#overview)
- [Quick Start: Minimum Permissions](#quick-start-minimum-permissions)
- [Deployment Approach Permissions](#deployment-approach-permissions)
- [Service Account Setup](#service-account-setup)
- [Detailed Permission Breakdown](#detailed-permission-breakdown)
- [CI/CD Permissions](#cicd-permissions)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

Different deployment approaches require different permission sets:

| Approach | Required Permissions | Complexity |
|----------|---------------------|------------|
| **Approach 1: One-Time Injection** | Vertex AI + Storage (Basic) | Low |
| **Approach 2: Automatic Terraform** | Vertex AI + Storage + Service APIs | Medium |
| **CI/CD Pipeline** | All above + Service Account impersonation | High |

---

## Quick Start: Minimum Permissions

### For Individual Developers (Approach 1)

```bash
# Grant to your user account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/storage.objectAdmin"
```

### For Terraform Service Account (Approach 2)

```bash
# Create service account
gcloud iam service-accounts create portal26-deployer \
  --display-name="Portal 26 Terraform Deployer"

# Grant required roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:portal26-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:portal26-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:portal26-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageAdmin"
```

---

## Deployment Approach Permissions

### Approach 1: One-Time Injection (Commit Code)

**Who needs permissions:** Developer running injection script locally

**Required GCP Roles:**

```yaml
roles/aiplatform.user:
  - aiplatform.agents.create
  - aiplatform.agents.update
  - aiplatform.agents.get
  - aiplatform.agents.list

roles/storage.objectAdmin:
  - storage.objects.create
  - storage.objects.delete
  - storage.objects.get
  - storage.objects.list
  # For Cloud Build staging buckets

roles/cloudbuild.builds.viewer:
  - cloudbuild.builds.get
  - cloudbuild.builds.list
  # To monitor deployment progress
```

**Setup:**

```bash
# Grant to your user
USER_EMAIL="developer@example.com"
PROJECT_ID="your-project-id"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/cloudbuild.builds.viewer"
```

**Duration:** Permanent (or until deployment complete)

---

### Approach 2: Automatic Terraform Injection

**Who needs permissions:** Terraform service account

**Required GCP Roles:**

```yaml
roles/aiplatform.admin:
  - aiplatform.agents.* (all operations)
  - aiplatform.models.*
  - aiplatform.endpoints.*

roles/storage.admin:
  - storage.* (all storage operations)
  # Terraform needs to manage staging buckets

roles/serviceusage.serviceUsageAdmin:
  - serviceusage.services.enable
  - serviceusage.services.disable
  - serviceusage.services.get
  - serviceusage.services.list
  # To enable required APIs automatically

roles/iam.serviceAccountUser:
  - iam.serviceAccounts.actAs
  # To deploy as default compute service account
```

**Setup:**

```bash
# Create dedicated service account
SA_NAME="portal26-terraform"
PROJECT_ID="your-project-id"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
  --display-name="Portal 26 Terraform Deployer" \
  --description="Service account for automated Portal 26 agent deployments"

# Grant roles
for ROLE in \
  "roles/aiplatform.admin" \
  "roles/storage.admin" \
  "roles/serviceusage.serviceUsageAdmin" \
  "roles/iam.serviceAccountUser"
do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE"
done

# Create and download key (for local Terraform)
gcloud iam service-accounts keys create terraform-key.json \
  --iam-account=$SA_EMAIL

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-key.json"
```

**Terraform Configuration:**

```hcl
# terraform/main.tf
provider "google" {
  project = var.project_id
  region  = var.region
  
  # Uses GOOGLE_APPLICATION_CREDENTIALS environment variable
  # Or specify key file:
  # credentials = file("terraform-key.json")
}
```

**Duration:** Permanent (service account active as long as needed)

---

## Service Account Setup

### Step-by-Step: Create Terraform Service Account

```bash
#!/bin/bash
# setup_terraform_sa.sh - Create Portal 26 Terraform service account

PROJECT_ID="your-project-id"
SA_NAME="portal26-terraform"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 1. Create service account
echo "Creating service account: $SA_NAME"
gcloud iam service-accounts create $SA_NAME \
  --project=$PROJECT_ID \
  --display-name="Portal 26 Terraform" \
  --description="Deploys agents with Portal 26 telemetry"

# 2. Grant IAM roles
echo "Granting IAM roles..."
ROLES=(
  "roles/aiplatform.admin"
  "roles/storage.admin"
  "roles/serviceusage.serviceUsageAdmin"
  "roles/iam.serviceAccountUser"
)

for ROLE in "${ROLES[@]}"; do
  echo "  - $ROLE"
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE" \
    --condition=None
done

# 3. Create key file
echo "Creating service account key..."
gcloud iam service-accounts keys create terraform-sa-key.json \
  --iam-account=$SA_EMAIL \
  --project=$PROJECT_ID

echo "✅ Service account setup complete!"
echo ""
echo "Next steps:"
echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"\$(pwd)/terraform-sa-key.json\""
echo "  cd terraform && terraform init"
```

**Run:**

```bash
chmod +x setup_terraform_sa.sh
./setup_terraform_sa.sh
```

---

## Detailed Permission Breakdown

### Required APIs

These APIs must be enabled in your GCP project:

```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  --project=PROJECT_ID
```

**API Enablement Permissions:**

- `serviceusage.services.enable` (included in `roles/serviceusage.serviceUsageAdmin`)

**Terraform handles this automatically** if the service account has `roles/serviceusage.serviceUsageAdmin`.

---

### Vertex AI Permissions

**For Agent Deployment:**

```yaml
# Minimum permissions for creating/updating agents
aiplatform.agents.create
aiplatform.agents.update
aiplatform.agents.get
aiplatform.agents.list
aiplatform.agents.delete  # Optional, for cleanup

# Agent Engine specific
aiplatform.agentEngines.create
aiplatform.agentEngines.update
aiplatform.agentEngines.get
aiplatform.agentEngines.list

# For viewing deployment status
aiplatform.operations.get
aiplatform.operations.list
```

**Included in Standard Roles:**

- `roles/aiplatform.user` - Minimum for deploying agents
- `roles/aiplatform.admin` - Full control (recommended for Terraform)

---

### Cloud Storage Permissions

**Why needed:** Vertex AI Agent Engine uses Cloud Build, which stages files in GCS.

```yaml
# Minimum permissions
storage.buckets.get
storage.buckets.list
storage.objects.create
storage.objects.delete
storage.objects.get
storage.objects.list

# Staging bucket access
storage.buckets.create  # If Terraform manages buckets
```

**Included in Standard Roles:**

- `roles/storage.objectAdmin` - Minimum for deployments
- `roles/storage.admin` - Full control (recommended for Terraform)

**Typical Staging Bucket Pattern:**

```
gs://[PROJECT_ID]_cloudbuild/
gs://[PROJECT_ID]-gcf-staging/
```

---

### Service Account Impersonation

**Why needed:** Vertex AI deployments run as a service account.

```yaml
iam.serviceAccounts.actAs
iam.serviceAccounts.get
iam.serviceAccounts.list
```

**Included in:**

- `roles/iam.serviceAccountUser`

**Which service account?**

- Default: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`
- Custom: Specify in deployment configuration

---

## CI/CD Permissions

### GitHub Actions Setup

**Service Account:**

```bash
# Create CI/CD service account
SA_NAME="portal26-cicd"
PROJECT_ID="your-project-id"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
  --display-name="Portal 26 CI/CD Pipeline"

# Grant roles (same as Terraform SA)
for ROLE in \
  "roles/aiplatform.admin" \
  "roles/storage.admin" \
  "roles/serviceusage.serviceUsageAdmin" \
  "roles/iam.serviceAccountUser"
do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE"
done

# Create key for GitHub Secrets
gcloud iam service-accounts keys create cicd-key.json \
  --iam-account=$SA_EMAIL

# Base64 encode for GitHub Secret
cat cicd-key.json | base64 > cicd-key-base64.txt
```

**GitHub Secrets:**

```yaml
# .github/workflows/deploy.yml
name: Deploy Agents with Portal 26

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}  # Base64 decoded key
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      
      - name: Deploy with Terraform
        run: |
          cd terraform
          terraform init
          terraform apply -auto-approve
```

**Required GitHub Secrets:**

- `GCP_SA_KEY` - Service account JSON key (base64 encoded)
- `GCP_PROJECT_ID` - Your project ID
- `PORTAL26_ENDPOINT` - Portal 26 endpoint URL

---

### GitLab CI Setup

```yaml
# .gitlab-ci.yml
deploy:
  image: google/cloud-sdk:alpine
  stage: deploy
  script:
    - echo $GCP_SA_KEY | base64 -d > /tmp/sa-key.json
    - export GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa-key.json
    - gcloud config set project $GCP_PROJECT_ID
    - cd terraform
    - terraform init
    - terraform apply -auto-approve
  only:
    - main
```

**GitLab CI/CD Variables:**

- `GCP_SA_KEY` (File, Protected)
- `GCP_PROJECT_ID`
- `PORTAL26_ENDPOINT`

---

## Security Best Practices

### 1. Principle of Least Privilege

**Use predefined roles when possible:**

```bash
# ❌ DON'T grant Editor or Owner
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/editor"  # Too broad!

# ✅ DO grant specific roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/aiplatform.admin"  # Scoped to Vertex AI
```

### 2. Custom Role (Advanced)

For production, create a custom role with only required permissions:

```bash
# Create custom role
gcloud iam roles create portal26Deployer \
  --project=PROJECT_ID \
  --title="Portal 26 Agent Deployer" \
  --description="Minimum permissions for Portal 26 agent deployment" \
  --permissions="\
aiplatform.agents.create,\
aiplatform.agents.update,\
aiplatform.agents.get,\
aiplatform.agents.list,\
aiplatform.operations.get,\
storage.buckets.get,\
storage.objects.create,\
storage.objects.delete,\
storage.objects.get,\
storage.objects.list,\
iam.serviceAccounts.actAs" \
  --stage=GA

# Grant custom role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA_EMAIL" \
  --role="projects/PROJECT_ID/roles/portal26Deployer"
```

### 3. Time-Limited Access

**For external consultants/partners:**

```bash
# Grant temporary access (expires in 30 days)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:consultant@external.com" \
  --role="roles/aiplatform.user" \
  --condition='expression=request.time < timestamp("2026-05-09T00:00:00Z"),title=30-day-access'
```

### 4. Service Account Key Rotation

```bash
# List existing keys
gcloud iam service-accounts keys list \
  --iam-account=SA_EMAIL

# Create new key
gcloud iam service-accounts keys create new-key.json \
  --iam-account=SA_EMAIL

# Update GitHub/GitLab secrets with new key

# Delete old key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=SA_EMAIL
```

**Recommendation:** Rotate keys every 90 days.

### 5. Audit Logging

**Enable Cloud Audit Logs:**

```bash
# View who deployed agents
gcloud logging read "protoPayload.serviceName=\"aiplatform.googleapis.com\"" \
  --project=PROJECT_ID \
  --format=json \
  --limit=50
```

### 6. Workload Identity (GKE)

If deploying from GKE, use Workload Identity instead of keys:

```bash
# Bind Kubernetes service account to GCP service account
gcloud iam service-accounts add-iam-policy-binding SA_EMAIL \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]"
```

---

## Organization Policy Constraints

### Required Policy Exemptions

Some organizations restrict service account key creation:

```bash
# Check if key creation is restricted
gcloud resource-manager org-policies describe \
  constraints/iam.disableServiceAccountKeyCreation \
  --project=PROJECT_ID

# If restricted, request exemption or use Workload Identity
```

### API Restrictions

```bash
# Check if Vertex AI API is allowed
gcloud resource-manager org-policies describe \
  constraints/serviceuser.services \
  --project=PROJECT_ID
```

---

## Troubleshooting

### Error: "Permission denied on resource project"

**Cause:** Missing `resourcemanager.projects.get` permission

**Solution:**

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/viewer"  # Adds project-level read access
```

### Error: "User does not have permission to access service"

**Cause:** API not enabled

**Solution:**

```bash
gcloud services enable aiplatform.googleapis.com --project=PROJECT_ID
```

### Error: "Service account does not have permission to act as"

**Cause:** Missing `iam.serviceAccounts.actAs`

**Solution:**

```bash
# Grant on the target service account (usually default compute SA)
TARGET_SA="PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud iam service-accounts add-iam-policy-binding $TARGET_SA \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/iam.serviceAccountUser" \
  --project=PROJECT_ID
```

### Error: "Caller does not have storage.objects.create permission"

**Cause:** Missing Cloud Storage permissions

**Solution:**

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/storage.objectAdmin"
```

### Permission Verification Script

```bash
#!/bin/bash
# verify_permissions.sh - Check if service account has required permissions

SA_EMAIL="$1"
PROJECT_ID="$2"

if [ -z "$SA_EMAIL" ] || [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <service-account-email> <project-id>"
  exit 1
fi

echo "Checking permissions for: $SA_EMAIL"
echo "Project: $PROJECT_ID"
echo ""

REQUIRED_ROLES=(
  "roles/aiplatform.admin"
  "roles/storage.admin"
  "roles/iam.serviceAccountUser"
)

for ROLE in "${REQUIRED_ROLES[@]}"; do
  echo -n "Checking $ROLE... "
  
  if gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SA_EMAIL AND bindings.role:$ROLE" \
    --format="value(bindings.role)" | grep -q "$ROLE"; then
    echo "✅ GRANTED"
  else
    echo "❌ MISSING"
  fi
done

echo ""
echo "Checking API enablement..."
REQUIRED_APIS=(
  "aiplatform.googleapis.com"
  "cloudbuild.googleapis.com"
  "storage.googleapis.com"
)

for API in "${REQUIRED_APIS[@]}"; do
  echo -n "  $API... "
  if gcloud services list --enabled --project=$PROJECT_ID --filter="name:$API" --format="value(name)" | grep -q "$API"; then
    echo "✅ ENABLED"
  else
    echo "❌ DISABLED"
  fi
done
```

**Usage:**

```bash
chmod +x verify_permissions.sh
./verify_permissions.sh portal26-terraform@PROJECT_ID.iam.gserviceaccount.com PROJECT_ID
```

---

## Summary

### Minimum Permissions Checklist

**For Approach 1 (One-Time Injection):**
- [ ] `roles/aiplatform.user` or custom role with agent permissions
- [ ] `roles/storage.objectAdmin`
- [ ] APIs enabled: `aiplatform.googleapis.com`, `storage.googleapis.com`

**For Approach 2 (Terraform):**
- [ ] Service account created
- [ ] `roles/aiplatform.admin` granted
- [ ] `roles/storage.admin` granted
- [ ] `roles/serviceusage.serviceUsageAdmin` granted
- [ ] `roles/iam.serviceAccountUser` granted
- [ ] Service account key created and secured
- [ ] APIs enabled (or SA can enable them)

**For CI/CD:**
- [ ] Same as Approach 2
- [ ] Key stored in CI/CD secrets
- [ ] Key rotation schedule established (90 days)
- [ ] Audit logging enabled

### Permission Matrix

| Operation | User Role | Terraform SA | CI/CD SA |
|-----------|-----------|--------------|----------|
| Deploy agents | `aiplatform.user` | `aiplatform.admin` | `aiplatform.admin` |
| Manage storage | `storage.objectAdmin` | `storage.admin` | `storage.admin` |
| Enable APIs | Manual | `serviceusage.admin` | `serviceusage.admin` |
| Impersonate SA | `iam.serviceAccountUser` | `iam.serviceAccountUser` | `iam.serviceAccountUser` |

---

## Additional Resources

- [GCP IAM Roles Documentation](https://cloud.google.com/iam/docs/understanding-roles)
- [Vertex AI IAM Permissions](https://cloud.google.com/vertex-ai/docs/general/access-control)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)

---

## Support

If you encounter permission issues not covered here:

1. Run the `verify_permissions.sh` script
2. Check Cloud Audit Logs for denied requests
3. Review organization policies for restrictions
4. Contact your GCP administrator for policy exemptions
