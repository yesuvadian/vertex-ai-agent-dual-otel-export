# GCP Log Sink to AWS Lambda - Terraform Setup

## 🎯 **Overview**

Forward GCP Reasoning Engine logs to your existing AWS Lambda using Terraform.

**What this does:**
```
GCP Reasoning Engine Logs
    ↓
Log Sink (with filters)
    ↓
Pub/Sub Topic
    ↓
Pub/Sub Subscription
    ↓
Push to: YOUR EXISTING AWS LAMBDA
```

---

## 📁 **Two Setup Options**

### **Option 1: terraform_no_oidc/ (Simpler - For Testing)**

**Best for:**
- ✅ Users without gcloud CLI
- ✅ Quick testing/POC
- ✅ Lambda doesn't validate JWT yet
- ✅ Development environments

**Security:** ⚠️ No authentication (public Lambda URL)

**Setup:** Uses existing App Engine service account
```
Email: agentic-ai-integration-490716@appspot.gserviceaccount.com
Role: Editor
```

---

### **Option 2: terraform/ (Secure - For Production)**

**Best for:**
- ✅ Production deployments
- ✅ Security/compliance required
- ✅ Lambda validates JWT tokens
- ✅ Need authentication

**Security:** ✅ OIDC JWT tokens

**Setup:** Requires bootstrap (creates OIDC service account)

---

## 🆚 **Quick Comparison**

| Feature | terraform_no_oidc/ | terraform/ |
|---------|-------------------|------------|
| **Authentication** | ❌ None | ✅ OIDC JWT |
| **gcloud CLI** | ❌ Not needed | ✅ Needed for bootstrap |
| **Setup Steps** | 3 steps | 4 steps (bootstrap first) |
| **Lambda Changes** | None | Must validate JWT |
| **Security** | ⚠️ Low | ✅ High |
| **Use Case** | Testing/POC | Production |

---

## 🚀 **Quick Start**

### **For terraform_no_oidc/ (No OIDC):**

```bash
cd terraform_no_oidc/

# Set authentication (uses existing service account)
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"

# Configure
cp terraform.tfvars.example terraform.tfvars
# Edit with Lambda URL and Engine IDs

# Deploy
terraform init && terraform apply
```

**Complete guide:** `terraform_no_oidc/README.md`

---

### **For terraform/ (With OIDC):**

```bash
# Step 1: Bootstrap (one-time)
cd terraform/bootstrap/
terraform init && terraform apply
terraform output -raw service_account_key_file_content > terraform-sa-key.json
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"

# Step 2: Main infrastructure
cd ..
cp terraform.tfvars.example terraform.tfvars
# Edit with Lambda URL and Engine IDs
terraform init && terraform apply
```

**Complete guide:** `terraform/README.md`

---

## 🔑 **Authentication Methods**

### **terraform_no_oidc/ - Uses Existing Service Account**

**Service Account:** `agentic-ai-integration-490716@appspot.gserviceaccount.com`  
**Key file:** Admin creates and distributes to users  
**Lambda:** No JWT validation needed

### **terraform/ - Creates New OIDC Service Account**

**Service Account:** `pubsub-oidc-invoker@PROJECT.iam.gserviceaccount.com`  
**Created by:** Bootstrap Terraform  
**Lambda:** Must validate JWT tokens

---

## 📋 **What Gets Created**

**Both Options Create (GCP):**
- Pub/Sub Topic: `reasoning-engine-logs-topic`
- Pub/Sub Subscription
- Log Sink: `reasoning-engine-to-pubsub`

**terraform/ Also Creates:**
- Service Account: `pubsub-oidc-invoker`
- IAM Role Binding: Token Creator

**AWS Resources:**
- None (uses existing Lambda)

---

## 💰 **Cost Optimization**

Both options support the same log filters:

```hcl
# terraform.tfvars
log_severity_filter = ["ERROR", "CRITICAL"]  # 80-90% cost savings
```

---

## 📚 **Documentation**

### **terraform_no_oidc/ (No OIDC):**
- `README.md` - Complete setup guide for users without gcloud CLI
- `ADMIN_GUIDE.md` - Admin guide for distributing packages
- `generate_package_for_users.sh/bat` - Package generator scripts

### **terraform/ (With OIDC):**
- `README.md` - Main setup guide
- `BOOTSTRAP_README.md` - Bootstrap service account setup
- `TERRAFORM_PERMISSIONS.md` - Required permissions
- `TERRAFORM_QUICK_START.md` - Quick deployment guide
- `FILTERS_OVERVIEW.md` - Log filtering options

---

## 🎯 **Which One Should I Use?**

```
Do you have gcloud CLI installed?
├─ No → Use terraform_no_oidc/
└─ Yes → Do you need production security?
         ├─ Yes → Use terraform/ (with OIDC)
         └─ No → Use terraform_no_oidc/ (simpler)

Can your Lambda validate JWT tokens?
├─ No → Use terraform_no_oidc/
└─ Yes → Use terraform/ (with OIDC)

Is this for production?
├─ Yes → Use terraform/ (with OIDC)
└─ No → Use terraform_no_oidc/ (testing)
```

---

## 🔧 **Requirements**

### **For terraform_no_oidc/:**
- Terraform >= 1.0
- Service account key file (`appengine-sa-key.json`)
- AWS Lambda URL
- Reasoning Engine IDs
- ❌ No gcloud CLI needed

### **For terraform/:**
- Terraform >= 1.0
- gcloud CLI (for bootstrap)
- GCP Owner/Editor permissions
- AWS Lambda URL
- Reasoning Engine IDs

---

## 🆘 **Support**

**Common Issues:**

| Issue | Solution |
|-------|----------|
| No key file (no-OIDC) | Contact admin for `appengine-sa-key.json` |
| Permission denied (OIDC) | Run bootstrap first: `cd bootstrap/ && terraform apply` |
| No logs appearing | Check filter settings and Engine IDs |
| JWT validation fails | Ensure Lambda validates tokens (OIDC only) |

---

## 📞 **Getting Started**

**Choose your path:**

1. **For Users Without gcloud CLI:**  
   → Go to `terraform_no_oidc/` and read `README.md`

2. **For Production with Security:**  
   → Go to `terraform/` and read `README.md`

3. **For Admins Distributing to Users:**  
   → Go to `terraform_no_oidc/` and read `ADMIN_GUIDE.md`

---

## 🔄 **Migration Path**

**Start with terraform_no_oidc/, upgrade to terraform/ later:**

1. Test with `terraform_no_oidc/`
2. Add JWT validation to your Lambda
3. Deploy `terraform/` with OIDC
4. Remove `terraform_no_oidc/` resources

---

**Two options available - choose based on your needs!** 🚀
