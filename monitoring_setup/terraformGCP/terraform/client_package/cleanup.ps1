# Cleanup script - Delete existing GCP resources

Write-Host "Cleaning up existing GCP resources..."
Write-Host ""

# Delete Pub/Sub Subscription
Write-Host "[1/3] Deleting Pub/Sub subscription..."
gcloud pubsub subscriptions delete reasoning-engine-to-lambda --project=agentic-ai-integration-490716 --quiet 2>$null
if ($?) { Write-Host "  Deleted" } else { Write-Host "  Not found or already deleted" }

# Delete Pub/Sub Topic
Write-Host "[2/3] Deleting Pub/Sub topic..."
gcloud pubsub topics delete reasoning-engine-logs-topic --project=agentic-ai-integration-490716 --quiet 2>$null
if ($?) { Write-Host "  Deleted" } else { Write-Host "  Not found or already deleted" }

# Delete Log Sink
Write-Host "[3/3] Deleting Log Sink..."
gcloud logging sinks delete reasoning-engine-to-pubsub --project=agentic-ai-integration-490716 --quiet 2>$null
if ($?) { Write-Host "  Deleted" } else { Write-Host "  Not found or already deleted" }

Write-Host ""
Write-Host "Cleanup complete! You can now run deploy.ps1"
