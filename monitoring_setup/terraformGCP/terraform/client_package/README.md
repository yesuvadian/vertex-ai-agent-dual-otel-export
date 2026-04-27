# ⚠️ IMPORTANT: Replace Example Files

This package contains **EXAMPLE** files that you must replace with your own:

## 1. appengine-sa-key.json
**This is an EXAMPLE key file.**

You MUST replace it with YOUR service account key from YOUR GCP project:
1. Go to your GCP Console → IAM & Admin → Service Accounts
2. Generate a new JSON key
3. Replace this file

## 2. terraform.tfvars.example
Copy to `terraform.tfvars` and update:
- `gcp_project_id` → YOUR project ID
- `aws_lambda_url` → YOUR Lambda URL
- `reasoning_engine_ids` → YOUR engine IDs

## Quick Start

1. Replace `appengine-sa-key.json` with your key
2. Configure `terraform.tfvars` with your values
3. Run deployment script:
   - Windows PowerShell: `.\deploy.ps1`
   - Windows CMD: `deploy.bat`
   - Linux/Mac: `./deploy.sh`

See `CLIENT_GUIDE.md` for detailed instructions.
