# GCP Log Sink Setup - For Existing AWS Infrastructure

## 🎯 **Use Case**

You **already have AWS infrastructure** (Lambda, S3, Kinesis, Portal26 routing).

This Terraform **only creates GCP resources** to forward logs to your existing Lambda.

---

## 📦 **What Gets Created (GCP Only)**

```
GCP Cloud Logging (Reasoning Engine)
    ↓
Log Sink (with severity/agent filters)
    ↓
Pub/Sub Topic
    ↓
Pub/Sub Subscription (OIDC authentication)
    ↓
Push to: YOUR EXISTING AWS LAMBDA ✅
```

**No AWS resources created** - just connects GCP to your existing setup.

---

## 🚀 **Quick Start**

### **1. Update Configuration**

Copy example config:
```bash
cd terraform/
cp terraform.tfvars.example.simple terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
# GCP Configuration
gcp_project_id = "agentic-ai-integration-490716"
gcp_region     = "us-central1"

# Your Existing AWS Lambda URL
aws_lambda_url = "https://abc123xyz.lambda-url.us-east-1.on.aws"

# Which Reasoning Engines to monitor
reasoning_engine_ids = [
  "8213677864684355584"  # Get from: gcloud ai reasoning-engines list
]

# Cost Optimization - Only export errors
log_severity_filter = ["ERROR", "CRITICAL"]
```

---

### **2. Create Service Account (One-time)**

```bash
cd bootstrap/
terraform init
terraform apply
```

**What this does:**
- Creates `terraform-deployer@PROJECT.iam.gserviceaccount.com`
- Grants 6 required IAM roles
- Generates key file: `terraform-sa-key.json`

---

### **3. Deploy GCP Infrastructure**

```bash
cd ..  # Back to terraform/ directory
terraform init
terraform plan    # Review what will be created
terraform apply   # Type 'yes' to confirm
```

**What gets created:**
- ✅ Pub/Sub Topic: `reasoning-engine-logs-topic`
- ✅ Pub/Sub Subscription: `reasoning-engine-to-oidc` (pushes to your Lambda)
- ✅ Log Sink: `reasoning-engine-to-pubsub` (with filters)
- ✅ OIDC Service Account: `pubsub-oidc-invoker@PROJECT.iam.gserviceaccount.com`

---

## 🔐 **OIDC Authentication**

### **How It Works:**

```
GCP Pub/Sub Subscription
    ↓
Generate OIDC JWT token
    ↓
POST https://your-lambda-url
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**JWT Token Contains:**
- `iss`: `https://accounts.google.com` (issuer)
- `aud`: Your Lambda URL (audience)
- `email`: `pubsub-oidc-invoker@PROJECT.iam.gserviceaccount.com`
- `exp`: Token expiration

---

## ⚠️ **Important: Lambda Must Validate JWT**

Your existing Lambda **must validate** the OIDC JWT token:

### **Python Example:**
```python
from google.auth.transport import requests
from google.oauth2 import id_token

def lambda_handler(event, context):
    # Extract JWT from Authorization header
    auth_header = event['headers'].get('authorization', '')
    token = auth_header.replace('Bearer ', '')
    
    # Validate JWT
    try:
        claims = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            audience='https://your-lambda-url'
        )
        
        # Verify issuer
        if claims['iss'] != 'https://accounts.google.com':
            return {'statusCode': 403, 'body': 'Invalid issuer'}
            
    except Exception as e:
        return {'statusCode': 403, 'body': f'Invalid token: {e}'}
    
    # Process message
    # ... your existing business logic ...
```

**Dependencies:**
```
google-auth==2.23.0
```

---

## 💰 **Cost Optimization**

### **Filter by Severity:**

```hcl
# Option 1: Only errors (80-90% cost savings)
log_severity_filter = ["ERROR", "CRITICAL"]

# Option 2: Warnings and above (60-70% savings)
log_severity_filter = ["WARNING", "ERROR", "CRITICAL"]

# Option 3: Everything (expensive)
log_severity_filter = []
```

### **Filter by Agent:**

```hcl
# Monitor specific agents only
agent_ids = ["agent-123", "agent-456"]

# Monitor all agents
agent_ids = []
```

---

## 🧪 **Testing**

### **1. Check GCP Resources:**
```bash
# List Pub/Sub topics
gcloud pubsub topics list

# List subscriptions
gcloud pubsub subscriptions list

# Test publish
gcloud pubsub topics publish reasoning-engine-logs-topic \
  --message='{"test": "data"}'
```

### **2. Check Lambda Logs:**
```bash
aws logs tail /aws/lambda/YOUR-FUNCTION-NAME --follow
```

### **3. Verify OIDC:**
- Check Lambda logs for `Authorization` header
- Verify JWT token is present
- Check for validation errors

---

## 📊 **What This Terraform Does NOT Create**

❌ AWS Lambda function (you already have it)
❌ S3 buckets (already exist)
❌ Kinesis streams (already exist)
❌ Portal26 routing logic (in your Lambda code)

---

## 🗂️ **File Structure**

```
terraform/
├── bootstrap/
│   └── main.tf                      # Service account setup
├── main.tf                          # Terraform config (GCP only)
├── gcp_log_sink_pubsub.tf          # Log sink + Pub/Sub
├── terraform.tfvars.example.simple  # Config example
└── README_EXISTING_AWS.md          # This file
```

---

## 🔧 **Troubleshooting**

### **"Permission denied" during terraform apply**
- Run bootstrap first: `cd bootstrap/ && terraform apply`
- Use service account: `export GOOGLE_APPLICATION_CREDENTIALS="../terraform-sa-key.json"`

### **"No logs appearing in Lambda"**
- Check log sink filter matches your reasoning engine ID
- Verify severity filter isn't too restrictive
- Check Pub/Sub subscription is pushing to correct URL

### **"Lambda returns 403"**
- Your Lambda must validate OIDC JWT tokens
- Check Authorization header is present
- Verify audience matches your Lambda URL

### **"JWT validation failed"**
- Install `google-auth` in Lambda: `pip install google-auth`
- Verify audience = Lambda URL (exact match)
- Check issuer = `https://accounts.google.com`

---

## 📞 **Get Your Reasoning Engine ID**

```bash
gcloud ai reasoning-engines list \
  --location=us-central1 \
  --project=agentic-ai-integration-490716
```

Copy the ID (e.g., `8213677864684355584`) to `terraform.tfvars`.

---

## ✅ **Deployment Checklist**

- [ ] AWS Lambda already exists and has business logic
- [ ] Updated `terraform.tfvars` with Lambda URL
- [ ] Updated reasoning engine IDs
- [ ] Set log severity filter for cost savings
- [ ] Deployed bootstrap (service account)
- [ ] Deployed main terraform (GCP resources)
- [ ] Lambda validates OIDC JWT tokens
- [ ] Tested end-to-end flow

---

**Clean, GCP-only setup for existing AWS infrastructure!** 🎯
