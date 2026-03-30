@echo off
echo ========================================================================
echo Switching to DUMMY values for testing
echo ========================================================================
echo.

REM Switch to dummy configuration
copy terraform.tfvars.dummy terraform.tfvars
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy dummy values
    exit /b 1
)

echo [OK] Switched to dummy configuration
echo.

REM Show what will change
echo Previewing changes...
echo.
terraform plan

echo.
echo ========================================================================
echo Ready to apply DUMMY values
echo ========================================================================
echo.
echo DUMMY VALUES:
echo   - ngrok endpoint: https://dummy-ngrok-endpoint.ngrok-free.dev
echo   - otel endpoint:  https://otel-test.portal26.in:4318
echo   - tenant_id:      tenant_test
echo   - user.id:        testuser
echo   - service names:  Added _TEST suffix
echo.
echo WARNING: Set trigger_redeploy=true to actually deploy to agents
echo.
echo Do you want to apply these changes? (This updates .env files only)
pause

terraform apply

echo.
echo ========================================================================
echo Next Steps:
echo ========================================================================
echo 1. Check .env files: type ..\portal26_ngrok_agent\.env
echo 2. To deploy agents, edit terraform.tfvars and set trigger_redeploy=true
echo 3. Then run: terraform apply
echo 4. Validate in Google Console
echo.
echo To switch back: run switch_to_old.bat
echo.
