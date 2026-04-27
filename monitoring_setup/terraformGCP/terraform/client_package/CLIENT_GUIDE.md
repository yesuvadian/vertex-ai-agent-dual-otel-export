# Setup Instructions

## Prerequisites
- Terraform installed
- GCP Project with Reasoning Engines
- Service Account with Editor role in your GCP project

## Steps

### 1. Replace Service Account Key

**The included `appengine-sa-key.json` is an EXAMPLE only.**

Generate YOUR service account key:

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select YOUR GCP project
3. Click on your service account (with Editor role)
4. **KEYS** tab → **ADD KEY** → **Create new key** → **JSON**
5. **Replace** the example file with your downloaded key
6. Rename to: `appengine-sa-key.json`

### 2. Configure

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

**Optional:**
- `aws_lambda_url` - Override if you have a different Lambda URL
- `log_severity_filter` - Filter by severity (e.g., `["ERROR", "CRITICAL"]`) for 80-90% cost savings
- `agent_ids` - Filter by specific agent IDs
- `log_resource_types` - Filter by resource types
- `custom_log_filter` - Advanced custom filter expression

**Example:**
```hcl
gcp_project_id = "my-gcp-project-123"
reasoning_engine_ids = ["9162160575269044224", "8213677864684355584"]
log_severity_filter = ["ERROR", "CRITICAL"]  # Uncomment for cost savings
```

### 3. Deploy (One Command!)

**Windows PowerShell:**
```powershell
.\deploy.ps1
```

**Windows CMD:**
```cmd
deploy.bat
```

**Git Bash / Linux / Mac:**
```bash
./deploy.sh
```

The script automatically:
- Sets credentials
- Initializes Terraform
- Deploys infrastructure

Type `yes` when Terraform asks to confirm.

---

**Manual Deployment (if scripts don't work):**

Set credentials first:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"  # Linux/Mac
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"     # PowerShell
```

Then deploy:
```bash
terraform init
terraform apply
```

## What Gets Created

In YOUR GCP project:
- Pub/Sub Topic: `reasoning-engine-logs-topic`
- Pub/Sub Subscription: Pushes to YOUR Lambda
- Log Sink: Routes YOUR Reasoning Engine logs

## Cleanup

```bash
terraform destroy
```
