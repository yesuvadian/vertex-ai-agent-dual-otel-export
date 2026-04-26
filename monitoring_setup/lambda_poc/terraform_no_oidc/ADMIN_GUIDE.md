# Admin Guide - Distributing Terraform to Users Without gcloud CLI

## 🎯 **Overview**

This guide explains how to package and distribute Terraform configuration to users who:
- ❌ Don't have gcloud CLI installed
- ❌ Don't have GCP accounts
- ✅ Only have Terraform installed
- ✅ Will use existing App Engine service account

---

## 🔑 **Service Account Being Used**

**Email:** `agentic-ai-integration-490716@appspot.gserviceaccount.com`  
**Role:** Editor (full project access)  
**Type:** App Engine default service account (already exists)

**Why this service account?**
- ✅ Already exists in the project
- ✅ Has Editor role (all permissions needed)
- ✅ No need to create new service account
- ✅ Can be used for Terraform deployment

---

## 📦 **Method 1: Automated Package Generation (Recommended)**

### **For Linux/Mac Admin:**

```bash
cd terraform_no_oidc/
bash generate_package_for_users.sh
```

### **For Windows Admin:**

```cmd
cd terraform_no_oidc\
generate_package_for_users.bat
```

**This script will:**
1. ✅ Create service account key file (`appengine-sa-key.json`)
2. ✅ Verify service account has Editor role
3. ✅ Package all necessary files
4. ✅ Create user-friendly README
5. ✅ Generate QUICK_START.txt guide
6. ✅ Create zip file (Linux/Mac only)

**Output:**
```
terraform-gcp-setup-YYYYMMDD.zip  (Linux/Mac)
terraform_no_oidc_package/        (Windows)
```

---

## 📦 **Method 2: Manual Package Creation**

### **Step 1: Create Service Account Key**

```bash
# Create key file
gcloud iam service-accounts keys create appengine-sa-key.json \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com \
  --project=agentic-ai-integration-490716
```

### **Step 2: Prepare Files**

Create a folder with these files:
```
terraform-package/
├── main.tf
├── gcp_log_sink_pubsub.tf
├── terraform.tfvars.example
├── appengine-sa-key.json          ← Service account key
├── README.md                       ← Copy from README_FOR_USERS.md
└── QUICK_START.txt                 ← Simple instructions
```

### **Step 3: Create QUICK_START.txt**

```txt
TERRAFORM GCP SETUP - QUICK START

1. Set Authentication:
   
   Windows PowerShell:
   $env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"
   
   Linux/Mac:
   export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"

2. Configure:
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with Lambda URL and Engine IDs

3. Deploy:
   terraform init
   terraform plan
   terraform apply

See README.md for detailed instructions.
```

### **Step 4: Compress**

**Linux/Mac:**
```bash
zip -r terraform-gcp-setup.zip terraform-package/

# Or with password protection:
zip -e -r terraform-gcp-setup.zip terraform-package/
```

**Windows:**
```powershell
Compress-Archive -Path terraform-package -DestinationPath terraform-gcp-setup.zip

# Or use 7-Zip for password protection:
7z a -p terraform-gcp-setup.zip terraform-package/
```

---

## 📧 **Distributing to Users**

### **What to Send:**

1. **The package:** `terraform-gcp-setup.zip` or folder
2. **AWS Lambda URL:** (user needs to add to terraform.tfvars)
3. **Reasoning Engine IDs:** (user needs to add to terraform.tfvars)

### **Email Template:**

```
Subject: Terraform Setup for GCP Log Sink

Hi [User],

Attached is the Terraform package to set up GCP log forwarding to AWS Lambda.

Prerequisites:
- Terraform installed (https://www.terraform.io/downloads)
- No gcloud CLI needed - everything is included!

Setup:
1. Extract the zip file
2. Follow QUICK_START.txt for 3-step setup
3. See README.md for detailed instructions

Configuration you'll need to provide:
- AWS Lambda URL: [PROVIDE YOUR LAMBDA URL HERE]
- Reasoning Engine IDs: [PROVIDE IDS HERE]

The package contains a service account key file that authenticates 
Terraform to GCP. Keep it secure and don't commit to git.

Let me know if you have any questions!

Best regards,
[Your Name]
```

---

## 🔐 **Security Best Practices**

### **When Creating Key:**

```bash
# Create key with expiry (if supported)
gcloud iam service-accounts keys create appengine-sa-key.json \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com \
  --project=agentic-ai-integration-490716

# Verify key was created
gcloud iam service-accounts keys list \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com
```

### **When Distributing:**

