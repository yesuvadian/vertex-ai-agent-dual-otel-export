@echo off
REM ============================================================================
REM Setup Script - Using Existing App Engine Service Account
REM ============================================================================
REM Uses: agentic-ai-integration-490716@appspot.gserviceaccount.com (Editor role)
REM No need to create new service account!
REM ============================================================================

setlocal enabledelayedexpansion

set PROJECT_ID=agentic-ai-integration-490716
set SA_EMAIL=agentic-ai-integration-490716@appspot.gserviceaccount.com
set KEY_FILE=appengine-sa-key.json

echo ============================================================================
echo Terraform Setup - Using Existing App Engine Service Account
echo ============================================================================
echo Project: %PROJECT_ID%
echo Service Account: %SA_EMAIL%
echo.

REM Step 1: Check if key file already exists
echo [1/5] Checking for existing key file...
if exist "%KEY_FILE%" (
    echo [OK] Key file already exists: %KEY_FILE%
) else (
    echo [INFO] Creating service account key...
    gcloud iam service-accounts keys create "%KEY_FILE%" --iam-account="%SA_EMAIL%" --project="%PROJECT_ID%"
    if errorlevel 1 (
        echo [ERROR] Failed to create key file
        exit /b 1
    )
    echo [OK] Key file created: %KEY_FILE%
)

REM Step 2: Set authentication
echo [2/5] Setting authentication...
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\%KEY_FILE%
echo [OK] GOOGLE_APPLICATION_CREDENTIALS set

REM Step 3: Verify authentication
echo [3/5] Verifying authentication...
gcloud auth activate-service-account --key-file="%KEY_FILE%" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Could not activate service account
) else (
    echo [OK] Service account activated
)

REM Step 4: Create terraform.tfvars if needed
echo [4/5] Checking terraform.tfvars...
if not exist "terraform.tfvars" (
    copy terraform.tfvars.example terraform.tfvars >nul
    echo [OK] Created terraform.tfvars from example
    echo.
    echo WARNING: Edit terraform.tfvars before running terraform apply!
    echo.
    echo Update these values:
    echo   - aws_lambda_url         (your Lambda URL^)
    echo   - reasoning_engine_ids   (your reasoning engine IDs^)
    echo   - log_severity_filter    (optional, for cost savings^)
    echo.
    echo Then run:
    echo   set GOOGLE_APPLICATION_CREDENTIALS=%cd%\%KEY_FILE%
    echo   terraform init
    echo   terraform plan
    echo   terraform apply
    echo.
    exit /b 0
) else (
    echo [OK] terraform.tfvars already exists
)

REM Step 5: Check if Terraform is initialized
echo [5/5] Checking Terraform initialization...
if not exist ".terraform" (
    echo [INFO] Terraform not initialized. Run: terraform init
) else (
    echo [OK] Terraform already initialized
)

echo.
echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo.
echo Service Account: %SA_EMAIL%
echo Key File: %KEY_FILE%
echo Authentication: GOOGLE_APPLICATION_CREDENTIALS is set
echo.
echo Next Steps:
echo   1. Edit terraform.tfvars (if not done^)
echo   2. Run: set GOOGLE_APPLICATION_CREDENTIALS=%cd%\%KEY_FILE%
echo   3. Run: terraform init
echo   4. Run: terraform plan
echo   5. Run: terraform apply
echo.
echo To use this authentication in future sessions:
echo   set GOOGLE_APPLICATION_CREDENTIALS=%cd%\%KEY_FILE%
echo.
