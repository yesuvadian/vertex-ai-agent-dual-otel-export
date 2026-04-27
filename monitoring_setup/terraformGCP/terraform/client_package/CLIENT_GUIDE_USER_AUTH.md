# Setup Instructions - User Account Authentication

**Use this guide if you want to deploy using your own GCP account credentials instead of a service account key.**

## Prerequisites
- Terraform installed
- gcloud CLI installed
- GCP account with these roles:
  - `roles/editor` (or `roles/pubsub.admin`)
  - `roles/logging.configWriter` (for log sinks)

## Steps

### 1. Configure terraform.tfvars

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` - **Required:**
- `gcp_project_id` - YOUR GCP Project ID
- `reasoning_engine_ids` - YOUR Reasoning Engine IDs (list format)

**How to get Reasoning Engine ID:**

1. Go to: https://console.cloud.google.com/vertex-ai/reasoning-engines
2. Select your project
3. Click on your Reasoning Engine
4. Copy the ID from the URL or details page
   - URL format: `.../reasoning-engines/REGION/REASONING_ENGINE_ID`
   - Example ID: `9162160575269044224`

**Optional Filters:**
- `aws_lambda_url` - Override if you have a different Lambda URL
- `log_severity_filter` - Filter by severity (e.g., `["ERROR", "CRITICAL"]`) for cost savings
- `agent_ids` - Filter by specific agent IDs
- `log_resource_types` - Filter by resource types

**Example:**
```hcl
gcp_project_id = "my-gcp-project-123"
reasoning_engine_ids = ["9162160575269044224"]
log_severity_filter = ["ERROR", "CRITICAL"]
```

### 2. Deploy

**Windows PowerShell:**
```powershell
.\deploy-with-user-account.ps1
```

**Windows CMD:**
```cmd
deploy-with-user-account.bat
```

**Linux / Mac / Git Bash:**
```bash
./deploy-with-user-account.sh
```

**What happens:**
1. Browser opens for GCP authentication
2. Enter verification code from browser
3. Terraform initializes
4. Terraform shows deployment plan
5. Type `yes` to confirm

---

## What Gets Created

In YOUR GCP project:
- **Pub/Sub Topic**: `reasoning-engine-logs-topic`
- **Pub/Sub Subscription**: Pushes to AWS Lambda
- **Log Sink**: Routes Reasoning Engine logs

## Cleanup

```bash
terraform destroy
```

---

## Troubleshooting

### Error: "Permission denied" on logging.sinks

Your account needs `roles/logging.configWriter` role.

**Check your permissions:**
```bash
gcloud projects get-iam-policy YOUR-PROJECT-ID --flatten="bindings[].members" --filter="bindings.members:YOUR-EMAIL@domain.com"
```

**Ask your GCP admin to add the role:**
```bash
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="user:YOUR-EMAIL@domain.com" \
  --role="roles/logging.configWriter"
```

### Error: "Invalid JWT Signature"

Clear old credentials and re-authenticate:

**PowerShell:**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = $null
gcloud auth application-default revoke
.\deploy-with-user-account.ps1
```

**Linux/Mac:**
```bash
unset GOOGLE_APPLICATION_CREDENTIALS
gcloud auth application-default revoke
./deploy-with-user-account.sh
```

### Error: "Resource already exists"

Resources from a previous deployment exist.

**Option 1: Destroy first**
```bash
terraform destroy
```
Then re-deploy.

**Option 2: Import existing resources**
```bash
terraform import google_pubsub_topic.reasoning_engine_logs projects/YOUR-PROJECT-ID/topics/reasoning-engine-logs-topic
terraform import google_pubsub_subscription.reasoning_engine_to_lambda projects/YOUR-PROJECT-ID/subscriptions/reasoning-engine-to-lambda
terraform import google_logging_project_sink.reasoning_engine_to_pubsub YOUR-PROJECT-ID/sinks/reasoning-engine-to-pubsub
```

---

## Required GCP Roles

Your GCP account (or Google Group you belong to) must have:

### 1. Editor or Pub/Sub Admin
**Role:** `roles/editor` OR `roles/pubsub.admin`

**Permissions needed:**
- Create/modify Pub/Sub topics
- Create/modify Pub/Sub subscriptions

### 2. Logging Config Writer ⚠️ **REQUIRED**
**Role:** `roles/logging.configWriter`

**Permissions needed:**
- `logging.sinks.create`
- `logging.sinks.update`
- `logging.sinks.delete`

**Note:** `roles/editor` does NOT include logging sink permissions. You must have `roles/logging.configWriter` separately.

---

## Advantages of User Account Method

✅ **No service account key management**
- No need to download/store JSON key files
- No risk of committing keys to version control

✅ **Uses your existing GCP access**
- Leverage permissions you already have
- No need to configure service account roles

✅ **Better for individual deployments**
- Quick setup for personal projects
- Easy authentication via browser

## When to Use Service Account Instead

Consider using service account authentication (`deploy.ps1`) if:
- Deploying from CI/CD pipelines
- Need non-interactive automation
- Multiple team members deploying with same credentials
- Don't want to install gcloud CLI

See `CLIENT_GUIDE.md` for service account instructions.
