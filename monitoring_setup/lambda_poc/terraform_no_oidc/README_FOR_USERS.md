# Terraform Setup - For Users Without gcloud CLI

## 📋 **Prerequisites**

You need:
1. ✅ Terraform installed (`terraform --version`)
2. ✅ Service account key file: `appengine-sa-key.json` (provided separately)
3. ❌ **NO gcloud CLI needed!**

---

## 🚀 **Setup Steps**

### **Step 1: Get the Files**

You should have:
```
terraform_no_oidc/
├── main.tf
├── gcp_log_sink_pubsub.tf
├── terraform.tfvars.example
├── appengine-sa-key.json           ← Key file (provided)
└── README_FOR_USERS.md             ← This file
```

**If you don't have `appengine-sa-key.json`:**
- Ask the admin to provide it
- It authenticates Terraform to GCP

---

### **Step 2: Set Authentication**

**Choose your operating system:**

#### **Linux/Mac:**
```bash
cd terraform_no_oidc/

export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"

# Verify it's set
echo $GOOGLE_APPLICATION_CREDENTIALS
```

#### **Windows PowerShell:**
```powershell
cd terraform_no_oidc\

$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"

# Verify it's set
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```

#### **Windows CMD:**
```cmd
cd terraform_no_oidc\

set GOOGLE_APPLICATION_CREDENTIALS=%cd%\appengine-sa-key.json

# Verify it's set
echo %GOOGLE_APPLICATION_CREDENTIALS%
```

---

### **Step 3: Configure Terraform**

```bash
# Create configuration file
cp terraform.tfvars.example terraform.tfvars

# Edit the file (use any text editor)
notepad terraform.tfvars    # Windows
nano terraform.tfvars       # Linux
vim terraform.tfvars        # Linux/Mac
```

**Update these values:**
```hcl
# Your AWS Lambda URL (required)
aws_lambda_url = "https://YOUR-LAMBDA-URL.lambda-url.us-east-1.on.aws"

# Your Reasoning Engine IDs (required)
reasoning_engine_ids = [
  "YOUR_ENGINE_ID_HERE"
]

# Cost optimization (optional but recommended)
log_severity_filter = ["ERROR", "CRITICAL"]
```

**Where to get these values:**
- `aws_lambda_url`: From AWS Console → Lambda → Your Function → Configuration → Function URL
- `reasoning_engine_ids`: Provided by admin or from GCP Console

---

### **Step 4: Initialize Terraform**

```bash
terraform init
```

**Expected output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
- Installing hashicorp/google v5.x.x...

Terraform has been successfully initialized!
```

✅ **If you see this** - continue to next step

❌ **If you see errors**:
- Check `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
- Check `appengine-sa-key.json` exists in current directory
- Check you're in `terraform_no_oidc/` directory

---

### **Step 5: Preview Changes**

```bash
terraform plan
```

**Expected output:**
```
Terraform will perform the following actions:

  # google_logging_project_sink.reasoning_engine_to_pubsub will be created
  + resource "google_logging_project_sink" ...

  # google_pubsub_topic.reasoning_engine_logs will be created
  + resource "google_pubsub_topic" ...

  # google_pubsub_subscription.reasoning_engine_to_lambda will be created
  + resource "google_pubsub_subscription" ...

  # google_pubsub_topic_iam_member.log_sink_publisher will be created
  + resource "google_pubsub_topic_iam_member" ...

Plan: 4 to add, 0 to change, 0 to destroy.
```

✅ **Review this carefully** - it shows what will be created

---

### **Step 6: Deploy**

```bash
terraform apply
```

Terraform will ask for confirmation:
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value:
```

**Type:** `yes` and press Enter

**Wait 1-2 minutes...**

**Success output:**
```
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

setup_complete = <<EOT
============================================================================
GCP Log Sink Deployment Complete!
============================================================================

GCP Resources Created:
- Pub/Sub Topic: reasoning-engine-logs-topic
- Pub/Sub Subscription: reasoning-engine-to-lambda
- Log Sink: reasoning-engine-to-pubsub

Target Endpoint:
- Your AWS Lambda: https://...
...
```

✅ **Done!** Resources are created in GCP

---

## 🧪 **Verification**

### **Check What Was Created:**

```bash
# View Terraform state
terraform show

