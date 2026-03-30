# Terraform Configuration for AI Agent

Infrastructure as Code (IaC) for deploying the AI Agent to Google Cloud Run.

## 🎯 What This Creates

When you run `terraform apply`, it automatically creates:

- ✅ **Cloud Run Service** - Serverless AI agent deployment
- ✅ **Secret Manager Secrets** - Secure storage for API keys
- ✅ **Service Account** - Dedicated identity with minimal permissions
- ✅ **IAM Bindings** - Proper access controls
- ✅ **API Enablement** - All required Google Cloud APIs

## 📋 Prerequisites

### 1. Install Terraform

**Windows (Chocolatey):**
```bash
choco install terraform
```

**Mac (Homebrew):**
```bash
brew install terraform
```

**Linux:**
```bash
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**Verify installation:**
```bash
terraform version
```

### 2. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project agentic-ai-integration-490716
```

### 3. Build Container Image

Before deploying with Terraform, build your container:

```bash
cd ..
gcloud builds submit --tag gcr.io/agentic-ai-integration-490716/ai-agent
```

## 🚀 Quick Start (5 Minutes)

### Step 1: Create Variables File

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

### Step 2: Edit terraform.tfvars

Open `terraform.tfvars` and fill in your secrets:

```hcl
gemini_api_key  = "AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8"
otel_auth_header = "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="
```

