# Terraform Infrastructure - Teams Summary

## 📦 **Quick Overview for Teams**

```
🎯 Terraform Scope
──────────────────────────────────────────────
1. ✅ GCP Agent Logging (automatic - documented)
2. ✅ Log Sink + Pub/Sub (GCP)
3. ✅ Single Lambda for all customers (AWS)
4. ✅ Shared Secret authentication

Result: Complete Infrastructure as Code!
```

---

## 🏗️ **What Gets Created**

### **GCP Side**
```
✓ Log Sink: reasoning-engine-to-pubsub
  └─ Filters logs from 3 specific Reasoning Engines
  
✓ Pub/Sub Topic: reasoning-engine-logs-topic
  └─ Message queue (7-day retention)
  
✓ Pub/Sub Subscription: reasoning-engine-to-oidc
  └─ Push type → sends to AWS Lambda URL
  └─ Includes shared secret in attributes
  
✓ Service Account: pubsub-oidc-invoker@...
  └─ Role: Token Creator
  
✓ Secret Manager: aws-lambda-shared-secret
  └─ Stores 64-character shared secret
  
✓ IAM Permissions: Auto-configured
```

### **AWS Side**
```
✓ Lambda Function: gcp-pubsub-multi-customer-processor
  └─ Handles ALL customers in one function
  └─ Verifies shared secret
  └─ Routes by customer + size
  
✓ Lambda Function URL: https://...lambda-url...
  └─ Public endpoint (auth in code)
  
✓ S3 Buckets: Per customer
  └─ portal26-customer1-traces
  └─ portal26-customer2-traces
  └─ For large traces (≥ 100 KB)
  
✓ Kinesis Streams: Per customer
  └─ portal26-customer1-stream
  └─ portal26-customer2-stream
  └─ Real-time streaming (all traces)
  
✓ Secrets Manager: gcp-pubsub-shared-secret
  └─ Same 64-char secret as GCP
  
✓ CloudWatch Logs: /aws/lambda/...
  └─ Lambda execution logs (30-day retention)
```

---

## 🔐 **Required Permissions**

### **GCP**
```
Grant these roles to Terraform service account/user:
├─ roles/logging.configWriter
├─ roles/pubsub.admin
├─ roles/iam.serviceAccountAdmin
├─ roles/iam.serviceAccountUser
├─ roles/resourcemanager.projectIamAdmin
└─ roles/secretmanager.admin

Quick grant command:
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="ROLE_NAME"
```

### **AWS**
```
Grant these permissions to Terraform IAM user/role:
├─ Lambda Management (create, update, delete)
├─ IAM Role Management (create roles, policies)
├─ S3 Management (create buckets, lifecycle)
├─ Kinesis Management (create streams)
├─ Secrets Manager (create, access secrets)
└─ CloudWatch Logs (create log groups)

Option 1 (Quick): PowerUserAccess + IAMFullAccess
Option 2 (Secure): Custom policy (see TERRAFORM_PERMISSIONS.md)
```

---

## 🚀 **Deployment Steps**

```bash
# 1. Setup
cd terraform/
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your values

# 2. Package Lambda
zip -r lambda_package.zip lambda_multi_customer.py

# 3. Initialize
terraform init

# 4. Plan (Preview)
terraform plan
# Review: What will be created?

# 5. Deploy
terraform apply
# Type: yes

# 6. Verify
terraform output
```

**Time**: ~5-10 minutes

---

## 🎯 **Multi-Customer Architecture**

```
Single Lambda Function
         │
         ├─ Receives from GCP Pub/Sub
         │
         ├─ Verifies shared secret ✓
         │
         ├─ Identifies customer:
         │  ├─ Message attributes (customer_id)
         │  ├─ GCP project_id
         │  └─ Reasoning engine_id
         │
         ├─ Consolidates data:
         │  ├─ logs → structured
         │  ├─ traces → extracted
         │  └─ metrics → calculated
         │
         └─ Routes based on size:
            ├─ < 100 KB  → Portal26 OTEL
            ├─ ≥ 100 KB  → Customer S3
            └─ All sizes → Customer Kinesis
```

---

## 🔐 **Shared Secret Flow**

```
1. Terraform generates random 64-char secret
         ↓
2. Stores in AWS Secrets Manager
         ↓
3. Stores in GCP Secret Manager
         ↓
4. GCP Pub/Sub reads from Secret Manager
         ↓
5. Adds to message attributes: shared_secret=...
         ↓
6. Sends to AWS Lambda
         ↓
7. Lambda reads from AWS Secrets Manager
         ↓
8. Compares (constant-time comparison)
         ↓
9. ✅ Match → Process | ❌ Mismatch → 403 Forbidden
```

