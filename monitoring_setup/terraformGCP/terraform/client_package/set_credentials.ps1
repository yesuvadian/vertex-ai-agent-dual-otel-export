# Auto-set GOOGLE_APPLICATION_CREDENTIALS for PowerShell

$KEY_FILE = "appengine-sa-key.json"

# Check if key file exists
if (-not (Test-Path $KEY_FILE)) {
    Write-Host "ERROR: $KEY_FILE not found!" -ForegroundColor Red
    Write-Host "Please generate your service account key first."
    exit 1
}

# Set the environment variable
$env:GOOGLE_APPLICATION_CREDENTIALS = "$pwd\$KEY_FILE"

Write-Host ""
Write-Host "[OK] Credentials set successfully!" -ForegroundColor Green
Write-Host "     GOOGLE_APPLICATION_CREDENTIALS=$env:GOOGLE_APPLICATION_CREDENTIALS"
Write-Host ""
Write-Host "Note: This variable is only set for the current PowerShell session."
Write-Host "Run this script again if you open a new terminal."
Write-Host ""
