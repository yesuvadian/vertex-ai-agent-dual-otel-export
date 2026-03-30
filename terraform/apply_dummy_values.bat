@echo off
echo ========================================================================
echo Applying DUMMY values with Terraform
echo ========================================================================
echo.

REM Check if Terraform is installed
terraform version
if %errorlevel% neq 0 (
    echo ERROR: Terraform not found in PATH
    echo Please restart your terminal or add Terraform to PATH
    exit /b 1
)

echo.
echo Terraform found! Proceeding...
echo.

REM Initialize Terraform (if not already done)
echo Step 1: Initializing Terraform...
terraform init
if %errorlevel% neq 0 (
    echo ERROR: Terraform init failed
    exit /b 1
)

echo.
echo Step 2: Enabling redeployment...
echo.

REM Backup current tfvars
copy terraform.tfvars terraform.tfvars.temp

REM Enable trigger_redeploy
powershell -Command "(Get-Content terraform.tfvars) -replace 'trigger_redeploy = false', 'trigger_redeploy = true' | Set-Content terraform.tfvars"

echo [OK] Set trigger_redeploy = true
echo.

REM Show what will change
echo Step 3: Previewing changes...
echo.
terraform plan

echo.
echo ========================================================================
echo Ready to DEPLOY DUMMY values to agents
echo ========================================================================
echo.
echo This will:
echo   1. Update .env files with DUMMY values
echo   2. Redeploy BOTH agents (takes 2-3 minutes)
echo   3. You'll see changes in Google Console
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause

echo.
echo Step 4: Applying changes...
echo.
terraform apply -auto-approve

if %errorlevel% neq 0 (
    echo ERROR: Terraform apply failed
    REM Restore backup
    copy terraform.tfvars.temp terraform.tfvars
    exit /b 1
)

echo.
echo ========================================================================
echo SUCCESS! Agents are being redeployed with DUMMY values
echo ========================================================================
echo.
echo Next steps:
echo   1. Wait 2-3 minutes for deployment to complete
echo   2. Open Google Console: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716
echo   3. Click on portal26_ngrok_agent or portal26_otel_agent
echo   4. Go to "Deployment details" tab
echo   5. Check "Environment" section - you should see DUMMY values!
echo.
echo Expected DUMMY values:
echo   - OTEL_EXPORTER_OTLP_ENDPOINT: https://dummy-ngrok-endpoint.ngrok-free.dev
echo   - OTEL_SERVICE_NAME: portal26_ngrok_agent_TEST
echo   - OTEL_RESOURCE_ATTRIBUTES: tenant_test, testuser, ngrok-test
echo.
echo To switch back to old values, run: switch_to_old.bat
echo.
