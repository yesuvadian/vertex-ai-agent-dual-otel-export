# How Clients Will Run Terraform

## 📋 Complete Workflow: Admin → Client

---

## **Part 1: Admin Preparation (You Do This Once)**

### **Step 1: Generate Client Package**

```bash
cd monitoring_setup/terraformGCP/terraform_no_oidc/

# Option A: Use automated script (Linux/Mac)
bash generate_package_for_users.sh

# Option B: Manual package creation
mkdir client_package
cp main.tf client_package/
cp gcp_log_sink_pubsub.tf client_package/
cp terraform.tfvars.example client_package/
cp appengine-sa-key.json client_package/
cp CLIENT_GUIDE.md client_package/
```

### **Step 2: Distribute to Client**

**What to send:**
- `client_package/` folder (or zip it)
- Client's AWS Lambda URL (you provide this)
- Client's Reasoning Engine IDs (you provide this)

**How to send:**
- Secure email (encrypted)
- Secure file transfer (OneDrive, Google Drive with expiry)
- Internal secure storage

---

## **Part 2: Client Execution (Client Does This)**

### **Prerequisites Client Needs:**
- ✅ Terraform installed
- ✅ Their AWS Lambda URL (you provide)
- ✅ Their Reasoning Engine IDs (you provide)
- ❌ NO gcloud CLI needed!
- ❌ NO GCP account needed!

### **Client Steps (3 Steps Only!):**

#### **Step 1: Set Authentication**

Extract the package and open terminal in the folder:

**Windows PowerShell:**
```powershell
cd client_package
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"
```

**Windows CMD:**
```cmd
cd client_package
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\appengine-sa-key.json
```

**Linux/Mac:**
```bash
cd client_package
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
```

#### **Step 2: Configure Settings**

```bash
# Copy template
copy terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars - only 3 lines to change:
```

Edit `terraform.tfvars`:
```hcl
gcp_project_id = "agentic-ai-integration-490716"  # ✅ Already set

aws_lambda_url = "https://abc123.lambda-url.us-east-1.on.aws"  # ⚠️ CHANGE THIS

reasoning_engine_ids = ["YOUR-ENGINE-ID"]  # ⚠️ CHANGE THIS
```

#### **Step 3: Deploy**

```bash
terraform init      # Downloads providers
terraform plan      # Shows what will be created
terraform apply     # Creates resources (type 'yes')
```

**Output after success:**
```
============================================================================
GCP Log Sink Deployment Complete!
============================================================================

GCP Resources Created:
- Pub/Sub Topic: reasoning-engine-logs-topic
- Pub/Sub Subscription: reasoning-engine-to-lambda
- Log Sink: reasoning-engine-to-pubsub

Target Endpoint:
- Your AWS Lambda: https://abc123.lambda-url.us-east-1.on.aws

Next Steps:
1. Generate a log in your Reasoning Engine
2. Check your Lambda logs in AWS CloudWatch
============================================================================
```

---

## **What Client Gets**

### **Before Terraform:**
```
GCP Reasoning Engine
    ↓
Logs stay in GCP only
```

### **After Terraform:**
```
GCP Reasoning Engine
    ↓
GCP Cloud Logging
    ↓
Log Sink (filters by Engine ID)
    ↓
Pub/Sub Topic
    ↓
Pub/Sub Subscription
    ↓
AWS Lambda (client's existing Lambda)
    ↓
Client's business logic
```

---

## **Client Experience Summary**

### **What Client Has:**
- ✅ Package folder with 4 files
- ✅ CLIENT_GUIDE.md (instructions)
- ✅ Terraform binary installed

### **What Client Does:**
1. Set one environment variable (1 command)
2. Edit 2 values in terraform.tfvars
3. Run 3 terraform commands

### **What Client Doesn't Need:**
- ❌ GCP account/credentials
- ❌ gcloud CLI
- ❌ GCP Console access
- ❌ Understanding of GCP infrastructure
- ❌ IAM permissions setup

### **Time to Deploy:**
- **First time:** ~5 minutes (including Terraform download)
- **After first time:** ~2 minutes

---

## **Admin Responsibilities**

### **Before Distribution:**
- ✅ Create service account key (done)
- ✅ Package files
- ✅ Provide Lambda URL to client
- ✅ Provide Reasoning Engine IDs to client

### **During Client Setup:**
- ✅ Available for questions
- ✅ Verify client's Lambda URL format
- ✅ Help troubleshoot if needed

### **After Deployment:**
- ✅ Verify resources created in GCP Console
- ✅ Test end-to-end flow
- ✅ Rotate service account key periodically (every 90 days)

---

## **Security Model**

### **Client Has:**
- ✅ Service account key file
- ✅ Editor role on GCP project
- ✅ Can create Pub/Sub, Log Sink resources

### **Client Cannot:**
- ❌ Access GCP Console (no user account)
- ❌ See other project resources (no Console access)
- ❌ Modify IAM policies (key is scoped)
- ❌ Delete other resources (Terraform state isolated)

### **Key Rotation:**
Admin rotates key every 90 days:
```bash
# Delete old key
gcloud iam service-accounts keys delete OLD_KEY_ID \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com

# Create new key
gcloud iam service-accounts keys create appengine-sa-key-new.json \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com

# Redistribute to clients
```

---

## **Troubleshooting Guide**

### **Client Issues:**

| Client Says | Admin Response |
|-------------|----------------|
| "terraform not found" | Install from terraform.io/downloads |
| "Credentials not found" | Did you set GOOGLE_APPLICATION_CREDENTIALS? |
| "Access denied" | Send new appengine-sa-key.json file |
| "No logs appearing" | Verify Lambda URL and Engine ID are correct |

### **Admin Checks:**

```bash
# Check if client's resources were created
gcloud pubsub topics list --project=agentic-ai-integration-490716
gcloud pubsub subscriptions list --project=agentic-ai-integration-490716
gcloud logging sinks list --project=agentic-ai-integration-490716

# Check service account permissions
gcloud projects get-iam-policy agentic-ai-integration-490716 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:agentic-ai-integration-490716@appspot.gserviceaccount.com"
```

---

## **Summary**

✅ **Client workflow is simple:**
1. Set one environment variable
2. Edit 2 values in config file
3. Run 3 terraform commands

✅ **No GCP knowledge required**
✅ **No gcloud CLI needed**
✅ **No IAM/permissions setup**
✅ **5 minutes to deploy**

**The package in `client_package/` folder is ready to distribute!**
