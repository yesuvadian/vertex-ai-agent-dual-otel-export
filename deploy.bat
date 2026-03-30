@echo off
REM Deployment script for AI Agent to Google Cloud Run (Windows)

SET PROJECT_ID=agentic-ai-integration-490716
SET REGION=us-central1
SET SERVICE_NAME=ai-agent
SET IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%

echo ==========================================
echo Deploying AI Agent to Google Cloud Run
echo ==========================================
echo.
echo Project: %PROJECT_ID%
echo Region: %REGION%
echo Service: %SERVICE_NAME%
echo.

REM Check if gcloud is installed
where gcloud >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: gcloud CLI is not installed
    echo Install from: https://cloud.google.com/sdk/docs/install
    exit /b 1
)

REM Set project
echo Setting project...
gcloud config set project %PROJECT_ID%

REM Enable required APIs
echo.
echo Enabling required APIs...
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com generativelanguage.googleapis.com

REM Build the container image
echo.
echo Building container image...
gcloud builds submit --tag %IMAGE_NAME%

REM Get API key from .env
for /f "tokens=2 delims==" %%a in ('findstr "GOOGLE_CLOUD_API_KEY" .env') do set API_KEY=%%a
for /f "tokens=2 delims==" %%a in ('findstr "OTEL_EXPORTER_OTLP_ENDPOINT" .env') do set OTEL_ENDPOINT=%%a
for /f "tokens=2 delims==" %%a in ('findstr "OTEL_EXPORTER_OTLP_HEADERS" .env') do set OTEL_HEADERS=%%a

REM Deploy to Cloud Run
echo.
echo Deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --image %IMAGE_NAME% ^
    --platform managed ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --set-env-vars="GOOGLE_CLOUD_PROJECT=%PROJECT_ID%" ^
    --set-env-vars="GOOGLE_CLOUD_LOCATION=%REGION%" ^
    --set-env-vars="GOOGLE_CLOUD_API_KEY=%API_KEY%" ^
    --set-env-vars="OTEL_SERVICE_NAME=ai-agent" ^
    --set-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=%OTEL_ENDPOINT%" ^
    --set-env-vars="OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf" ^
    --set-env-vars="OTEL_EXPORTER_OTLP_HEADERS=%OTEL_HEADERS%" ^
    --set-env-vars="OTEL_TRACES_EXPORTER=otlp" ^
    --set-env-vars="OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=production" ^
    --set-env-vars="AGENT_MODE=manual" ^
    --memory 512Mi ^
    --cpu 1 ^
    --max-instances 10 ^
    --timeout 300

REM Get the service URL
echo.
echo ==========================================
echo Deployment complete!
echo ==========================================
echo.

gcloud run services describe %SERVICE_NAME% --region %REGION% --format="value(status.url)" > temp_url.txt
set /p SERVICE_URL=<temp_url.txt
del temp_url.txt

echo Service URL: %SERVICE_URL%
echo.
echo Test your deployment:
echo   curl %SERVICE_URL%/status
echo.
echo   curl -X POST %SERVICE_URL%/chat -H "Content-Type: application/json" -d "{\"message\": \"What is the weather in Tokyo?\"}"
echo.

pause
