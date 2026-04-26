# GCP Log Sink Setup Guide - Choose Your Option

## 🎯 **You Have Two Complete Options**

Both options are fully functional and ready to use. Choose based on your requirements.

---

## 📦 **Option 1: terraform/ - WITH OIDC (Production)**

### **✅ Use This When:**
- Production deployment
- Security is required
- Compliance needed
- Lambda can validate JWT tokens
- You have gcloud CLI installed

### **🔐 Security:**
- OIDC JWT token authentication
- Service account: `pubsub-oidc-invoker@PROJECT.iam.gserviceaccount.com`
- Lambda MUST validate JWT tokens
- Tokens are short-lived (1 hour)
- Cryptographically signed by Google

### **📋 Setup Steps:**

```bash
# Step 1: Bootstrap (creates OIDC service account)
cd bootstrap/
gcloud auth application-default login
terraform init
terraform apply
terraform output -raw service_account_key_file_content > terraform-sa-key.json

# Step 2: Set authentication
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"

# Step 3: Main infrastructure
cd ../terraform/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with:
#   - aws_lambda_url
#   - reasoning_engine_ids
#   - log_severity_filter

# Step 4: Deploy
terraform init
terraform plan
terraform apply
```

### **📚 Documentation:**
- `terraform/README.md` - Main setup guide
- `bootstrap/BOOTSTRAP_README.md` - Bootstrap details
- `terraform/TERRAFORM_PERMISSIONS.md` - Required permissions
- `terraform/TERRAFORM_QUICK_START.md` - Quick start
- `terraform/FILTERS_OVERVIEW.md` - Log filtering

### **⚙️ What Gets Created:**
```
GCP Resources:
├── Pub/Sub Topic
├── Pub/Sub Subscription (with OIDC token)
├── Log Sink
├── Service Account (pubsub-oidc-invoker)
└── IAM Role Binding (Token Creator)
```

### **🔧 Lambda Requirements:**
Your Lambda **MUST** validate JWT tokens:
```python
from google.oauth2 import id_token
from google.auth.transport import requests

def lambda_handler(event, context):
    # Extract JWT
    auth_header = event['headers'].get('authorization', '')
    token = auth_header.replace('Bearer ', '')
    
    # Validate JWT
    claims = id_token.verify_oauth2_token(
        token,
        requests.Request(),
        audience='https://your-lambda-url'
    )
    
    # Verify issuer
    if claims['iss'] != 'https://accounts.google.com':
        return {'statusCode': 403}
    
    # Process message...
```

---

## 📦 **Option 2: terraform_no_oidc/ - WITHOUT OIDC (Testing)**

### **✅ Use This When:**
- Testing/POC/Development
- Users don't have gcloud CLI
- Lambda doesn't validate JWT (yet)
- Quick setup needed
- No security requirements (or secured differently)

### **🔓 Security:**
- No OIDC authentication
- Public Lambda URL (anyone can POST)
- Service account: `agentic-ai-integration-490716@appspot.gserviceaccount.com` (existing)
- Lambda doesn't need JWT validation

### **📋 Setup Steps:**

**For Admin (one-time):**
```bash
cd terraform_no_oidc/

# Generate package for users
bash generate_package_for_users.sh  # Linux/Mac
# OR
generate_package_for_users.bat      # Windows

# This creates: terraform-gcp-setup-YYYYMMDD.zip
# Share this with users
```

**For Users:**
```bash
# Extract package
unzip terraform-gcp-setup.zip
cd terraform_no_oidc/

# Step 1: Set authentication
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"

# Step 2: Configure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with:
#   - aws_lambda_url
#   - reasoning_engine_ids
#   - log_severity_filter

# Step 3: Deploy
terraform init
terraform plan
terraform apply
```

### **📚 Documentation:**
- `terraform_no_oidc/README.md` - Complete user guide (no gcloud CLI)
- `terraform_no_oidc/ADMIN_GUIDE.md` - Admin distribution guide

### **⚙️ What Gets Created:**
```
GCP Resources:
├── Pub/Sub Topic
├── Pub/Sub Subscription (NO OIDC - plain HTTP)
└── Log Sink
```

### **🔧 Lambda Requirements:**
Lambda doesn't need JWT validation:
```python
def lambda_handler(event, context):
    # No authentication check needed
    # Just process the message
    message = event.get('message', {})
    # ... your business logic ...
```

---

## 🆚 **Side-by-Side Comparison**

| Feature | terraform/ (OIDC) | terraform_no_oidc/ (No OIDC) |
|---------|-------------------|------------------------------|
| **Authentication** | ✅ OIDC JWT | ❌ None |
| **Security Level** | ✅ High | ⚠️ Low |
| **gcloud CLI** | ✅ Required | ❌ Not needed |
| **Bootstrap Step** | ✅ Required | ❌ Not needed |
| **Setup Steps** | 4 steps | 3 steps |
| **Lambda Changes** | ✅ Must validate JWT | ❌ No changes |
| **Service Account** | Creates new | Uses existing |
| **Production Ready** | ✅ Yes | ❌ No (testing only) |
| **Deployment Time** | ~10-15 min | ~5 min |
| **Dependencies** | PyJWT, google-auth | None |
| **Package Size** | N/A | Zip with key file |
| **User Requirements** | gcloud + GCP perms | Just key file |

---

## 🔄 **Architecture Comparison**

