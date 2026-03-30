@echo off
REM Quick Start Script for Local OTEL Collector

echo ====================================================================
echo LOCAL OTEL COLLECTOR - QUICK START
echo ====================================================================
echo.

REM Check Docker
echo [1/4] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found! Please install Docker Desktop.
    echo Download: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)
echo [OK] Docker is installed
echo.

REM Create data directory
echo [2/4] Creating data directory...
if not exist "otel-data" mkdir otel-data
echo [OK] Data directory ready
echo.

REM Start collector
echo [3/4] Starting OTEL Collector...
docker-compose -f docker-compose-otel-collector.yml up -d
if errorlevel 1 (
    echo [ERROR] Failed to start collector
    pause
    exit /b 1
)
echo [OK] Collector started
echo.

REM Wait for collector to be ready
echo Waiting for collector to initialize...
timeout /t 3 /nobreak >nul
echo.

REM Check collector status
echo [4/4] Checking collector status...
docker ps | findstr "otel-collector"
if errorlevel 1 (
    echo [WARNING] Collector may not be running
) else (
    echo [OK] Collector is running
)
echo.

echo ====================================================================
echo NEXT STEPS:
echo ====================================================================
echo.
echo 1. Start ngrok in a NEW terminal:
echo    ngrok http 4318
echo.
echo 2. Copy the ngrok HTTPS URL (e.g., https://abc123.ngrok.io)
echo.
echo 3. Update Cloud Run with the ngrok URL:
echo    gcloud run services update ai-agent --region=us-central1 \
echo      --update-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=https://YOUR_NGROK_URL"
echo.
echo 4. Send test request:
echo    TOKEN=$(gcloud auth print-identity-token)
echo    curl -X POST https://ai-agent-czvzx73drq-uc.a.run.app/chat \
echo      -H "Authorization: Bearer $TOKEN" \
echo      -H "Content-Type: application/json" \
echo      -d "{\"message\": \"Test local collector\"}"
echo.
echo 5. View data:
echo    - Collector logs: docker logs local-otel-collector -f
echo    - ngrok requests: http://localhost:4040
echo    - Local files: dir otel-data
echo.
echo ====================================================================
echo.
pause
