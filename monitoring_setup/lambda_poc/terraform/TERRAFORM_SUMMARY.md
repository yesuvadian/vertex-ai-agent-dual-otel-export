# Terraform Deployment Summary

## 📋 **What Terraform Does**

Automates deployment of complete cross-cloud observability infrastructure from GCP to AWS.

---

## 🎯 **Terraform Scope**

### ✅ **1. GCP Agent Logging**
- **Automatic**: Vertex AI Reasoning Engines already log to Cloud Logging
- **Terraform**: Documents logging configuration, verifies engines exist
- **No explicit enable needed**: Logging is built-in

### ✅ **2. Log Sink and Pub/Sub (GCP)**
Creates:
- **Log Sink**: Filters logs from specific Reasoning Engines
- **Pub/Sub Topic**: Queues messages
- **Pub/Sub Subscription**: Push type, includes shared secret
- **Service Account**: For authentication
- **IAM Permissions**: Token creator, publisher roles

### ✅ **3. Lambda for All Customers (AWS)**
Creates:
- **Single Lambda Function**: Handles all customers
- **Customer Identification**: From GCP project/metadata
- **Dynamic Routing**: Routes to customer-specific endpoints
- **Size-Based Routing**:
  - Small traces (< 100 KB) → OTEL endpoint
  - Large traces (≥ 100 KB) → S3
  - All traces → Kinesis stream

### ✅ **4. Security - Shared Secret**
Creates:
- **AWS Secrets Manager**: Stores shared secret
- **GCP Secret Manager**: Stores same shared secret
- **Random Generation**: 64-character secure secret
- **Lambda Verification**: Validates secret on every request

---

## 🔐 **Required Permissions**

### **GCP Permissions**

```
Service Account/User needs:
├── roles/logging.configWriter      (Create Log Sinks)
├── roles/pubsub.admin              (Create Pub/Sub resources)
├── roles/iam.serviceAccountAdmin   (Create service accounts)
├── roles/iam.serviceAccountUser    (Use service accounts)
├── roles/resourcemanager.projectIamAdmin  (Grant permissions)
└── roles/secretmanager.admin       (Manage secrets)
```

**Quick Grant:**
```bash
# For service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="ROLE_NAME"

# For user
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL@example.com" \
  --role="ROLE_NAME"
```

### **AWS Permissions**

```
IAM User/Role needs:
├── Lambda Management (create, update, delete functions)
├── IAM Role Management (create roles, attach policies)
├── S3 Management (create buckets, lifecycle policies)
├── Kinesis Management (create streams)
├── CloudWatch Logs (create log groups)
└── Secrets Manager (create, access secrets)
```

**Quick Setup:**
```bash
# Option 1: Managed policies (easier)
aws iam attach-user-policy --user-name terraform-user \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

aws iam attach-user-policy --user-name terraform-user \
  --policy-arn arn:aws:iam::aws:policy/IAMFullAccess

# Option 2: Custom policy (more secure)
# See TERRAFORM_PERMISSIONS.md for minimal policy JSON
```

---

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# Install Terraform
brew install terraform  # Mac
# OR
choco install terraform  # Windows

# Verify versions
terraform --version  # >= 1.0
gcloud --version
aws --version
```

### **Authentication**
```bash
# GCP
gcloud auth application-default login
# OR
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# AWS
aws configure
# OR
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

### **Deployment Steps**

```bash
# 1. Navigate to terraform directory
cd terraform/

# 2. Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

# 3. Package Lambda code
zip -r lambda_package.zip lambda_multi_customer.py

# 4. Initialize Terraform
terraform init

# 5. Plan (dry run - see what will be created)
terraform plan

# 6. Apply (create resources)
terraform apply
# Type: yes

# 7. Verify
terraform output
```

---

## 📦 **What Gets Created**

### **GCP Resources**
```
✓ Pub/Sub Topic: reasoning-engine-logs-topic
✓ Pub/Sub Subscription: reasoning-engine-to-oidc (Push)
✓ Service Account: pubsub-oidc-invoker@...
✓ Log Sink: reasoning-engine-to-pubsub
✓ Secret: aws-lambda-shared-secret
✓ IAM Bindings: Token creator, Publisher roles
```

### **AWS Resources**
```
✓ Lambda Function: gcp-pubsub-multi-customer-processor
✓ Lambda Function URL: https://...lambda-url.us-east-1.on.aws/
✓ IAM Role: Lambda execution role
✓ S3 Buckets: per-customer trace storage
✓ Kinesis Streams: per-customer real-time streaming
✓ CloudWatch Log Group: /aws/lambda/...
✓ Secret: gcp-pubsub-shared-secret
```

---

## 🔄 **Multi-Customer Support**

### **How It Works**

```
Single Lambda Function
         │
         ├─ Identifies customer from:
         │  ├─ Message attributes (customer_id)
         │  ├─ GCP project_id
         │  └─ Reasoning engine_id
         │
         ├─ Routes to customer-specific:
         │  ├─ OTEL endpoint
         │  ├─ S3 bucket
         │  └─ Kinesis stream
         │
         └─ Size-based routing:
            ├─ < 100 KB → OTEL (real-time)
            ├─ ≥ 100 KB → S3 (storage)
            └─ All → Kinesis (streaming)
```

### **Adding New Customer**