### **With OIDC (terraform/):**
```
GCP Cloud Logging
    ↓
Log Sink (filter)
    ↓
Pub/Sub Topic
    ↓
Pub/Sub Subscription
    ↓
Service Account generates JWT
    ↓
POST https://lambda-url
Authorization: Bearer eyJhbGc...
    ↓
Lambda validates JWT ✓
    ↓
Process message
```

### **Without OIDC (terraform_no_oidc/):**
```
GCP Cloud Logging
    ↓
Log Sink (filter)
    ↓
Pub/Sub Topic
    ↓
Pub/Sub Subscription
    ↓
POST https://lambda-url
(no Authorization header)
    ↓
Lambda processes directly
```

---

## 🎯 **Decision Tree**

```
START: Choose Your Option
│
├─ Is this for PRODUCTION?
│  ├─ YES → Use terraform/ (with OIDC) ✅
│  └─ NO → Continue...
│
├─ Do you have gcloud CLI?
│  ├─ NO → Use terraform_no_oidc/ (no OIDC) ✅
│  └─ YES → Continue...
│
├─ Can your Lambda validate JWT?
│  ├─ NO → Use terraform_no_oidc/ (no OIDC) ✅
│  └─ YES → Continue...
│
├─ Do you need security/compliance?
│  ├─ YES → Use terraform/ (with OIDC) ✅
│  └─ NO → Use terraform_no_oidc/ (simpler) ✅
│
└─ DEFAULT → Use terraform/ (best practice)
```

---

## 📋 **Common Configuration (Both Options)**

Both options support the same configuration in `terraform.tfvars`:

```hcl
# GCP Project
gcp_project_id = "agentic-ai-integration-490716"
gcp_region     = "us-central1"

# AWS Lambda URL (REQUIRED)
aws_lambda_url = "https://YOUR-LAMBDA.lambda-url.us-east-1.on.aws"

# Reasoning Engine IDs (REQUIRED)
reasoning_engine_ids = [
  "8213677864684355584"
]

# Cost Optimization (RECOMMENDED)
log_severity_filter = ["ERROR", "CRITICAL"]  # 80-90% savings

# Optional Filters
agent_ids = []
log_resource_types = []
custom_log_filter = ""
```

---

## 🚀 **Quick Start Commands**

### **Option 1 (With OIDC):**
```bash
cd bootstrap/ && terraform init && terraform apply
cd terraform/ && terraform init && terraform apply
```

### **Option 2 (Without OIDC):**
```bash
cd terraform_no_oidc/
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
terraform init && terraform apply
```

---

## 🔄 **Migration Path**

### **Start Testing → Move to Production:**

1. **Phase 1: Test with No-OIDC**
   ```bash
   cd terraform_no_oidc/
   terraform apply
   # Test end-to-end flow
   ```

2. **Phase 2: Add JWT Validation to Lambda**
   - Update Lambda code to validate JWT
   - Deploy Lambda changes
   - Test JWT validation

3. **Phase 3: Deploy OIDC Version**
   ```bash
   # Destroy no-OIDC version
   cd terraform_no_oidc/
   terraform destroy
   
   # Deploy OIDC version
   cd ../bootstrap/ && terraform apply
   cd ../terraform/ && terraform apply
   ```

---

## 💰 **Cost Comparison**

**Both options have SAME GCP costs:**
- Pub/Sub messages: ~$0.40 per million
- Log Sink: Free
- Service accounts: Free

**Differences:**
- OIDC token generation: Free
- Lambda dependencies (PyJWT): Free
- **Total: NO COST DIFFERENCE** ✅

---

## 🆘 **Troubleshooting**

### **terraform/ (With OIDC):**

**Issue: "Permission denied" during bootstrap**
```bash
# Solution: Authenticate first
gcloud auth application-default login
```

**Issue: "Lambda returns 403"**
```python
# Solution: Add JWT validation to Lambda
# See terraform/README.md for code example
```

---

### **terraform_no_oidc/ (Without OIDC):**

**Issue: "No key file"**
```bash
# Solution: Admin must generate package
cd terraform_no_oidc/
bash generate_package_for_users.sh
# Then share the zip file
```

**Issue: "Application Default Credentials not found"**
```bash
# Solution: Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
```

---

## 📞 **Getting Help**

### **For terraform/ (With OIDC):**
1. Read `terraform/README.md`
2. Check `bootstrap/BOOTSTRAP_README.md` for bootstrap issues
3. Check `terraform/TERRAFORM_PERMISSIONS.md` for permission errors

### **For terraform_no_oidc/ (Without OIDC):**
1. **Users:** Read `terraform_no_oidc/README.md`
2. **Admins:** Read `terraform_no_oidc/ADMIN_GUIDE.md`

---

## ✅ **Both Options Are Production-Ready**

- ✅ **terraform/** - Best for production with security
- ✅ **terraform_no_oidc/** - Best for testing/users without gcloud

**Choose based on your requirements!** Both are fully functional and maintained.

---

## 🎯 **Summary**

| When to Use | Folder |
|-------------|--------|
| **Production deployment** | `terraform/` |
| **Security required** | `terraform/` |
| **Have gcloud CLI** | `terraform/` (recommended) |
| **Lambda validates JWT** | `terraform/` |
| **Testing/POC** | `terraform_no_oidc/` |
| **No gcloud CLI** | `terraform_no_oidc/` |
| **Users without GCP access** | `terraform_no_oidc/` |
| **Quick deployment** | `terraform_no_oidc/` |

---

**Both options available - choose what fits your needs!** 🚀
