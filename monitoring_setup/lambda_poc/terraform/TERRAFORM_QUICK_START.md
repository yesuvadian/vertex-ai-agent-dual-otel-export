# Terraform Infrastructure - Quick Start

## 🎯 **What This Does**

Deploys cross-cloud monitoring: GCP AI agents → AWS Lambda

**Flow:** GCP logs → Pub/Sub → AWS Lambda → Portal26

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
# GCP
gcloud auth application-default login

# AWS
aws configure
```

**Permissions:** See `TERRAFORM_PERMISSIONS.md`

---

## 🚀 **Deploy in 5 Steps**

### **Step 1: Configure**
```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
```

### **Step 2: Edit Variables**
Edit `terraform.tfvars`:
```hcl
gcp_project_id = "your-project-id"
reasoning_engine_ids = ["your-engine-id"]
log_severity_filter = ["ERROR", "CRITICAL"]  # Recommended
```

### **Step 3: Initialize**
```bash
terraform init
```

### **Step 4: Plan**
```bash
terraform plan
```

### **Step 5: Deploy**
```bash
terraform apply
```

**Done!** Takes 5-10 minutes.

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

### **Customer Endpoints**
```hcl
portal26_endpoints = {
  "customer1" = {
    otel_endpoint  = "https://customer1.portal26.com/v1/traces"
    s3_bucket      = "unique-bucket-name"
    kinesis_stream = "stream-name"
    customer_id    = "cust-001"
  }
}
```

---

## 📊 **What Gets Created**

**GCP:**
- Log Sink (with filters)
- Pub/Sub Topic & Subscription
- Service Account (OIDC)
- Secret Manager (shared secret)

**AWS:**
- Lambda Function (multi-customer router)
- Lambda Function URL
- S3 Buckets (per customer)
- Kinesis Streams (per customer)
- Secrets Manager (shared secret)

---

## 🧪 **Testing**

```bash
# Check outputs
terraform output

# Test Lambda
aws lambda invoke \
  --function-name gcp-pubsub-multi-customer-processor \
  --payload '{"test": "message"}' \
  response.json

# View logs
aws logs tail /aws/lambda/gcp-pubsub-multi-customer-processor --follow
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

### **Add Customer**
```hcl
portal26_endpoints = {
  # ... existing ...
  "new_customer" = { ... }
}
```
```bash
terraform apply
```

---

## 🗑️ **Cleanup**

```bash
terraform destroy
```

**Warning:** Deletes all resources and data!

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