# List outputs
terraform output

# See specific output
terraform output lambda_target_url
```

### **Check in AWS:**

Monitor your Lambda function logs to see if messages are arriving:
```bash
# If you have AWS CLI
aws logs tail /aws/lambda/YOUR_FUNCTION_NAME --follow
```

Or check AWS Console → Lambda → Your Function → Monitor → View CloudWatch logs

---

## 🔄 **Making Changes**

### **Update Configuration:**

1. Edit `terraform.tfvars`
2. Run `terraform plan` to preview changes
3. Run `terraform apply` to apply changes

### **Example: Add More Reasoning Engines**

Edit `terraform.tfvars`:
```hcl
reasoning_engine_ids = [
  "8213677864684355584",
  "NEW_ENGINE_ID_HERE"    # Add new ID
]
```

Then:
```bash
terraform plan
terraform apply
```

---

## 🗑️ **Cleanup (Remove Resources)**

When you want to remove all GCP resources:

```bash
terraform destroy
```

Type `yes` to confirm.

**This will delete:**
- Pub/Sub Topic
- Pub/Sub Subscription
- Log Sink

**Your AWS Lambda is NOT affected** - it remains unchanged

---

## 🐛 **Troubleshooting**

### **Error: "Application Default Credentials not found"**

**Cause:** `GOOGLE_APPLICATION_CREDENTIALS` not set

**Solution:**
```bash
# Make sure environment variable is set
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"

# Then try again
terraform plan
```

---

### **Error: "appengine-sa-key.json: no such file"**

**Cause:** Key file missing or wrong path

**Solution:**
```bash
# Check file exists
ls appengine-sa-key.json

# If missing, ask admin for the file
# Place it in terraform_no_oidc/ directory
```

---

### **Error: "Permission denied"**

**Cause:** Service account lacks permissions

**Solution:**
- Contact admin to verify service account has Editor role
- Service account email: `agentic-ai-integration-490716@appspot.gserviceaccount.com`

---

### **No logs appearing in Lambda**

**Possible causes:**

1. **Filter too restrictive**
   - Check `log_severity_filter` in `terraform.tfvars`
   - Try removing filter temporarily: `log_severity_filter = []`

2. **Wrong reasoning engine ID**
   - Verify ID in `terraform.tfvars` is correct
   - Ask admin for correct IDs

3. **Lambda URL incorrect**
   - Check `aws_lambda_url` in `terraform.tfvars`
   - Must be complete HTTPS URL from AWS

---

## 📝 **Important Notes**

### **Authentication in Future Sessions**

Every time you open a new terminal, you must set the environment variable again:

**Linux/Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/appengine-sa-key.json"
```

**Windows:**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\full\path\to\appengine-sa-key.json"
```

**Tip:** Add this to your shell profile to make it permanent

---

### **Security**

- 🔒 Keep `appengine-sa-key.json` secure
- ❌ Never commit it to git
- ❌ Never share it publicly
- ✅ Store in secure location
- ✅ Delete when no longer needed

---

### **Multiple Environments**

For different environments (dev, staging, prod):

1. Create separate directories:
   ```
   terraform_no_oidc_dev/
   terraform_no_oidc_staging/
   terraform_no_oidc_prod/
   ```

2. Use different `terraform.tfvars` for each

3. Use same service account key file for all

---

## ✅ **Quick Reference**

### **Initial Setup:**
```bash
cd terraform_no_oidc/
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform plan
terraform apply
```

### **Daily Usage:**
```bash
cd terraform_no_oidc/
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
terraform plan
terraform apply
```

### **Cleanup:**
```bash
terraform destroy
```

---

## 📞 **Getting Help**

**Common Issues:**

| Issue | Solution |
|-------|----------|
| No key file | Ask admin for `appengine-sa-key.json` |
| Permission errors | Contact admin to check service account permissions |
| Wrong Lambda URL | Get correct URL from AWS Console |
| No logs appearing | Check filters and reasoning engine IDs |

**Contact your admin for:**
- Service account key file
- Reasoning engine IDs
- AWS Lambda URL
- GCP project access issues

---

**No gcloud CLI needed - just Terraform!** 🚀
