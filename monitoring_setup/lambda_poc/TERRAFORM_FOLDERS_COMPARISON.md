# Terraform Folders Comparison

## 📁 **Two Terraform Setups Available**

You have **two options** for deploying GCP Log Sink infrastructure:

---

## 🔐 **Option 1: With OIDC Authentication (Recommended for Production)**

**Folder:** `terraform/`

### **Features:**
- ✅ **Secure**: OIDC JWT tokens for authentication
- ✅ **Service Account**: Creates `pubsub-oidc-invoker` for token generation
- ✅ **Lambda Validation**: Lambda validates JWT tokens from GCP
- ✅ **Production-Ready**: Industry standard authentication
- ✅ **Audit Trail**: Know exactly who sent what

### **Use When:**
- ✅ Production deployment
- ✅ Security/compliance required
- ✅ Lambda can validate JWT tokens
- ✅ Need to verify requests are from GCP

### **What Gets Created:**
```
GCP Resources:
├─ Log Sink (with filters)
├─ Pub/Sub Topic
├─ Pub/Sub Subscription (with OIDC)
└─ Service Account (pubsub-oidc-invoker)
   └─ Role: iam.serviceAccountTokenCreator
```

### **Deployment:**
```bash
cd terraform/

# Step 1: Bootstrap (one-time)
cd bootstrap/
terraform init && terraform apply
terraform output -raw service_account_key_file_content > terraform-sa-key.json
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"

# Step 2: Main infrastructure
cd ..
cp terraform.tfvars.example terraform.tfvars
# Edit: aws_lambda_url, reasoning_engine_ids, filters
terraform init
terraform apply
```

### **Lambda Requirements:**
Your Lambda **MUST validate JWT tokens**:
```python
from google.auth.transport import requests
from google.oauth2 import id_token

# Validate JWT
claims = id_token.verify_oauth2_token(
    token,
    requests.Request(),
    audience='https://your-lambda-url'
)
```

See `lambda_with_oidc.py` for full implementation.

---

## 🔓 **Option 2: Without OIDC Authentication (Testing Only)**

**Folder:** `terraform_no_oidc/`

### **Features:**
- ⚠️ **No Authentication**: Public Lambda URL, no JWT validation
- ✅ **Simple**: No service account, no bootstrap step
- ✅ **Quick Setup**: Faster deployment for testing
- ❌ **Not Secure**: Anyone with URL can send requests
- ❌ **No Verification**: Can't confirm requests are from GCP

### **Use When:**
- ✅ Testing/POC phase
- ✅ Development environment
- ✅ Lambda doesn't validate JWT yet
- ✅ Quick proof-of-concept
- ❌ NOT for production

### **What Gets Created:**
```
GCP Resources:
├─ Log Sink (with filters)
├─ Pub/Sub Topic
└─ Pub/Sub Subscription (plain HTTP POST, no OIDC)
```

### **Deployment:**
```bash
cd terraform_no_oidc/

cp terraform.tfvars.example terraform.tfvars
# Edit: aws_lambda_url, reasoning_engine_ids, filters
terraform init
terraform apply
```

### **Lambda Requirements:**
No JWT validation needed:
```python
def lambda_handler(event, context):
    # No authentication check
    # Just process the message
    message = event.get('message', {})
    # ... your business logic ...
```

---

## 🆚 **Side-by-Side Comparison**

| Feature | terraform/ (OIDC) | terraform_no_oidc/ (No OIDC) |
|---------|-------------------|------------------------------|
| **Security** | ✅ JWT tokens | ❌ None |
| **Authentication** | ✅ OIDC | ❌ Public URL |
| **Service Account** | ✅ Created | ❌ Not created |
| **Bootstrap Step** | ✅ Required | ❌ Not needed |
| **Lambda Validates JWT** | ✅ Required | ❌ Not required |
| **Production Ready** | ✅ Yes | ❌ No |
| **Setup Complexity** | Medium | Simple |
| **Deployment Time** | 10-15 min | 5 min |
| **Request Verification** | ✅ Yes | ❌ No |
| **Audit Trail** | ✅ Yes | ❌ No |

---

## 📊 **Architecture Comparison**

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
Service Account generates JWT token
    ↓
POST https://lambda-url
Authorization: Bearer eyJhbGc...
    ↓
