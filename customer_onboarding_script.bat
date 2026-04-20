@echo off
REM Customer Onboarding Script for Windows
REM Give this script to your customers to run in their GCP project

setlocal enabledelayedexpansion

echo ==========================================
echo Customer Onboarding - Log Forwarding Setup
echo ==========================================
echo.

REM Customer must fill these variables
set CUSTOMER_PROJECT_ID=YOUR-GCP-PROJECT-ID
set VENDOR_PROJECT_ID=agentic-ai-integration-490716
set VENDOR_TOPIC=all-customers-logs
set SINK_NAME=send-logs-to-vendor

REM Validate configuration
if "%CUSTOMER_PROJECT_ID%"=="YOUR-GCP-PROJECT-ID" (
    echo ERROR: Please edit this script and set CUSTOMER_PROJECT_ID to your GCP project ID
    exit /b 1
)

echo Configuration:
echo   Your Project: %CUSTOMER_PROJECT_ID%
echo   Vendor Project: %VENDOR_PROJECT_ID%
echo   Vendor Topic: %VENDOR_TOPIC%
echo.
set /p CONFIRM="Is this correct? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Aborted.
    exit /b 1
)

echo.
echo [1/3] Creating log sink in your project...
gcloud logging sinks create %SINK_NAME% ^
  --log-filter="resource.type=\"aiplatform.googleapis.com/ReasoningEngine\"" ^
  --destination=pubsub.googleapis.com/projects/%VENDOR_PROJECT_ID%/topics/%VENDOR_TOPIC% ^
  --project=%CUSTOMER_PROJECT_ID%

if errorlevel 1 (
    echo ERROR: Failed to create log sink
    exit /b 1
)
echo SUCCESS: Log sink created

echo.
echo [2/3] Getting service account identity...
for /f "delims=" %%a in ('gcloud logging sinks describe %SINK_NAME% --project=%CUSTOMER_PROJECT_ID% --format="value(writerIdentity)"') do set SERVICE_ACCOUNT=%%a

if "%SERVICE_ACCOUNT%"=="" (
    echo ERROR: Could not retrieve service account
    exit /b 1
)
echo SUCCESS: Service account retrieved

echo.
echo [3/3] Verification...
echo Checking if log sink is active...
gcloud logging sinks describe %SINK_NAME% --project=%CUSTOMER_PROJECT_ID% >nul 2>&1
if errorlevel 1 (
    echo WARNING: Could not verify log sink status
) else (
    echo SUCCESS: Log sink is active
)

echo.
echo ============================================
echo SETUP COMPLETE!
echo ============================================
echo.
echo Next Steps:
echo 1. Send the following information to your vendor:
echo.
echo    Service Account:
echo    %SERVICE_ACCOUNT%
echo.
echo    Customer Project ID:
echo    %CUSTOMER_PROJECT_ID%
echo.
echo 2. Wait for vendor to grant permission (usually within 24 hours)
echo.
echo 3. Your Reasoning Engine logs will automatically flow to vendor's monitoring
echo.
echo To verify logs are being exported, run:
echo   gcloud logging read "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\"" --limit 5 --project=%CUSTOMER_PROJECT_ID%
echo.
echo To stop sending logs (revoke at any time):
echo   gcloud logging sinks delete %SINK_NAME% --project=%CUSTOMER_PROJECT_ID%
echo.
echo ============================================

endlocal
