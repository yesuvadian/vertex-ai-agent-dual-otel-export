@echo off
REM Terraform Quick Start Script for Vertex AI Agent Engine (Windows)
REM Usage: quickstart.bat [init|plan|apply|status|help]

setlocal enabledelayedexpansion

set PROJECT_ID=agentic-ai-integration-490716
set REGION=us-central1

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="init" goto init
if "%1"=="plan" goto plan
if "%1"=="apply" goto apply
if "%1"=="status" goto status
if "%1"=="check" goto check

goto help

:check
echo ==========================================
echo Checking Prerequisites
echo ==========================================

where terraform >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Terraform not installed
    exit /b 1
)
echo [OK] Terraform installed

where gcloud >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] gcloud not installed
    exit /b 1
)
echo [OK] gcloud installed

gcloud auth application-default print-access-token >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] GCP not authenticated
    echo Run: gcloud auth application-default login
    exit /b 1
)
echo [OK] GCP authenticated

python -m google.adk.cli --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] google-adk not installed
    echo Run: pip install google-adk
    exit /b 1
)
echo [OK] google-adk installed

echo.
echo All prerequisites met!
goto :eof

:init
echo ==========================================
echo Initializing Terraform
echo ==========================================

if not exist terraform.tfvars (
    echo [INFO] terraform.tfvars not found. Creating from example...
    copy terraform.tfvars.example terraform.tfvars
    echo [SUCCESS] Created terraform.tfvars
    echo.
    echo Please review and customize terraform.tfvars before proceeding
    goto :eof
)

terraform init
if %errorlevel% neq 0 (
    echo [ERROR] Terraform init failed
    exit /b 1
)

echo [SUCCESS] Terraform initialized
goto :eof

:plan
echo ==========================================
echo Planning Terraform Changes
echo ==========================================

terraform plan
goto :eof

:apply
echo ==========================================
echo Applying Terraform Configuration
echo ==========================================

terraform apply
if %errorlevel% neq 0 (
    echo [ERROR] Terraform apply failed
    exit /b 1
)

echo.
echo [SUCCESS] Configuration applied
echo.
echo Next steps:
echo   1. Review the updated .env files
echo   2. To redeploy agents, set trigger_redeploy=true in terraform.tfvars
echo   3. Run: quickstart.bat apply
goto :eof

:status
echo ==========================================
echo Current Agent Status
echo ==========================================

echo portal26_ngrok_agent:
terraform output -raw portal26_ngrok_agent_id 2>nul
if %errorlevel% neq 0 (
    echo   ID: Not set
) else (
    echo   ID: %errorlevel%
)

echo.
echo portal26_otel_agent:
terraform output -raw portal26_otel_agent_id 2>nul
if %errorlevel% neq 0 (
    echo   ID: Not set
)

echo.
echo === portal26_ngrok_agent .env ===
if exist ..\portal26_ngrok_agent\.env (
    type ..\portal26_ngrok_agent\.env
) else (
    echo File not found
)

echo.
echo === portal26_otel_agent .env ===
if exist ..\portal26_otel_agent\.env (
    type ..\portal26_otel_agent\.env
) else (
    echo File not found
)

goto :eof

:help
echo Terraform Quick Start for Vertex AI Agent Engine
echo.
echo Usage: %0 [command]
echo.
echo Commands:
echo   init           - Initialize Terraform and create terraform.tfvars
echo   plan           - Preview changes
echo   apply          - Apply configuration changes
echo   status         - Show current agent status and env vars
echo   check          - Check prerequisites
echo   help           - Show this help message
echo.
echo Examples:
echo   %0 init        # First time setup
echo   %0 plan        # Preview changes
echo   %0 apply       # Apply changes
echo   %0 status      # Check current status
goto :eof