**Why shared secret?**
- GCP Pub/Sub doesn't support custom HTTP headers
- Shared secret in attributes is the secure alternative
- Rotatable via Terraform

---

## 📊 **Adding New Customer**

```bash
# 1. Edit terraform.tfvars
portal26_endpoints = {
  "customer1" = { ... },
  "customer2" = { ... },
  "new_customer" = {  # ← Add this
    otel_endpoint  = "https://newcust.portal26.com/v1/traces"
    s3_bucket      = "portal26-newcust-traces"
    kinesis_stream = "portal26-newcust-stream"
    customer_id    = "cust-003"
  }
}

# 2. Apply
terraform apply

# Result: New S3 bucket + Kinesis stream created
# Lambda automatically routes to new customer
```

---

## 🗑️ **Cleanup**

```bash
terraform destroy
# Type: yes

⚠️  WARNING: Deletes ALL resources including:
- S3 buckets and ALL trace data
- Kinesis streams
- Lambda function
- Pub/Sub resources
- Secrets
```

---

## ✅ **Pre-Deployment Checklist**

```
GCP:
☐ Project ID correct
☐ Reasoning Engine IDs correct
☐ GCP authenticated (gcloud auth list)
☐ Permissions granted
☐ Can run: gcloud projects list

AWS:
☐ Region correct
☐ S3 bucket names unique globally
☐ AWS authenticated (aws sts get-caller-identity)
☐ Permissions granted
☐ Can run: aws lambda list-functions

Terraform:
☐ terraform.tfvars created
☐ Lambda code packaged (lambda_package.zip)
☐ Portal26 endpoints configured
☐ terraform plan looks good
```

---

## 🐛 **Common Issues**

| Issue | Solution |
|-------|----------|
| "Permission denied" | Check TERRAFORM_PERMISSIONS.md |
| "Bucket already exists" | S3 names must be globally unique |
| "Lambda package too large" | Use Lambda layers for dependencies |
| "Pub/Sub not receiving" | Check Log Sink filter matches engine IDs |

---

## 📂 **File Structure**

```
terraform/
├── main.tf                          # Main config
├── gcp_agent_logging.tf             # Agent logging
├── gcp_log_sink_pubsub.tf           # Log Sink + Pub/Sub
├── aws_lambda_multi_customer.tf     # Lambda + AWS
├── security_shared_secret.tf        # Shared secret
├── lambda_multi_customer.py         # Lambda code
├── lambda_package.zip               # Deployment package
├── terraform.tfvars.example         # Example vars
├── TERRAFORM_PERMISSIONS.md         # Permissions guide
├── TERRAFORM_SUMMARY.md             # Detailed summary
├── TERRAFORM_ARCHITECTURE.md        # Visual diagrams
└── README.md                        # Full docs
```

---

## 📝 **Key Terraform Commands**

```bash
terraform init       # Initialize (first time)
terraform plan       # Preview changes
terraform apply      # Create resources
terraform destroy    # Delete everything
terraform output     # Show outputs
terraform state list # List all resources
```

---

## 🎯 **What You Get**

```
Complete automated deployment of:
✓ GCP Log Sink → filters by engine ID
✓ GCP Pub/Sub → queues + forwards to AWS
✓ AWS Lambda → processes all customers
✓ Per-customer S3 → large trace storage
✓ Per-customer Kinesis → real-time streaming
✓ Shared secret auth → secure cross-cloud
✓ CloudWatch monitoring → execution logs

Result: Production-ready observability pipeline!
```

---

## 💼 **For Architect Review**

```
📋 Infrastructure Scope Document

Components Managed by Terraform:
1. GCP Log Sink + Pub/Sub pipeline
2. AWS Lambda (multi-tenant architecture)
3. Per-customer S3 + Kinesis resources
4. Cross-cloud authentication (shared secret)
5. IAM roles and permissions (both clouds)

Security Model:
- Shared secret (64-char random)
- Stored in both cloud secret managers
- Verified on every request
- Rotatable without downtime

Scalability:
- Single Lambda handles all customers
- Auto-scaling (serverless)
- Size-based routing (OTEL/S3/Kinesis)
- No infrastructure limits

Cost:
- Infrastructure as Code = reproducible
- Multi-tenant = efficient
- Pay-per-use = cost-effective

Next Steps:
1. Review terraform.tfvars configuration
2. Validate permissions on both clouds
3. Run terraform plan (dry-run)
4. Deploy with terraform apply
5. Test end-to-end flow
```

---

**Ready to deploy?** Follow the deployment steps above!

**Questions?** Check README.md for full documentation.
