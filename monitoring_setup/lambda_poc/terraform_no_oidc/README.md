# GCP Log Sink Setup - WITHOUT OIDC Authentication

## ⚠️ **WARNING: NO AUTHENTICATION**

This Terraform configuration creates GCP resources **without OIDC authentication**.

**Security:**
- ❌ No OIDC service account
- ❌ No JWT tokens
- ❌ Lambda URL is public - anyone can send requests

**Use Cases:**
- ✅ Testing/POC when Lambda doesn't validate JWT
- ✅ Development environments
- ❌ NOT for production

**For Production:** Use `../terraform/` folder with OIDC authentication

---

## 📦 **What Gets Created (GCP Only)**

```
GCP Cloud Logging (Reasoning Engine)
    ↓
Log Sink (with severity/agent filters)
    ↓
Pub/Sub Topic
    ↓
Pub/Sub Subscription (NO OIDC - just HTTP POST)
    ↓
Push to: YOUR EXISTING AWS LAMBDA ✅
```

**No authentication** - Pub/Sub sends plain HTTP POST to Lambda

---

## 🚀 **Quick Start (Automated Setup)**

### **Option 1: Use Setup Script (Easiest)**

**Linux/Mac:**
```bash
cd terraform_no_oidc/
bash setup_with_existing_sa.sh
```

**Windows:**
```cmd
cd terraform_no_oidc\
setup_with_existing_sa.bat
```

This script will:
- ✅ Create key file for existing App Engine service account
- ✅ Set authentication automatically
- ✅ Create terraform.tfvars from example

Then edit `terraform.tfvars` and run:
```bash
terraform init
terraform plan
terraform apply
```

---

### **Option 2: Manual Setup**

### **Step 1: Create Service Account Key**

Using the existing **App Engine service account** (Editor role):

```bash
cd terraform_no_oidc/

# Create key file
gcloud iam service-accounts keys create appengine-sa-key.json \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com \
  --project=agentic-ai-integration-490716
```

### **Step 2: Set Authentication**

**Linux/Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
```

**Windows PowerShell:**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"
```

**Windows CMD:**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\appengine-sa-key.json
```

### **Step 3: Update Configuration**

```bash
cp terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars
```

Edit these values:
```hcl
# Your Existing AWS Lambda URL
aws_lambda_url = "https://abc123xyz.lambda-url.us-east-1.on.aws"

# Your Reasoning Engine IDs
reasoning_engine_ids = [
  "8213677864684355584"
]

# Cost Optimization
log_severity_filter = ["ERROR", "CRITICAL"]
```

### **Step 4: Deploy GCP Infrastructure**

```bash
terraform init
terraform plan    # Review what will be created
terraform apply   # Type 'yes' to confirm
```

**What gets created:**
- ✅ Pub/Sub Topic: `reasoning-engine-logs-topic`
- ✅ Pub/Sub Subscription: `reasoning-engine-to-lambda` (no OIDC)
- ✅ Log Sink: `reasoning-engine-to-pubsub` (with filters)

---

## 🆚 **Comparison with OIDC Version**

| Feature | This (No OIDC) | terraform/ (With OIDC) |
|---------|----------------|------------------------|
| **Authentication** | ❌ None | ✅ JWT tokens |
| **Service Account** | ❌ Not created | ✅ pubsub-oidc-invoker |
| **Lambda Validation** | Not required | Required |
| **Security** | ⚠️ Low | ✅ High |
| **Use Case** | Testing only | Production |
| **Setup Complexity** | Simple | Medium (bootstrap needed) |

---

## 🔧 **Differences from OIDC Version**

### **What's NOT Created:**

1. ❌ **Service Account** (`pubsub-oidc-invoker`)
   - No service account for OIDC token generation
   
2. ❌ **IAM Role Binding**
   - No Token Creator role needed

3. ❌ **Bootstrap Step**
   - No terraform-deployer service account needed
   - Use your personal GCP credentials directly

### **What's Different:**

**Pub/Sub Subscription:**
```hcl
# No OIDC (this version)
push_config {
  push_endpoint = var.aws_lambda_url
  # No authentication
}

