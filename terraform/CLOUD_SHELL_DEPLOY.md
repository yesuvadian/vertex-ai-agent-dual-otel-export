# Deploy with Google Cloud Shell (Terraform Pre-installed)

Google Cloud Shell has Terraform pre-installed, making deployment easy!

## 🚀 Quick Deploy (5 Minutes)

### Step 1: Open Cloud Shell

Go to: https://console.cloud.google.com/

Click the **Cloud Shell** icon (>_) in the top right corner.

### Step 2: Upload Your Project

In Cloud Shell, run:

```bash
# Clone or upload your project
# Option A: If using git
git clone <your-repo-url>
cd ai_agent_projectgcp/terraform

# Option B: Upload files manually
# Click the "More" (⋮) menu → Upload → Upload folder
# Select the ai_agent_projectgcp folder
cd ai_agent_projectgcp/terraform
```

### Step 3: Create terraform.tfvars

```bash
cat > terraform.tfvars << 'EOF'
# GCP Configuration
project_id = "agentic-ai-integration-490716"
region     = "us-central1"

# Service Configuration
service_name    = "ai-agent"
container_image = "gcr.io/agentic-ai-integration-490716/ai-agent:latest"
environment     = "production"
service_version = "1.0"

# Secrets (FILL IN YOUR VALUES!)
gemini_api_key  = "AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8"
otel_auth_header = "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="

# OpenTelemetry Configuration
otel_service_name    = "ai-agent"
otel_endpoint        = "https://otel-tenant1.portal26.in:4318"
portal26_user_id     = "relusys"
portal26_tenant_id   = "tenant1"

# Agent Configuration
agent_mode = "manual"

# Resource Configuration
cpu             = "1"
memory          = "512Mi"
timeout_seconds = 300
concurrency     = 80

# Scaling Configuration
min_instances = 0
max_instances = 10

# Access Control
allow_unauthenticated = false
EOF
```

### Step 4: Set GCP Project

```bash
gcloud config set project agentic-ai-integration-490716
```

### Step 5: Run Deployment Script

```bash
# Make script executable
chmod +x deploy_terraform.sh

# Run deployment
./deploy_terraform.sh
```

Or run manually:

```bash
# Initialize
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply
```

### Step 6: Get Service URL

```bash
terraform output service_url
```

## 🧪 Test Your Deployment

```bash
# Get service URL
SERVICE_URL=$(terraform output -raw service_url)

# Get auth token
TOKEN=$(gcloud auth print-identity-token)

# Test status
curl -H "Authorization: Bearer $TOKEN" $SERVICE_URL/status

# Test chat
curl -X POST $SERVICE_URL/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Tokyo?"}'
```

## 📊 View Logs in Portal26

After making requests, check your Portal26 dashboard at:
- https://portal26.in/tenant1

You should see:
- **Traces**: Agent execution spans
- **Metrics**: Request counts, response times
- **Logs**: Application logs every 500ms

## 🔄 Update Deployment

After making code changes:

```bash
# Build new container image
cd ..
gcloud builds submit --tag gcr.io/agentic-ai-integration-490716/ai-agent

# Update deployment
cd terraform
terraform apply
```

## 🗑️ Cleanup (Destroy Resources)

```bash
terraform destroy
```

## 💡 Tips

- **Cloud Shell timeout**: Sessions timeout after 20 minutes of inactivity. Your files persist.
- **Editor**: Click "Open Editor" in Cloud Shell for a built-in IDE
- **File transfer**: Use `gcloud` commands or the upload/download buttons in Cloud Shell

---

**Ready to deploy? Just follow the 6 steps above!** 🚀
