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

Edit `terraform.tfvars` - update these values:
- `gcp_project_id` - YOUR GCP Project ID
- `reasoning_engine_ids` - YOUR Reasoning Engine IDs
- `aws_lambda_url` - (optional) Override if you have a different Lambda URL

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
