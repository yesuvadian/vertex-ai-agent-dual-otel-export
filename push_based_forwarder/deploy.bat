@echo off
REM Deploy Cloud Function for Push-Based Forwarding (Windows)

echo ========================================
echo Deploying Cloud Function to GCP
echo ========================================
echo.

REM Configuration
set PROJECT_ID=agentic-ai-integration-490716
set FUNCTION_NAME=vertex-to-portal26
set REGION=us-central1
set TOPIC=vertex-telemetry-topic

REM Portal26 Configuration
set PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318
set PORTAL26_AUTH=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
set TENANT_ID=tenant1
set USER_ID=relusys_terraform
set SERVICE_NAME=gcp-vertex-monitor

echo Configuration:
echo   Project:        %PROJECT_ID%
echo   Function:       %FUNCTION_NAME%
echo   Region:         %REGION%
echo   Trigger Topic:  %TOPIC%
echo   Portal26:       %PORTAL26_ENDPOINT%
echo.

echo Deploying Cloud Function...
gcloud functions deploy %FUNCTION_NAME% ^
  --gen2 ^
  --runtime python311 ^
  --region %REGION% ^
  --source . ^
  --entry-point pubsub_to_portal26 ^
  --trigger-topic %TOPIC% ^
  --set-env-vars PORTAL26_ENDPOINT=%PORTAL26_ENDPOINT% ^
  --set-env-vars PORTAL26_AUTH="%PORTAL26_AUTH%" ^
  --set-env-vars TENANT_ID=%TENANT_ID% ^
  --set-env-vars USER_ID=%USER_ID% ^
  --set-env-vars SERVICE_NAME=%SERVICE_NAME% ^
  --max-instances 10 ^
  --timeout 60s ^
  --memory 256MB ^
  --project %PROJECT_ID%

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo The Cloud Function will be automatically triggered when messages
echo arrive in the Pub/Sub topic: %TOPIC%
echo.
echo To view logs:
echo   gcloud functions logs read %FUNCTION_NAME% --region %REGION% --gen2 --project %PROJECT_ID%
echo.
echo To test, trigger your Reasoning Engine and check the logs!
echo.
pause