# With OIDC (../terraform/ version)
push_config {
  push_endpoint = var.aws_lambda_url
  oidc_token {
    service_account_email = google_service_account.pubsub_oidc_invoker.email
    audience              = var.aws_lambda_url
  }
}
```

---

## 🧪 **Testing**

### **1. Check GCP Resources:**
```bash
# List Pub/Sub topics
gcloud pubsub topics list

# List subscriptions
gcloud pubsub subscriptions list

# Describe subscription (no OIDC config)
gcloud pubsub subscriptions describe reasoning-engine-to-lambda
```

### **2. Test Message:**
```bash
gcloud pubsub topics publish reasoning-engine-logs-topic \
  --message='{"test": "data"}'
```

### **3. Check Lambda Logs:**
```bash
# Should receive message without Authorization header
aws logs tail /aws/lambda/YOUR-FUNCTION-NAME --follow
```

---

## 📊 **What This Terraform Does NOT Create**

❌ AWS Lambda function (you already have it)
❌ S3 buckets (already exist)
❌ Kinesis streams (already exist)
❌ OIDC service account (intentionally not created)
❌ Portal26 routing logic (in your Lambda code)

---

## 🔐 **Security Considerations**

### **Risks:**

1. **Public Lambda URL**
   - Anyone with the URL can send requests
   - No authentication validation

2. **No Request Verification**
   - Can't verify requests are from GCP
   - Potential for spam/abuse

3. **No Audit Trail**
   - Can't identify who sent what

### **Mitigations:**

**Option 1: IP Allowlisting (AWS)**
```
Restrict Lambda URL to Google Cloud IP ranges
```

**Option 2: Upgrade to OIDC**
```bash
# Use the main terraform/ folder instead
cd ../terraform/
```

---

## 🎯 **When to Use This vs OIDC**

### **Use This (No OIDC) When:**
- ✅ Testing/POC phase
- ✅ Lambda doesn't validate JWT (yet)
- ✅ Development environment
- ✅ Quick proof-of-concept

### **Use OIDC (../terraform/) When:**
- ✅ Production deployment
- ✅ Security is required
- ✅ Lambda can validate JWT
- ✅ Compliance requirements

---

## 📁 **File Structure**

```
terraform_no_oidc/
├── main.tf                          # Core Terraform config
├── gcp_log_sink_pubsub.tf          # Log sink + Pub/Sub (no OIDC)
├── terraform.tfvars.example         # Config example
└── README.md                        # This file
```

---

## 🔄 **Migrating to OIDC Later**

When ready for production:

### **Step 1: Deploy OIDC version**
```bash
cd ../terraform/bootstrap/
terraform init && terraform apply

cd ..
terraform init && terraform apply
```

### **Step 2: Update Lambda**
Add JWT validation to your Lambda code (see `../lambda_with_oidc.py`)

### **Step 3: Remove non-OIDC version**
```bash
cd ../terraform_no_oidc/
terraform destroy
```

---

## ✅ **Deployment Checklist**

- [ ] AWS Lambda already exists and has business logic
- [ ] Lambda **does NOT** validate JWT tokens (or you're testing)
- [ ] Updated `terraform.tfvars` with Lambda URL
- [ ] Updated reasoning engine IDs
- [ ] Set log severity filter for cost savings
- [ ] Understand security risks (no authentication)
- [ ] Planning to upgrade to OIDC for production

---

## 🆘 **Support**

**Common Issues:**

**"No logs appearing"**
- Check filter settings (`log_severity_filter`)
- Verify reasoning engine ID is correct
- Check Lambda is receiving requests (CloudWatch logs)

**"Lambda returning errors"**
- Check Lambda expects plain HTTP POST (no Authorization header)
- Verify message format is correct

**"Want to add authentication"**
- Use `../terraform/` folder with OIDC instead
- See `../terraform/README.md` for setup

---

**Simple, no-auth setup for testing!** 🎯  
**Remember: Upgrade to OIDC (`../terraform/`) for production!** 🔒
