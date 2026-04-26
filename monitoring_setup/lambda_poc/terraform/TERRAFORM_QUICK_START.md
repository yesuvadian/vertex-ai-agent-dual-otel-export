# Terraform Infrastructure - Quick Start

## 🎯 **What This Does**

Connects GCP AI agent logs to your existing AWS Lambda infrastructure.

**Flow:** GCP logs → Pub/Sub → Your existing AWS Lambda → Portal26

---

## 📋 **Prerequisites**

**Tools:**
```bash
terraform --version  # >= 1.0
gcloud --version
aws --version
```

**Authentication:**
```bash
# GCP (required)
gcloud auth application-default login
```

**AWS Lambda:**
- Have your Lambda Function URL ready (from existing deployment)

**Permissions:** See `TERRAFORM_PERMISSIONS.md`

---

## 🚀 **Deploy in 6 Steps**

### **Step 1: Bootstrap (First Time Only)**
```bash
cd terraform/
terraform init
terraform apply -target=google_service_account.oidc_auth
```

This creates the GCP service account needed for OIDC authentication. Copy the service account email from the output.

### **Step 2: Configure AWS Lambda**
Add the GCP service account email to your Lambda's OIDC configuration (see Lambda setup docs).

### **Step 3: Configure Terraform**
```bash
cp terraform.tfvars.example terraform.tfvars
```

### **Step 4: Edit Variables**
Edit `terraform.tfvars`:
```hcl
gcp_project_id = "your-project-id"
reasoning_engine_ids = ["your-engine-id"]
aws_lambda_url = "https://your-lambda-url.lambda-url.us-east-1.on.aws/"
log_severity_filter = ["ERROR", "CRITICAL"]  # Recommended
```

### **Step 5: Plan**
```bash
terraform plan
```

### **Step 6: Deploy**
```bash
terraform apply
```

**Done!** Takes 2-3 minutes.

---

## 🎛️ **Key Configuration Options**

### **Filter Settings (Cost Optimization)**
```hcl
# Option 1: Errors only (Recommended - 80% savings)
log_severity_filter = ["ERROR", "CRITICAL"]

# Option 2: Everything (Testing only)
log_severity_filter = []

# Option 3: Specific agents
agent_ids = ["agent-001"]
log_severity_filter = ["ERROR"]
```

### **AWS Lambda URL**
```hcl
# Required: URL of your existing Lambda Function
aws_lambda_url = "https://your-lambda-url.lambda-url.us-east-1.on.aws/"
```

---

## 📊 **What Gets Created**

**GCP Resources (Created by Terraform):**
- Log Sink (with filters)
- Pub/Sub Topic & Subscription
- Service Account (for OIDC authentication)
- IAM Bindings (Pub/Sub push permissions)

**AWS Resources (Pre-existing):**
- Lambda Function (already deployed)
- Lambda Function URL (provided as variable)

---

## 🧪 **Testing**

```bash
# Check Terraform outputs
terraform output

# Trigger a test log in GCP to verify flow
gcloud logging write test-log "Test message" --severity=ERROR

# Check GCP Pub/Sub
gcloud pubsub subscriptions pull reasoning-engine-to-aws --limit=1

# Check your Lambda logs (adjust function name as needed)
# AWS CLI or AWS Console
```

---

## 🔄 **Making Changes**

### **Add New Agent**
```hcl
reasoning_engine_ids = [
  "existing-id",
  "new-id"  # Add here
]
```
```bash
terraform apply
```

### **Change Filters**
```hcl
log_severity_filter = ["WARNING", "ERROR", "CRITICAL"]  # Changed
```
```bash
terraform apply
```

### **Update Lambda URL**
```hcl
aws_lambda_url = "https://new-lambda-url.lambda-url.us-east-1.on.aws/"
```
```bash
terraform apply
```

---

## 🗑️ **Cleanup**

```bash
terraform destroy
```

**Note:** This only deletes GCP resources (Log Sink, Pub/Sub). Your AWS Lambda remains unchanged.

---

## 🐛 **Troubleshooting**

### **No logs in Lambda?**
```bash
# Test filter
gcloud logging read 'YOUR_FILTER' --limit=5

# Check sink
gcloud logging sinks describe reasoning-engine-to-pubsub
```

### **Too many logs (high cost)?**
```hcl
# Add severity filter
log_severity_filter = ["ERROR", "CRITICAL"]
```

### **Permission errors?**
See `TERRAFORM_PERMISSIONS.md`

---

## 📚 **Documentation**

- **Filters:** `FILTERS_OVERVIEW.md` (high-level), `LOG_SINK_FILTERS_GUIDE.md` (detailed)
- **Business:** `LOG_SINK_FILTERS_BUSINESS_OVERVIEW.md`
- **Architecture:** `TERRAFORM_ARCHITECTURE.md`
- **Permissions:** `TERRAFORM_PERMISSIONS.md`

---

## 💰 **Cost Optimization Tips**

1. **Use severity filters** (save 80-90%)
   ```hcl
   log_severity_filter = ["ERROR", "CRITICAL"]
   ```

2. **Filter by environment**
   ```hcl
   custom_log_filter = "labels.environment=\"production\""
   ```

3. **Monitor and adjust**
   - Check costs weekly
   - Adjust filters as needed

---

## 🔑 **Key Takeaways**

- ✅ Filters are optional but recommended
- ✅ Start with ERROR logs only (huge savings)
- ✅ Test filters before deploying
- ✅ Monitor costs and adjust
- ✅ Easy to update after deployment

---

**Need Help?**
- Check README.md
- Review filter examples in FILTERS_OVERVIEW.md
- Test in GCP Logs Explorer first
