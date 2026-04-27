@echo off
REM Deployment script using USER account credentials (not service account)
REM Run this when you want to use your own GCP login instead of service account

setlocal enabledelayedexpansion

echo ============================================
echo GCP Log Sink Deployment (User Account)
echo ============================================
echo.

REM Check if terraform.tfvars exists
if not exist "terraform.tfvars" (
    echo ERROR: terraform.tfvars not found!
    echo Please copy and configure terraform.tfvars.example
    echo See CLIENT_GUIDE.md Step 2
    exit /b 1
)

REM Use user's gcloud credentials (not service account key)
echo [1/4] Authenticating with your GCP account...
gcloud auth application-default login --no-launch-browser
if errorlevel 1 exit /b 1

echo [2/4] Credentials set from your GCP login

REM Initialize Terraform
echo [3/4] Initializing Terraform...
terraform init
if errorlevel 1 exit /b 1

REM Deploy
echo [4/4] Deploying infrastructure...
terraform apply
if errorlevel 1 exit /b 1

echo.
echo ============================================
echo Deployment Complete!
echo ============================================