Lambda validates JWT
    ↓ (if valid)
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
Lambda processes message
(no validation)
```

---

## 🎯 **Which One Should I Use?**

### **Start with No OIDC if:**
1. You're just testing the integration
2. Your Lambda doesn't validate JWT yet
3. You want to see data flowing quickly
4. You're in development/POC phase

**Then upgrade to OIDC when:**
1. Moving to production
2. Lambda code is ready to validate JWT
3. Security is a concern
4. Need compliance/audit trail

### **Start with OIDC if:**
1. You're deploying to production immediately
2. Lambda already validates JWT tokens
3. Security is required from day 1
4. You have compliance requirements

---

## 🔄 **Migration Path**

### **No OIDC → OIDC:**

**Step 1: Add JWT validation to Lambda**
```python
# Update your Lambda code
# See lambda_with_oidc.py for reference
```

**Step 2: Deploy OIDC infrastructure**
```bash
cd terraform/bootstrap/
terraform init && terraform apply
cd ..
terraform init && terraform apply
```

**Step 3: Remove non-OIDC version**
```bash
cd terraform_no_oidc/
terraform destroy
```

### **OIDC → No OIDC:**
```bash
# Generally NOT recommended
# Security downgrade
# Only if absolutely necessary
```

---

## 📝 **Configuration Files**

### **terraform/**
```
terraform/
├── bootstrap/
│   ├── main.tf                      # Service account for Terraform
│   └── terraform.tfvars.example
├── main.tf                          # Core config
├── gcp_log_sink_pubsub.tf          # Log sink + Pub/Sub with OIDC
├── terraform.tfvars.example         # Config example
├── BOOTSTRAP_README.md              # Bootstrap guide
├── README.md                        # Main guide
├── TERRAFORM_PERMISSIONS.md         # Permissions
├── TERRAFORM_QUICK_START.md         # Quick start
└── FILTERS_OVERVIEW.md              # Filter reference
```

### **terraform_no_oidc/**
```
terraform_no_oidc/
├── main.tf                          # Core config
├── gcp_log_sink_pubsub.tf          # Log sink + Pub/Sub (no OIDC)
├── terraform.tfvars.example         # Config example
└── README.md                        # Setup guide
```

---

## 🔐 **Security Implications**

### **With OIDC (terraform/):**
- ✅ Cryptographically signed JWT tokens
- ✅ Audience restriction (token only valid for your Lambda)
- ✅ Short-lived tokens (~1 hour expiry)
- ✅ Service account identity verification
- ✅ Can audit who sent what
- ✅ Prevents unauthorized access

### **Without OIDC (terraform_no_oidc/):**
- ❌ Public URL - anyone can send requests
- ❌ No verification of sender identity
- ❌ No audit trail
- ❌ Potential for spam/abuse
- ❌ No compliance with security standards

---

## 💰 **Cost Comparison**

**Both options have the same GCP costs:**
- Log Sink: Free
- Pub/Sub messages: ~$0.40 per million
- Log filtering reduces costs equally

**OIDC adds:**
- Service account: Free
- IAM operations: Free
- Token generation: Free

**Conclusion:** OIDC adds security with **no additional cost** ✅

---

## 🚀 **Quick Decision Tree**

```
Are you deploying to production?
    ├─ Yes → Use terraform/ (with OIDC)
    └─ No → Is this just a quick test?
            ├─ Yes → Use terraform_no_oidc/ (no OIDC)
            └─ No → Use terraform/ (with OIDC)

Can your Lambda validate JWT tokens?
    ├─ Yes → Use terraform/ (with OIDC)
    └─ No → Use terraform_no_oidc/ temporarily
            → Add JWT validation to Lambda
            → Migrate to terraform/

Do you have security/compliance requirements?
    ├─ Yes → Use terraform/ (with OIDC)
    └─ No → Still recommend terraform/ for best practices
```

---

## 📞 **Getting Help**

**For OIDC version:**
- See `terraform/README.md`
- See `terraform/BOOTSTRAP_README.md`
- Example: `lambda_with_oidc.py`

**For No-OIDC version:**
- See `terraform_no_oidc/README.md`

**Both versions:**
- See `FILTERS_OVERVIEW.md` for filtering options
- See `TERRAFORM_PERMISSIONS.md` for GCP permissions

---

## ✅ **Recommendations**

1. **For Production:** Always use `terraform/` with OIDC ✅
2. **For Testing:** Use `terraform_no_oidc/` temporarily, then upgrade
3. **Default Choice:** `terraform/` (OIDC) - it's the right long-term solution
4. **Migration:** Easy to go from No-OIDC → OIDC, just add JWT validation

---

**Choose wisely based on your security needs!** 🔒
