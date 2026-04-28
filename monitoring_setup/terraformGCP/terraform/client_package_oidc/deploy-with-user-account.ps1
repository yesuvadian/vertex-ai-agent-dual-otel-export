# Deployment script using USER account credentials (not service account)
# Run this when you want to use your own GCP login instead of service account

$ErrorActionPreference = "Stop"

Write-Host "============================================"
Write-Host "GCP Log Sink Deployment (User Account)"
Write-Host "============================================"
Write-Host ""

# Check if terraform.tfvars exists
if (-not (Test-Path "terraform.tfvars")) {
    Write-Host "ERROR: terraform.tfvars not found!" -ForegroundColor Red
    Write-Host "Please copy and configure terraform.tfvars.example"
    Write-Host "See CLIENT_GUIDE.md Step 2"
    exit 1
}

# Use user's gcloud credentials (not service account key)
Write-Host "[1/4] Authenticating with your GCP account..."
gcloud auth application-default login --no-launch-browser
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/4] Credentials set from your GCP login" -ForegroundColor Green

# Initialize Terraform
Write-Host "[3/4] Initializing Terraform..."
terraform init
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Deploy
Write-Host "[4/4] Deploying infrastructure..."
terraform apply
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "============================================"
Write-Host "Deployment Complete!"
Write-Host "============================================"
