# GCP Log Sink Deployment Script - User Account Authentication

Write-Host "========================================"
Write-Host "GCP Log Sink Deployment - User Account"
Write-Host "========================================"
Write-Host ""

# Extract project ID
$content = Get-Content "terraform.tfvars" -Raw
if ($content -match 'gcp_project_id\s*=\s*"([^"]+)"') {
    $projectId = $matches[1]
} else {
    Write-Host "ERROR: Could not find gcp_project_id"
    exit 1
}

Write-Host "Project ID: $projectId"
Write-Host ""

# Authenticate
Write-Host "Authenticating with Google Cloud..."
Write-Host "Browser will open for authentication."
Write-Host ""

gcloud auth application-default login --project=$projectId

Write-Host ""
gcloud config set project $projectId 2>&1 | Out-Null
Write-Host "Project set"
Write-Host ""

# Backup main.tf
Copy-Item "main.tf" "main.tf.backup" -Force

# Comment out credentials line
$mainTf = Get-Content "main.tf" -Raw
$mainTf = $mainTf -replace 'credentials\s*=\s*file\("appengine-sa-key\.json"\)', '# credentials = file("appengine-sa-key.json")'
Set-Content "main.tf" -Value $mainTf -NoNewline

Write-Host "Initializing Terraform..."
terraform init
Write-Host ""

Write-Host "Planning deployment..."
terraform plan
Write-Host ""

Write-Host "========================================"
Write-Host "Ready to deploy!"
Write-Host "========================================"
Write-Host ""
Write-Host "Type YES to continue or anything else to cancel"
$answer = Read-Host "Proceed"

if ($answer -ne "YES") {
    Write-Host "Cancelled"
    Copy-Item "main.tf.backup" "main.tf" -Force
    Remove-Item "main.tf.backup" -Force
    exit 0
}

Write-Host ""
Write-Host "Deploying..."
terraform apply -auto-approve

# Restore
Copy-Item "main.tf.backup" "main.tf" -Force
Remove-Item "main.tf.backup" -Force

Write-Host ""
Write-Host "========================================"
Write-Host "Deployment Complete!"
Write-Host "========================================"
