# One-command deployment script for PowerShell
# Automatically sets credentials and deploys infrastructure

$ErrorActionPreference = "Stop"

$KEY_FILE = "appengine-sa-key.json"

Write-Host "============================================"
Write-Host "GCP Log Sink Deployment"
Write-Host "============================================"
Write-Host ""

# Check if key file exists
if (-not (Test-Path $KEY_FILE)) {
    Write-Host "ERROR: $KEY_FILE not found!" -ForegroundColor Red
    Write-Host "Please generate your service account key first."
    Write-Host "See CLIENT_GUIDE.md Step 1"
    exit 1
}

# Check if terraform.tfvars exists
if (-not (Test-Path "terraform.tfvars")) {
    Write-Host "ERROR: terraform.tfvars not found!" -ForegroundColor Red
    Write-Host "Please copy and configure terraform.tfvars.example"
    Write-Host "See CLIENT_GUIDE.md Step 2"
    exit 1
}

# Set credentials automatically
$env:GOOGLE_APPLICATION_CREDENTIALS = "$pwd\$KEY_FILE"
Write-Host "[1/3] Credentials set" -ForegroundColor Green

# Initialize Terraform
Write-Host "[2/3] Initializing Terraform..."
terraform init
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Deploy
Write-Host "[3/3] Deploying infrastructure..."
terraform apply
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "============================================"
Write-Host "Deployment Complete!"
Write-Host "============================================"