**⚠️ NEVER commit terraform.tfvars to Git!** (It's already in .gitignore)

### Step 3: Initialize Terraform

```bash
terraform init
```

This downloads the Google Cloud provider and prepares Terraform.

### Step 4: Preview Changes

```bash
terraform plan
```

Review what Terraform will create. You should see:
- 6 resources to add
- 0 resources to change
- 0 resources to destroy

### Step 5: Deploy!

```bash
terraform apply
```

Type `yes` when prompted.

**Deployment takes ~2-3 minutes.**

### Step 6: Get Service URL

```bash
terraform output service_url
```

## 📊 Terraform Commands Reference

### Basic Commands

```bash
# Initialize (first time only)
terraform init

# Format code
terraform fmt

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Apply changes
terraform apply

# Destroy all resources
terraform destroy

# Show current state
terraform show

# List all resources
terraform state list

# View outputs
terraform output
```

### Useful Workflows

```bash
# Deploy without confirmation prompt
terraform apply -auto-approve

# Deploy specific resource
terraform apply -target=google_cloud_run_v2_service.ai_agent

# Refresh state
terraform refresh

# Generate dependency graph
terraform graph | dot -Tpng > graph.png
```

## 🔄 Updating Your Deployment

### Update Container Image

1. Build new image:
```bash
cd ..
gcloud builds submit --tag gcr.io/agentic-ai-integration-490716/ai-agent
```

2. Update Terraform:
```bash
cd terraform
terraform apply
```

Terraform will detect the new image and update the service.

### Update Environment Variables

Edit `terraform.tfvars`:
```hcl
agent_mode = "both"  # Change from "manual"
```

Then apply:
```bash
terraform apply
```

### Update Scaling

Edit `terraform.tfvars`:
```hcl
min_instances = 1   # Keep 1 instance warm
max_instances = 50  # Allow more scaling
```

Then apply:
```bash
terraform apply
```

## 🌍 Multi-Environment Setup

### Create Environment-Specific Files

**dev.tfvars:**
```hcl
environment       = "dev"
container_image   = "gcr.io/agentic-ai-integration-490716/ai-agent:dev"
min_instances     = 0
max_instances     = 3
allow_unauthenticated = true  # For testing
```

**staging.tfvars:**
```hcl
environment       = "staging"
container_image   = "gcr.io/agentic-ai-integration-490716/ai-agent:staging"
min_instances     = 0
max_instances     = 5
allow_unauthenticated = false
```

**production.tfvars:**
```hcl
environment       = "production"
container_image   = "gcr.io/agentic-ai-integration-490716/ai-agent:latest"
min_instances     = 1  # Always available
max_instances     = 20
allow_unauthenticated = false
```

### Deploy to Specific Environment

```bash
# Development
terraform apply -var-file="dev.tfvars"

# Staging
terraform apply -var-file="staging.tfvars"

# Production
terraform apply -var-file="production.tfvars"
```

## 🔐 Using Secret Manager (Recommended)

Instead of storing secrets in `terraform.tfvars`, use environment variables:

```bash
# Set secrets as environment variables
export TF_VAR_gemini_api_key="your-key-here"
export TF_VAR_otel_auth_header="your-header-here"

# Deploy without secrets in files
terraform apply
```

Or use a secrets file outside the repo:

```bash
# Store secrets in ~/secrets/ai-agent.tfvars (outside repo)
terraform apply -var-file="~/secrets/ai-agent.tfvars"
```

## 📦 Remote State (Team Collaboration)

For team collaboration, store Terraform state in GCS:

### Step 1: Create GCS Bucket

```bash
gsutil mb -p agentic-ai-integration-490716 \
  -c STANDARD -l us-central1 \
  gs://agentic-ai-integration-490716-tfstate
```

### Step 2: Enable Versioning

```bash
gsutil versioning set on gs://agentic-ai-integration-490716-tfstate
```

### Step 3: Update main.tf

Uncomment the backend configuration in `main.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket  = "agentic-ai-integration-490716-tfstate"
    prefix  = "ai-agent/state"
  }
}
```

### Step 4: Migrate State

```bash
terraform init -migrate-state
```

Now your team can collaborate with shared state!

## 🧪 Testing After Deployment

Terraform outputs a test command:

```bash
terraform output test_command
```

Copy and run it to test your deployment.

Or use this:

```bash
# Get service URL
SERVICE_URL=$(terraform output -raw service_url)
TOKEN=$(gcloud auth print-identity-token)

# Test status
curl -H "Authorization: Bearer $TOKEN" $SERVICE_URL/status

# Test chat
curl -X POST $SERVICE_URL/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Tokyo?"}'
```

## 📊 View Console Links

```bash
terraform output console_links
```

This shows direct links to:
- Cloud Run service
- Logs
- Metrics
- Secret Manager

## 🔍 Troubleshooting

### Error: "API not enabled"

**Solution:**
```bash
# Terraform should enable APIs automatically, but if not:
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Error: "Permission denied"

**Solution:**
```bash
# Ensure you have required roles
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/editor"
```

### Error: "Container image not found"

**Solution:**
```bash
# Build the image first
cd ..
gcloud builds submit --tag gcr.io/agentic-ai-integration-490716/ai-agent
cd terraform
terraform apply
```

### Error: "State lock"

If Terraform crashes, state might be locked:

```bash
# Force unlock (use with caution!)
terraform force-unlock LOCK_ID
```

### View Detailed Logs

```bash
export TF_LOG=DEBUG
terraform apply
```

## 🎯 Best Practices

### 1. Use Version Control

```bash
git add main.tf variables.tf outputs.tf
git add terraform.tfvars.example
git commit -m "Add Terraform configuration"

# NEVER add terraform.tfvars or *.tfstate files!
```

### 2. Run Plan Before Apply

Always run `terraform plan` first to preview changes.

### 3. Use Workspaces for Environments

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select prod

# Apply (uses workspace-specific state)
terraform apply
```

### 4. Tag Resources

Add tags to track costs and ownership:

```hcl
resource "google_cloud_run_v2_service" "ai_agent" {
  # ... other config ...

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    team        = "ai-team"
  }
}
```

### 5. Pin Provider Versions

Already done in `main.tf`:
```hcl
required_providers {
  google = {
    source  = "hashicorp/google"
    version = "~> 5.0"  # Locked to 5.x
  }
}
```

## 📈 Cost Optimization

### Scale to Zero (Dev/Test)

```hcl
min_instances = 0
max_instances = 3
```

### Keep Warm (Production)

```hcl
min_instances = 1
max_instances = 20
```

### Right-Size Resources

Start small and adjust:
```hcl
cpu    = "1"
memory = "512Mi"
```

Monitor in Cloud Console and increase if needed.

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy with Terraform

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: hashicorp/setup-terraform@v2

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_CREDENTIALS }}

      - name: Terraform Init
        run: terraform init
        working-directory: terraform

      - name: Terraform Apply
        run: terraform apply -auto-approve
        working-directory: terraform
        env:
          TF_VAR_gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
          TF_VAR_otel_auth_header: ${{ secrets.OTEL_AUTH_HEADER }}
```

## 📚 Learn More

- **Terraform Docs**: https://www.terraform.io/docs
- **Google Provider**: https://registry.terraform.io/providers/hashicorp/google/latest/docs
- **Cloud Run Resource**: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service

## 🎓 Summary

**Advantages of Using Terraform:**

✅ **Repeatable** - Deploy identical infrastructure every time
✅ **Version Controlled** - Track infrastructure changes in Git
✅ **Multi-Environment** - Easy dev/staging/prod setups
✅ **Safe** - Preview changes before applying
✅ **Automated** - Integrate with CI/CD pipelines
✅ **Declarative** - Describe desired state, not steps
✅ **Idempotent** - Safe to run multiple times
✅ **Documented** - Configuration is self-documenting

---

**Ready to deploy? Run:**

```bash
terraform init
terraform plan
terraform apply
```

🚀 Your infrastructure will be deployed in minutes!
