# Setup Instructions

## Prerequisites
- Terraform installed

## Steps

### 1. Set Credentials

**Windows PowerShell:**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"
```

**Git Bash / Linux / Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
```

### 2. Configure

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` - update these 2 values:
- `aws_lambda_url` - Your Lambda URL
- `reasoning_engine_ids` - Your Engine IDs

### 3. Deploy

```bash
terraform init
terraform apply
```

Type `yes` when prompted.

## Cleanup

```bash
terraform destroy
```
