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

## 📁 **Folder Structure**

```
lambda_poc/
├── README.md                           ← This file
├── terraform_no_oidc/                  ← USE THIS
│   ├── README.md                       # Complete user guide
│   ├── ADMIN_GUIDE.md                  # Admin distribution guide
│   ├── generate_package_for_users.sh   # Package generator
│   ├── main.tf                         # Terraform config
│   ├── gcp_log_sink_pubsub.tf         # GCP resources
│   └── terraform.tfvars.example        # Config example
│
└── terraform_with_oidc_ARCHIVED/       ← ARCHIVED (reference only)
    └── _DO_NOT_USE.txt                 # Why this is archived
```

---

## 🚀 **Quick Start**

### **For Users (Deploying Terraform):**

1. **Get the package from admin**
   - Contains Terraform files + service account key

2. **Follow the README**
   ```bash
   cd terraform_no_oidc/
   # Read README.md for complete instructions
   ```

3. **3-step deployment:**
   ```bash
   # Set authentication
   export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
   
   # Configure
   cp terraform.tfvars.example terraform.tfvars
   # Edit with your Lambda URL and Engine IDs
   
   # Deploy
   terraform init && terraform apply
   ```

**Complete guide:** See `terraform_no_oidc/README.md`

---

### **For Admins (Distributing to Users):**

1. **Generate package**
   ```bash
   cd terraform_no_oidc/
   bash generate_package_for_users.sh  # Linux/Mac
   # OR
   generate_package_for_users.bat      # Windows
   ```

2. **Distribute package**
   - Package contains: Terraform files + service account key
   - Share securely with users
   - Provide Lambda URL and Reasoning Engine IDs

**Complete guide:** See `terraform_no_oidc/ADMIN_GUIDE.md`

---

## 🔑 **Authentication**

Uses **existing App Engine service account**:
```
Email: agentic-ai-integration-490716@appspot.gserviceaccount.com
Role: Editor (full project access)
```

**Users need:**
- ✅ Service account key file (`appengine-sa-key.json`)
- ✅ Terraform installed
- ❌ **NO gcloud CLI required!**

---

## 📋 **What Gets Created**

**GCP Resources:**
- Pub/Sub Topic: `reasoning-engine-logs-topic`
- Pub/Sub Subscription: `reasoning-engine-to-lambda`
- Log Sink: `reasoning-engine-to-pubsub`

**AWS Resources:**
- None (uses existing Lambda)

---

## 💰 **Cost Optimization**

Use log filters to reduce costs by 80-90%:

```hcl
# terraform.tfvars
log_severity_filter = ["ERROR", "CRITICAL"]  # Only export errors
```

---

## 📚 **Documentation**

| File | Purpose | Audience |
|------|---------|----------|
| `terraform_no_oidc/README.md` | Complete setup guide | Users |
| `terraform_no_oidc/ADMIN_GUIDE.md` | Distribution guide | Admins |
| `terraform_no_oidc/terraform.tfvars.example` | Config template | Users |

---

## 🔧 **Requirements**

**For Deployment:**
- Terraform >= 1.0
- Service account key file (provided by admin)
- AWS Lambda URL
- Reasoning Engine IDs

**NOT Required:**
- ❌ gcloud CLI
- ❌ Personal GCP account
- ❌ GCP Console access

---

## ⚠️ **Important Notes**

1. **No OIDC authentication** - Lambda URL is public
2. **Testing/Development use** - For production, consider authentication
3. **Existing AWS Lambda** - This setup assumes Lambda already exists
4. **One setup method** - Use `terraform_no_oidc/` folder only

---

## 🆘 **Support**

**Common Issues:**

| Issue | Solution |
|-------|----------|
| No key file | Contact admin for `appengine-sa-key.json` |
| Permission errors | Verify service account has Editor role |
| No logs appearing | Check filter settings and Engine IDs |
| Wrong Lambda URL | Get correct URL from AWS Console |

---

## 📞 **Getting Started**

**Users:** Go to `terraform_no_oidc/` and read `README.md`

**Admins:** Go to `terraform_no_oidc/` and read `ADMIN_GUIDE.md`

---

**Simple, self-contained Terraform setup - no gcloud CLI needed!** 🚀
