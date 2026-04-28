@echo off
REM One-command deployment script for Windows CMD
REM Automatically sets credentials and deploys infrastructure

setlocal enabledelayedexpansion

set KEY_FILE=appengine-sa-key.json

echo ============================================
echo GCP Log Sink Deployment
echo ============================================
echo.

REM Check if key file exists
if not exist "%KEY_FILE%" (
    echo ERROR: %KEY_FILE% not found!
    echo Please generate your service account key first.
    echo See CLIENT_GUIDE.md Step 1
    exit /b 1
)

REM Check if terraform.tfvars exists
if not exist "terraform.tfvars" (
    echo ERROR: terraform.tfvars not found!
    echo Please copy and configure terraform.tfvars.example
    echo See CLIENT_GUIDE.md Step 3
    exit /b 1
)

REM Set credentials automatically
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\%KEY_FILE%
echo [1/3] OK Credentials set

REM Initialize Terraform
echo [2/3] Initializing Terraform...
terraform init
if errorlevel 1 exit /b 1

REM Deploy
echo [3/3] Deploying infrastructure...
terraform apply
if errorlevel 1 exit /b 1

echo.
echo ============================================
echo Deployment Complete!
echo ============================================
