# Cleanup script - Delete existing GCP resources

Write-Host "Cleaning up existing GCP resources..."
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
    Write-Host "Could not find gcp_project_id in terraform.tfvars"
    $projectId = Read-Host "Enter your GCP Project ID"
    Write-Host ""
}

# Delete Pub/Sub Subscription
Write-Host "[1/3] Deleting Pub/Sub subscription..."
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
Write-Host "[2/3] Deleting Pub/Sub topic..."
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
Write-Host "[3/3] Deleting Log Sink..."
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

Write-Host ""
Write-Host "Cleanup complete! You can now run deploy.ps1" -ForegroundColor Green