Edit `terraform.tfvars`:
```hcl
portal26_endpoints = {
  "customer1" = { ... },
  "new_customer" = {
    otel_endpoint  = "https://newcustomer.portal26.com/v1/traces"
    s3_bucket      = "portal26-newcustomer-traces"
    kinesis_stream = "portal26-newcustomer-stream"
    customer_id    = "cust-003"
  }
}
```

Run:
```bash
terraform apply
```

---

## 🔐 **Shared Secret Security**

### **How It Works**

```
1. Terraform generates random 64-char secret
         ↓
2. Stores in AWS Secrets Manager
         ↓
3. Stores in GCP Secret Manager
         ↓
4. GCP Pub/Sub reads from Secret Manager
         ↓
5. Adds secret to message attributes
         ↓
6. AWS Lambda reads from Secrets Manager
         ↓
7. Compares secrets (constant-time)
         ↓
8. ✅ Match → Process OR ❌ Mismatch → Reject (403)
```

### **Why Shared Secret (Not OIDC)?**

**Note**: GCP Pub/Sub **does NOT support custom HTTP headers**.

Options:
1. **OIDC/JWT**: Requires header support ❌
2. **Shared Secret in attributes**: Works! ✅
3. **Shared Secret in payload**: Works but less clean

**Terraform uses**: Shared Secret in message attributes

---

## 📊 **Testing**

### **Test Lambda Directly**
```bash
aws lambda invoke \
  --function-name gcp-pubsub-multi-customer-processor \
  --payload '{"test": "message"}' \
  response.json
```

### **Test End-to-End**
```bash
# Publish to Pub/Sub (with shared secret)
gcloud pubsub topics publish reasoning-engine-logs-topic \
  --message='{"test": "message"}' \
  --attribute=shared_secret=YOUR_SECRET,customer_id=customer1

# Wait 10 seconds, then check Lambda logs
aws logs tail /aws/lambda/gcp-pubsub-multi-customer-processor --since 1m
```

---

## 🗑️ **Cleanup**

```bash
# Destroy all resources
terraform destroy
# Type: yes

# WARNING: This deletes:
# - All S3 buckets and data
# - All Kinesis streams
# - Lambda function
# - Pub/Sub resources
# - Secrets
```

---

## 📂 **File Structure**

```
terraform/
├── main.tf                          ← Main config
├── gcp_agent_logging.tf             ← Agent logging docs
├── gcp_log_sink_pubsub.tf           ← Log Sink + Pub/Sub
├── aws_lambda_multi_customer.tf     ← Lambda + AWS resources
├── security_shared_secret.tf        ← Shared secret
├── lambda_multi_customer.py         ← Lambda code
├── lambda_package.zip               ← Lambda deployment
├── terraform.tfvars.example         ← Example variables
├── TERRAFORM_PERMISSIONS.md         ← Permissions guide
└── README.md                        ← Full documentation
```

---

## 🎯 **Key Terraform Commands**

```bash
terraform init          # Initialize (first time)
terraform plan          # Preview changes
terraform apply         # Create resources
terraform destroy       # Delete resources
terraform output        # Show outputs
terraform state list    # List resources
terraform validate      # Check syntax
terraform fmt           # Format code
```

---

## ✅ **Checklist Before Deployment**

### **GCP**
- [ ] Project ID is correct
- [ ] Reasoning Engine IDs are correct
- [ ] GCP authentication configured
- [ ] Required permissions granted
- [ ] Can run: `gcloud projects list`

### **AWS**
- [ ] AWS region is correct
- [ ] S3 bucket names are unique globally
- [ ] AWS authentication configured
- [ ] Required permissions granted
- [ ] Can run: `aws sts get-caller-identity`

### **Terraform**
- [ ] `terraform.tfvars` created and filled
- [ ] Lambda code packaged (`lambda_package.zip`)
- [ ] Portal26 endpoints configured
- [ ] Reviewed `terraform plan` output

---

## 🐛 **Common Issues**

### **Issue**: "Permission denied on resource project"
**Solution**: Grant `roles/resourcemanager.projectIamAdmin`

### **Issue**: "Error creating Pub/Sub topic"
**Solution**: Grant `roles/pubsub.admin`

### **Issue**: "Lambda deployment package too large"
**Solution**: Use Lambda layers for dependencies

### **Issue**: "S3 bucket name already exists"
**Solution**: S3 bucket names are globally unique, choose different name

---

## 📞 **For Teams Chat - Quick Copy**

```
📦 Terraform Deployment - GCP to AWS Observability

Scope:
✓ Log Sink + Pub/Sub (GCP)
✓ Lambda (AWS) - handles all customers
✓ Security: Shared secret authentication
✓ Multi-customer routing (OTEL/S3/Kinesis)

Required Permissions:
GCP: logging.configWriter, pubsub.admin, iam.serviceAccountAdmin, secretmanager.admin
AWS: Lambda, IAM, S3, Kinesis, Secrets Manager permissions

Quick Start:
1. terraform init
2. terraform plan
3. terraform apply

What It Creates:
GCP: Log Sink, Pub/Sub Topic+Subscription, Service Account
AWS: Lambda, S3 Buckets, Kinesis Streams, Secrets

Result: Complete automated cross-cloud observability!
```

---

This Terraform configuration provides **Infrastructure as Code** for the entire GCP → AWS observability pipeline!
