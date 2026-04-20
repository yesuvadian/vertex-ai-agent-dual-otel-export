@echo off
REM Vendor Script - Grant Permission to Customer (Windows)
REM Run this after customer sends you their service account

setlocal enabledelayedexpansion

echo ==========================================
echo Grant Customer Permission to Pub/Sub Topic
echo ==========================================
echo.

REM Your configuration
set YOUR_PROJECT=agentic-ai-integration-490716
set YOUR_TOPIC=all-customers-logs

REM Customer information (fill these after customer provides)
set CUSTOMER_SERVICE_ACCOUNT=
set CUSTOMER_PROJECT_ID=
set CUSTOMER_NAME=

REM Check if variables are set
if "%CUSTOMER_SERVICE_ACCOUNT%"=="" (
    echo Please edit this script and fill in:
    echo   CUSTOMER_SERVICE_ACCOUNT - The service account customer sent you
    echo   CUSTOMER_PROJECT_ID - The customer's GCP project ID
    echo   CUSTOMER_NAME - (Optional^) Customer friendly name for tracking
    echo.
    echo Example:
    echo   set CUSTOMER_SERVICE_ACCOUNT=serviceAccount:o-123456@gcp-sa-logging.iam.gserviceaccount.com
    echo   set CUSTOMER_PROJECT_ID=customer-project-123
    echo   set CUSTOMER_NAME=Acme Corporation
    exit /b 1
)

echo Configuration:
echo   Your Project: %YOUR_PROJECT%
echo   Your Topic: %YOUR_TOPIC%
echo   Customer SA: %CUSTOMER_SERVICE_ACCOUNT%
echo   Customer Project: %CUSTOMER_PROJECT_ID%
echo   Customer Name: %CUSTOMER_NAME%
echo.
set /p CONFIRM="Grant permission? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Aborted.
    exit /b 1
)

echo.
echo Granting pubsub.publisher permission...
gcloud pubsub topics add-iam-policy-binding %YOUR_TOPIC% ^
  --member="%CUSTOMER_SERVICE_ACCOUNT%" ^
  --role=roles/pubsub.publisher ^
  --project=%YOUR_PROJECT%

if errorlevel 1 (
    echo ERROR: Failed to grant permission
    exit /b 1
)

echo.
echo ============================================
echo SUCCESS! Permission granted.
echo ============================================
echo.
echo Customer logs will now flow to your topic: %YOUR_TOPIC%
echo.
echo Tracking information:
echo   Customer: %CUSTOMER_NAME%
echo   Project: %CUSTOMER_PROJECT_ID%
echo   Service Account: %CUSTOMER_SERVICE_ACCOUNT%
echo   Date: %date% %time%
echo.
echo To verify logs arriving:
echo   gcloud pubsub subscriptions pull all-customers-logs-sub --limit=5 --project=%YOUR_PROJECT%
echo.
echo To query in Portal26:
echo   customer.project_id = "%CUSTOMER_PROJECT_ID%"
echo.
echo ============================================

endlocal
