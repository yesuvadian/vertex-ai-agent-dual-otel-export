# Terraform Required Permissions

## 📋 **Overview**

This document lists all required IAM permissions for running Terraform to deploy the GCP-AWS observability infrastructure.

---

## 🔐 **GCP Permissions**

### User/Service Account Requirements

The user or service account running Terraform needs these GCP roles:

#### **Core Roles**

```bash
# Grant to your Terraform service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="ROLE_NAME"
```

| Role | Purpose | Specific Permissions |
|------|---------|---------------------|
| `roles/logging.configWriter` | Create and manage Log Sinks | `logging.sinks.create`<br>`logging.sinks.update`<br>`logging.sinks.delete`<br>`logging.sinks.list` |
| `roles/pubsub.admin` | Create and manage Pub/Sub resources | `pubsub.topics.create`<br>`pubsub.topics.setIamPolicy`<br>`pubsub.subscriptions.create`<br>`pubsub.subscriptions.update` |
| `roles/iam.serviceAccountAdmin` | Create service accounts for OIDC | `iam.serviceAccounts.create`<br>`iam.serviceAccounts.delete`<br>`iam.serviceAccounts.get` |
| `roles/iam.serviceAccountUser` | Use service accounts | `iam.serviceAccounts.actAs` |
| `roles/resourcemanager.projectIamAdmin` | Grant IAM permissions | `resourcemanager.projects.setIamPolicy`<br>`resourcemanager.projects.getIamPolicy` |

#### **Optional (for verification)**

| Role | Purpose |
|------|---------|
| `roles/aiplatform.user` | Verify Reasoning Engines exist |

### Minimal Custom Role (Alternative)

If you want a custom role with minimal permissions:

```bash
gcloud iam roles create terraformGCPDeployment \
  --project=PROJECT_ID \
  --title="Terraform GCP Deployment" \
  --description="Minimal permissions for Terraform to deploy observability infrastructure" \
  --permissions="\
logging.sinks.create,\
logging.sinks.update,\
logging.sinks.delete,\
logging.sinks.get,\
logging.sinks.list,\
pubsub.topics.create,\
pubsub.topics.delete,\
pubsub.topics.get,\
pubsub.topics.setIamPolicy,\
pubsub.topics.getIamPolicy,\
pubsub.subscriptions.create,\
pubsub.subscriptions.update,\
pubsub.subscriptions.delete,\
pubsub.subscriptions.get,\
iam.serviceAccounts.create,\
iam.serviceAccounts.delete,\
iam.serviceAccounts.get,\
iam.serviceAccounts.actAs,\
resourcemanager.projects.get,\
resourcemanager.projects.getIamPolicy,\
resourcemanager.projects.setIamPolicy"
```

---

## 🔐 **AWS Permissions**

**No AWS permissions needed** - Terraform uses existing AWS Lambda infrastructure.

The `aws_lambda_url` variable points to your pre-deployed Lambda function. Terraform only creates GCP resources (Log Sink + Pub/Sub) that forward to this existing Lambda.

---

## 🛠️ **Setup Instructions**

### GCP Setup

#### Option 1: Using Service Account (Recommended)

```bash
# 1. Create service account for Terraform
gcloud iam service-accounts create terraform-deployer \
  --display-name="Terraform Deployer" \
  --project=PROJECT_ID

# 2. Grant required roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.configWriter"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountAdmin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.projectIamAdmin"

# 3. Create and download key
gcloud iam service-accounts keys create terraform-key.json \
  --iam-account=terraform-deployer@PROJECT_ID.iam.gserviceaccount.com

# 4. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="./terraform-key.json"
```

#### Option 2: Using User Account

```bash
# Authenticate as user
gcloud auth application-default login

# Grant yourself the roles (requires Project IAM Admin)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/logging.configWriter"

# Repeat for other roles...
```

---

## 🔒 **Security Best Practices**

### 1. Principle of Least Privilege
- Only grant permissions actually needed
- Use custom roles instead of broad managed roles
- Review permissions regularly

### 2. Service Account Keys
- **GCP**: Store JSON key file securely, rotate regularly
- **AWS**: Use AWS Secrets Manager for access keys
- Never commit keys to version control

### 3. Terraform State
- Store state in secure backend (GCS, S3)
- Enable versioning
- Encrypt state files
- Restrict access to state bucket

```hcl
# Example: GCS backend with encryption
terraform {
  backend "gcs" {
    bucket = "terraform-state-bucket"
    prefix = "observability-infrastructure"
  }
}
```

### 4. Temporary Credentials
- Use short-lived credentials when possible
- GCP: Workload Identity Federation
- AWS: AssumeRole with temporary credentials

---

## ✅ **Verification Checklist**

Before running Terraform, verify:

### GCP
- [ ] Service account created
- [ ] All required roles granted
- [ ] JSON key file downloaded
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` environment variable set
- [ ] Can list projects: `gcloud projects list`
- [ ] Can create test topic: `gcloud pubsub topics create test-topic`

### AWS
- [ ] Have the Lambda Function URL from existing deployment
- [ ] Lambda is accessible and configured with OIDC authentication

---

## 📝 **Quick Start Commands**

```bash
# Verify GCP access
gcloud auth list
gcloud projects list
gcloud pubsub topics list

# Initialize Terraform
terraform init

# Plan (dry run)
terraform plan

# Apply
terraform apply
```

---

## 🐛 **Troubleshooting**

### Common Permission Errors

#### GCP: "Permission denied on resource project"
```
Solution: Grant roles/resourcemanager.projectIamAdmin
```

#### GCP: "Error creating Pub/Sub topic"
```
Solution: Grant roles/pubsub.admin
```

#### "Cannot access Lambda Function URL"
```
Solution: Verify aws_lambda_url variable points to your existing Lambda
```

---

This document provides all necessary permissions for Terraform to deploy the complete GCP-AWS observability infrastructure!
