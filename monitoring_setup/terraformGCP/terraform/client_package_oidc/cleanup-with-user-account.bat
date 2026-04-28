@echo off
REM Cleanup script using USER account credentials (not service account)
REM Deletes GCP resources created by deploy-with-user-account.bat

setlocal enabledelayedexpansion

echo ============================================
echo GCP Log Sink Cleanup (User Account)
echo ============================================
echo.

REM Extract GCP Project ID from terraform.tfvars
set "PROJECT_ID="
if exist terraform.tfvars (
    for /f "tokens=2 delims==" %%a in ('findstr /r "gcp_project_id.*=" terraform.tfvars') do (
        set "line=%%a"
        set "line=!line:~1,-1!"
        set "line=!line: =!"
        set "PROJECT_ID=!line!"
    )
)

if defined PROJECT_ID (
    echo Using project: !PROJECT_ID!
    echo.
) else (
    echo Could not find gcp_project_id in terraform.tfvars
    set /p PROJECT_ID="Enter your GCP Project ID: "
    echo.
)

REM Check authentication
echo [1/5] Checking GCP authentication...
gcloud auth application-default print-access-token >nul 2>&1
if errorlevel 1 (
    echo Not authenticated. Logging in...
    gcloud auth application-default login --no-launch-browser
    if errorlevel 1 exit /b 1
)
echo   Authenticated

REM Delete Pub/Sub Subscription
echo [2/5] Deleting Pub/Sub subscription...
gcloud pubsub subscriptions delete reasoning-engine-to-lambda --project=!PROJECT_ID! --quiet >nul 2>&1
if errorlevel 1 (
    echo   Not found or already deleted
) else (
    echo   Deleted
)

REM Delete Pub/Sub Topic
echo [3/5] Deleting Pub/Sub topic...
gcloud pubsub topics delete reasoning-engine-logs-topic --project=!PROJECT_ID! --quiet >nul 2>&1
if errorlevel 1 (
    echo   Not found or already deleted
) else (
    echo   Deleted
)

REM Delete Log Sink
echo [4/5] Deleting Log Sink...
gcloud logging sinks delete reasoning-engine-to-pubsub --project=!PROJECT_ID! --quiet >nul 2>&1
if errorlevel 1 (
    echo   Not found or already deleted
) else (
    echo   Deleted
)

REM Optional: Clean Terraform state
echo [5/5] Cleaning Terraform state...
if exist terraform.tfstate (
    echo   Found terraform.tfstate
    set /p RESPONSE="Do you want to delete Terraform state files? (y/N): "
    if /i "!RESPONSE!"=="y" (
        del /f terraform.tfstate 2>nul
        del /f terraform.tfstate.backup 2>nul
        echo   Terraform state deleted
    ) else (
        echo   Keeping Terraform state
    )
) else (
    echo   No Terraform state found
)

echo.
echo ============================================
echo Cleanup Complete!
echo ============================================
echo.
echo You can now run deploy-with-user-account.bat to redeploy

endlocal
