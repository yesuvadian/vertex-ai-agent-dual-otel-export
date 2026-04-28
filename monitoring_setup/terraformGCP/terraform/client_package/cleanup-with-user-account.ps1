# Cleanup script using USER account credentials (not service account)
# Deletes GCP resources created by deploy-with-user-account.ps1

$ErrorActionPreference = "Stop"

Write-Host "============================================"
Write-Host "GCP Log Sink Cleanup (User Account)"
Write-Host "============================================"
Write-Host ""

# Extract GCP Project ID from terraform.tfvars
$projectId = ""
if (Test-Path "terraform.tfvars") {
    $content = Get-Content "terraform.tfvars" -Raw
    if ($content -match 'gcp_project_id\s*=\s*"([^"]+)"') {
        $projectId = $matches[1]
        Write-Host "Using project: $projectId"
        Write-Host ""
    }
}

# Fallback: ask user if not found
if ([string]::IsNullOrEmpty($projectId)) {
    Write-Host "Could not find gcp_project_id in terraform.tfvars" -ForegroundColor Yellow
    $projectId = Read-Host "Enter your GCP Project ID"
    Write-Host ""
}

# Check authentication
Write-Host "[1/5] Checking GCP authentication..."
$authCheck = gcloud auth application-default print-access-token 2>$null
if (-not $authCheck) {
    Write-Host "Not authenticated. Logging in..." -ForegroundColor Yellow
    gcloud auth application-default login --no-launch-browser
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host "  Authenticated" -ForegroundColor Green

# Delete Pub/Sub Subscription
Write-Host "[2/5] Deleting Pub/Sub subscription..."
$checkSub = gcloud pubsub subscriptions list --project=$projectId --filter="name:reasoning-engine-to-lambda" --format="value(name)" 2>$null
if ($checkSub) {
    $prevErrorPref = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    gcloud pubsub subscriptions delete reasoning-engine-to-lambda --project=$projectId --quiet 2>&1 | Out-Null
    $ErrorActionPreference = $prevErrorPref
    Write-Host "  Deleted" -ForegroundColor Green
} else {
    Write-Host "  Not found or already deleted" -ForegroundColor Yellow
}

# Delete Pub/Sub Topic
Write-Host "[3/5] Deleting Pub/Sub topic..."
$checkTopic = gcloud pubsub topics list --project=$projectId --filter="name:reasoning-engine-logs-topic" --format="value(name)" 2>$null
if ($checkTopic) {
    $prevErrorPref = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    gcloud pubsub topics delete reasoning-engine-logs-topic --project=$projectId --quiet 2>&1 | Out-Null
    $ErrorActionPreference = $prevErrorPref
    Write-Host "  Deleted" -ForegroundColor Green
} else {
    Write-Host "  Not found or already deleted" -ForegroundColor Yellow
}

# Delete Log Sink
Write-Host "[4/5] Deleting Log Sink..."
$checkSink = gcloud logging sinks list --project=$projectId --filter="name:reasoning-engine-to-pubsub" --format="value(name)" 2>$null
if ($checkSink) {
    $prevErrorPref = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    gcloud logging sinks delete reasoning-engine-to-pubsub --project=$projectId --quiet 2>&1 | Out-Null
    $ErrorActionPreference = $prevErrorPref
    Write-Host "  Deleted" -ForegroundColor Green
} else {
    Write-Host "  Not found or already deleted" -ForegroundColor Yellow
}

# Optional: Clean Terraform state
Write-Host "[5/5] Cleaning Terraform state..."
if (Test-Path "terraform.tfstate") {
    Write-Host "  Found terraform.tfstate"
    $response = Read-Host "Do you want to delete Terraform state files? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Remove-Item "terraform.tfstate" -Force
        if (Test-Path "terraform.tfstate.backup") {
            Remove-Item "terraform.tfstate.backup" -Force
        }
        Write-Host "  Terraform state deleted" -ForegroundColor Green
    } else {
        Write-Host "  Keeping Terraform state" -ForegroundColor Yellow
    }
} else {
    Write-Host "  No Terraform state found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================"
Write-Host "Cleanup Complete!"
Write-Host "============================================"
Write-Host ""
Write-Host "You can now run deploy-with-user-account.ps1 to redeploy" -ForegroundColor Cyan
