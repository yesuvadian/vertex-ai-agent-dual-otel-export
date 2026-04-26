@echo off
REM ============================================================================
REM Generate Package for Users - Admin Script (Windows)
REM ============================================================================
REM This script creates a package with key file for users without gcloud CLI
REM Run this as admin to prepare files for distribution to users
REM ============================================================================

setlocal enabledelayedexpansion

set PROJECT_ID=agentic-ai-integration-490716
set SA_EMAIL=agentic-ai-integration-490716@appspot.gserviceaccount.com
set KEY_FILE=appengine-sa-key.json

echo ============================================================================
echo Generate Terraform Package for Users (No gcloud CLI required)
echo ============================================================================
echo Project: %PROJECT_ID%
echo Service Account: %SA_EMAIL%
echo.

REM Step 1: Check if gcloud is available
echo [1/4] Checking gcloud CLI...
where gcloud >nul 2>nul
if errorlevel 1 (
    echo [ERROR] gcloud CLI not found
    echo Please install: https://cloud.google.com/sdk/docs/install
    exit /b 1
)
echo [OK] gcloud CLI found

REM Step 2: Create service account key
echo [2/4] Creating service account key...
if exist "%KEY_FILE%" (
    echo [WARN] Key file already exists: %KEY_FILE%
    set /p OVERWRITE="Overwrite? (y/n): "
    if /i not "!OVERWRITE!"=="y" (
        echo [INFO] Using existing key file
        goto :skip_key_creation
    )
    del "%KEY_FILE%"
)

gcloud iam service-accounts keys create "%KEY_FILE%" --iam-account="%SA_EMAIL%" --project="%PROJECT_ID%"
if errorlevel 1 (
    echo [ERROR] Failed to create key file
    exit /b 1
)
echo [OK] Key file created: %KEY_FILE%

:skip_key_creation

REM Step 3: Create package directory
echo [3/4] Creating package structure...
set PACKAGE_DIR=terraform_no_oidc_package
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"

REM Copy files
copy main.tf "%PACKAGE_DIR%\" >nul
copy gcp_log_sink_pubsub.tf "%PACKAGE_DIR%\" >nul
copy terraform.tfvars.example "%PACKAGE_DIR%\" >nul
copy "%KEY_FILE%" "%PACKAGE_DIR%\" >nul
copy README_FOR_USERS.md "%PACKAGE_DIR%\README.md" >nul

REM Create quick start guide
echo Creating QUICK_START.txt...
(
echo ========================================================================================
echo TERRAFORM GCP SETUP - QUICK START
echo ========================================================================================
echo.
echo PREREQUISITES:
echo - Terraform installed ^(terraform --version^)
echo - This package contains everything you need ^(no gcloud CLI needed^)
echo.
echo SETUP STEPS:
echo.
echo 1. Set Authentication ^(choose your OS^):
echo.
echo    Windows PowerShell:
echo    $env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"
echo.
echo    Windows CMD:
echo    set GOOGLE_APPLICATION_CREDENTIALS=%%cd%%\appengine-sa-key.json
echo.
echo    Linux/Mac:
echo    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
echo.
echo 2. Create Configuration:
echo    copy terraform.tfvars.example terraform.tfvars
echo.
echo    Edit terraform.tfvars and update:
echo    - aws_lambda_url ^(your Lambda URL^)
echo    - reasoning_engine_ids ^(your reasoning engine IDs^)
echo.
echo 3. Deploy:
echo    terraform init
echo    terraform plan
echo    terraform apply    ^(type 'yes'^)
echo.
echo 4. Cleanup ^(when done^):
echo    terraform destroy  ^(type 'yes'^)
echo.
echo For detailed instructions, see README.md
echo.
echo IMPORTANT:
echo - Keep appengine-sa-key.json secure
echo - Never commit it to git
echo - Set GOOGLE_APPLICATION_CREDENTIALS every time you open a new terminal
echo.
echo ========================================================================================
) > "%PACKAGE_DIR%\QUICK_START.txt"

echo [OK] Package structure created

REM Step 4: Create instructions
echo [4/4] Creating distribution package...
echo.
echo ============================================================================
echo Package Created Successfully!
echo ============================================================================
echo.
echo Package Directory: %PACKAGE_DIR%
echo Contains:
echo   - Terraform configuration files
echo   - Service account key: %KEY_FILE%
echo   - README.md ^(user instructions^)
echo   - QUICK_START.txt ^(quick reference^)
echo.
echo Service Account Details:
echo   Email: %SA_EMAIL%
echo   Role: Editor ^(full GCP access^)
echo   Project: %PROJECT_ID%
echo.
echo Distribution:
echo   1. Share the %PACKAGE_DIR% folder with users
echo   2. Or create a zip file: 7z a terraform-gcp-setup.zip %PACKAGE_DIR%
echo   3. Users extract and follow QUICK_START.txt
echo   4. No gcloud CLI needed - just Terraform!
echo.
echo Security Notes:
echo   - Package contains sensitive key file
echo   - Share via secure channel ^(encrypted email, secure file transfer^)
echo   - Consider password-protecting when zipping
echo   - Rotate key periodically
echo.
echo Next Steps for Admin:
echo   - Compress %PACKAGE_DIR% to zip file
echo   - Share securely with users
echo   - Provide AWS Lambda URL and Reasoning Engine IDs
echo.