1. **Encrypt the package**
   ```bash
   # Password-protect zip
   zip -e terraform-gcp-setup.zip terraform-package/
   # Share password separately (e.g., via SMS or phone)
   ```

2. **Use secure channels**
   - Encrypted email (e.g., ProtonMail)
   - Secure file transfer (e.g., OneDrive with link expiry)
   - Internal secure storage

3. **Track distribution**
   - Keep record of who received key file
   - Note when distributed

### **Key Rotation:**

**Every 90 days or when compromised:**

```bash
# List existing keys
gcloud iam service-accounts keys list \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com

# Delete old key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com

# Create new key
gcloud iam service-accounts keys create appengine-sa-key-new.json \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com

# Distribute new key to users
```

---

## 👥 **Supporting Users**

### **Common User Issues:**

| Issue | Solution |
|-------|----------|
| "terraform: command not found" | User needs to install Terraform |
| "Application Default Credentials not found" | User forgot to set `GOOGLE_APPLICATION_CREDENTIALS` |
| "Permission denied" | Key file may be corrupted, send new one |
| "No such file: appengine-sa-key.json" | User didn't extract properly or wrong directory |

### **Quick Diagnostics:**

Ask user to run:
```bash
# Check Terraform installed
terraform --version

# Check environment variable set
echo $GOOGLE_APPLICATION_CREDENTIALS  # Linux/Mac
echo %GOOGLE_APPLICATION_CREDENTIALS%  # Windows

# Check key file exists
ls appengine-sa-key.json              # Linux/Mac
dir appengine-sa-key.json             # Windows

# Test authentication
terraform init
```

---

## 📋 **User Information Needed**

Users must provide these values in `terraform.tfvars`:

### **1. AWS Lambda URL** (Required)
```hcl
aws_lambda_url = "https://abc123xyz.lambda-url.us-east-1.on.aws"
```

**How to get:**
- AWS Console → Lambda → Function → Configuration → Function URL
- Or provide it to them directly

### **2. Reasoning Engine IDs** (Required)
```hcl
reasoning_engine_ids = [
  "8213677864684355584"
]
```

**How to get:**
```bash
gcloud ai reasoning-engines list \
  --location=us-central1 \
  --project=agentic-ai-integration-490716
```

Provide this list to users, or have them select from available engines.

### **3. Log Filters** (Optional but recommended)
```hcl
log_severity_filter = ["ERROR", "CRITICAL"]
```

Recommend ERROR/CRITICAL for cost savings.

---

## 🔍 **Verification**

### **After User Deploys:**

Ask user to send output of:
```bash
terraform output
```

Should show:
```
lambda_target_url = "https://..."
log_sink_filter = "..."
pubsub_subscription_name = "reasoning-engine-to-lambda"
pubsub_topic_name = "reasoning-engine-logs-topic"
```

### **Check in GCP Console:**

1. **Pub/Sub Topic:** https://console.cloud.google.com/cloudpubsub/topic/list?project=agentic-ai-integration-490716
   - Should see: `reasoning-engine-logs-topic`

2. **Pub/Sub Subscription:** 
   - Should see: `reasoning-engine-to-lambda`
   - Push endpoint should be user's Lambda URL

3. **Log Sink:** https://console.cloud.google.com/logs/router?project=agentic-ai-integration-490716
   - Should see: `reasoning-engine-to-pubsub`

---

## 🎯 **Complete Admin Workflow**

```bash
# 1. Generate package (one-time)
cd terraform_no_oidc/
bash generate_package_for_users.sh

# 2. Review package contents
ls terraform-gcp-setup-*.zip

# 3. Optionally add password
zip -e terraform-gcp-setup-secure.zip terraform_no_oidc_package/

# 4. Send to user with instructions
# Email template above

# 5. Provide required info:
#    - Lambda URL
#    - Reasoning Engine IDs

# 6. Support user through deployment

# 7. Verify resources created in GCP Console

# 8. Schedule key rotation in 90 days
```

---

## 📞 **Support Checklist**

When user reports issues:

- [ ] Verify Terraform is installed
- [ ] Verify `GOOGLE_APPLICATION_CREDENTIALS` is set
- [ ] Verify key file exists and is not corrupted
- [ ] Check terraform.tfvars has correct values
- [ ] Verify AWS Lambda URL is correct
- [ ] Check reasoning engine IDs are valid
- [ ] Review terraform plan output with user
- [ ] Check GCP Console for created resources
- [ ] Verify Lambda is receiving messages

---

**Summary:** Users get a self-contained package with service account key - no gcloud CLI needed! 🚀
