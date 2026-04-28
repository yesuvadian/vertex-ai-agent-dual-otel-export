# Prepare terraformGCP folder for upload to GitHub
# This script removes sensitive files before upload

Write-Host "Preparing terraformGCP for GitHub upload..." -ForegroundColor Cyan
Write-Host ""

$basePath = "terraform/client_package"

# Files to remove (sensitive)
$sensitiveFiles = @(
    "$basePath/terraform.tfvars",
    "$basePath/terraform.tfstate",
    "$basePath/terraform.tfstate.backup",
    "$basePath/.terraform.lock.hcl",
    "terraform/client_package.zip"
)

# Directories to remove
$sensitiveDirs = @(
    "$basePath/.terraform"
)

Write-Host "Removing sensitive files..." -ForegroundColor Yellow
foreach ($file in $sensitiveFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  ✓ Removed: $file" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Removing build directories..." -ForegroundColor Yellow
foreach ($dir in $sensitiveDirs) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force
        Write-Host "  ✓ Removed: $dir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Verifying example files exist..." -ForegroundColor Yellow
$requiredFiles = @(
    "$basePath/terraform.tfvars.example",
    "$basePath/appengine-sa-key.json",
    "$basePath/CLIENT_GUIDE.md"
)

$allGood = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING: $file" -ForegroundColor Red
        $allGood = $false
    }
}

Write-Host ""
if ($allGood) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Ready to upload!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Go to: https://github.com/titaniam/lambda-gcp-otel-preprocessor"
    Write-Host "2. Click 'Add file' → 'Upload files'"
    Write-Host "3. Drag the entire 'terraformGCP' folder"
    Write-Host "4. Commit changes"
    Write-Host ""
    Write-Host "Or see UPLOAD_INSTRUCTIONS.md for detailed steps"
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "WARNING: Missing required files!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}
