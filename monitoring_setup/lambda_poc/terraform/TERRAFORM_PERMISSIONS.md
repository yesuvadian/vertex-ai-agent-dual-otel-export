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
| `roles/secretmanager.admin` | Manage secrets (shared secret) | `secretmanager.secrets.create`<br>`secretmanager.versions.add`<br>`secretmanager.secrets.setIamPolicy` |

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
resourcemanager.projects.setIamPolicy,\
secretmanager.secrets.create,\
secretmanager.secrets.delete,\
secretmanager.secrets.get,\
secretmanager.versions.add,\
secretmanager.versions.access,\
secretmanager.secrets.setIamPolicy"
```

---

## 🔐 **AWS Permissions**

### User/Role Requirements

The AWS user or role running Terraform needs these permissions:

#### **Required IAM Policies**

##### **1. Lambda Management**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:ListFunctions",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:CreateFunctionUrlConfig",
        "lambda:UpdateFunctionUrlConfig",
        "lambda:DeleteFunctionUrlConfig",
        "lambda:GetFunctionUrlConfig"
      ],
      "Resource": "*"
    }
  ]
}
```

##### **2. IAM Role Management**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:ListRoles",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:PassRole",
        "iam:TagRole",
        "iam:UntagRole"
      ],
      "Resource": "*"
    }
  ]
}
```

##### **3. S3 Management**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:PutBucketVersioning",
        "s3:GetBucketVersioning",
        "s3:PutLifecycleConfiguration",
        "s3:GetLifecycleConfiguration",
        "s3:PutBucketTagging",
        "s3:GetBucketTagging"
      ],
      "Resource": "*"
    }
  ]
}
```

##### **4. Kinesis Management**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:CreateStream",
        "kinesis:DeleteStream",
        "kinesis:DescribeStream",
        "kinesis:ListStreams",
        "kinesis:AddTagsToStream",
        "kinesis:RemoveTagsFromStream"
      ],
      "Resource": "*"
    }
  ]
}
```

##### **5. CloudWatch Logs**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy",
        "logs:TagLogGroup",
        "logs:UntagLogGroup"
      ],
      "Resource": "*"
    }
  ]
}
```

##### **6. Secrets Manager**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:DeleteSecret",
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:TagResource",
        "secretsmanager:UntagResource"
      ],
      "Resource": "*"
    }
  ]
}
```

#### **AWS Managed Policies (Alternative)**

Instead of custom policies, you can use these AWS managed policies:

```bash
# Attach to your Terraform user/role
aws iam attach-user-policy \
  --user-name terraform-user \
  --policy-arn arn:aws:iam::aws:policy/POLICY_NAME
```

| Managed Policy | Purpose |
|----------------|---------|
| `PowerUserAccess` | Full access except IAM (recommended for testing) |
| `IAMFullAccess` | Full IAM permissions (needed for role creation) |

**OR** for production, use minimal custom policy above.

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

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

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

### AWS Setup

#### Option 1: Using IAM User (Recommended for CI/CD)

```bash
# 1. Create IAM user
aws iam create-user --user-name terraform-deployer

# 2. Create custom policy (save as terraform-policy.json)
aws iam create-policy \
  --policy-name TerraformDeploymentPolicy \
  --policy-document file://terraform-policy.json

# 3. Attach policy to user
aws iam attach-user-policy \
  --user-name terraform-deployer \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/TerraformDeploymentPolicy

# 4. Create access keys
aws iam create-access-key --user-name terraform-deployer

# 5. Configure AWS CLI
aws configure
# Enter access key, secret key, region
```

#### Option 2: Using IAM Role (for EC2/ECS)

```bash
# Create role with trust policy
aws iam create-role \
  --role-name TerraformDeployerRole \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name TerraformDeployerRole \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/TerraformDeploymentPolicy
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
- [ ] IAM user/role created
- [ ] Required policies attached
- [ ] AWS CLI configured
- [ ] Can list functions: `aws lambda list-functions`
- [ ] Can list buckets: `aws s3 ls`

---

## 📝 **Quick Start Commands**

```bash
# Verify GCP access
gcloud auth list
gcloud projects list
gcloud pubsub topics list

# Verify AWS access
aws sts get-caller-identity
aws lambda list-functions --region us-east-1
aws s3 ls

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

#### AWS: "User is not authorized to perform: lambda:CreateFunction"
```
Solution: Attach Lambda management policy
```

#### AWS: "Access Denied" on S3
```
Solution: Grant S3 bucket creation permissions
```

---

This document provides all necessary permissions for Terraform to deploy the complete GCP-AWS observability infrastructure!
