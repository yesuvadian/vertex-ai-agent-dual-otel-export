# Client Setup Guide - GCP Log Sink to AWS Lambda

## 📦 What You Received

This package contains everything you need to forward GCP logs to your AWS Lambda:
- `main.tf` - Main Terraform configuration
- `gcp_log_sink_pubsub.tf` - Log sink and Pub/Sub setup
- `terraform.tfvars.example` - Configuration template
- `appengine-sa-key.json` - Service account credentials (KEEP SECURE!)

## ⚙️ Prerequisites

You need:
- ✅ Terraform installed ([Download](https://www.terraform.io/downloads))
- ✅ Your AWS Lambda Function URL
- ✅ Your Reasoning Engine IDs (from GCP)

## 🚀 Setup Steps (3 Steps Only!)

### **Step 1: Configure Authentication**

**Windows PowerShell:**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"
```

**Windows CMD:**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\appengine-sa-key.json
```

**Linux/Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
```

### **Step 2: Configure Your Settings**

```bash
# Copy the example file
copy terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars and update:
```

Open `terraform.tfvars` and change:

```hcl
# Line 1: Leave as-is (already set)
gcp_project_id = "agentic-ai-integration-490716"

# Line 2: CHANGE THIS - Your AWS Lambda URL
aws_lambda_url = "https://YOUR-LAMBDA-URL.lambda-url.us-east-1.on.aws"

# Line 3: CHANGE THIS - Your Reasoning Engine IDs
reasoning_engine_ids = [
  "8213677864684355584"  # Replace with your ID
]
```

### **Step 3: Deploy Infrastructure**

```bash
# Initialize Terraform
terraform init

# Preview what will be created
terraform plan

# Deploy (type 'yes' when prompted)
terraform apply
```

## ✅ What Gets Created

After deployment, you'll have:
- ✅ **Pub/Sub Topic**: `reasoning-engine-logs-topic`
- ✅ **Pub/Sub Subscription**: Pushes logs to your Lambda
- ✅ **Log Sink**: Filters and routes GCP logs

## 🧪 Testing

After deployment:

1. **Generate a log** in your GCP Reasoning Engine
2. **Check your AWS Lambda logs** in CloudWatch
3. You should see incoming messages from GCP Pub/Sub

## 🔧 Troubleshooting

### Issue: "Application Default Credentials not found"
**Solution:** Make sure you ran Step 1 (set `GOOGLE_APPLICATION_CREDENTIALS`)

### Issue: "terraform: command not found"
**Solution:** Install Terraform from https://www.terraform.io/downloads

### Issue: "No logs appearing in Lambda"
**Solution:** 
- Check Lambda URL is correct in `terraform.tfvars`
- Verify Lambda is accessible (public URL)
- Check Reasoning Engine ID is correct

### Issue: "Access denied" errors
**Solution:** Contact your admin - the service account key may be expired

## 🗑️ Cleanup

To remove all resources:

```bash
terraform destroy
```

Type `yes` when prompted.

## ⚠️ Security Notes

- **NEVER commit `appengine-sa-key.json` to git**
- **NEVER share the key file publicly**
- Keep `terraform.tfvars` private (contains your Lambda URL)
- This setup has NO authentication - use for testing only
- For production, ask your admin about the OIDC version

## 📞 Need Help?

Contact your GCP administrator if you encounter issues with:
- Service account permissions
- GCP project access
- Key file expiration

---

**That's it! Just 3 steps to get GCP logs flowing to your AWS Lambda.**
