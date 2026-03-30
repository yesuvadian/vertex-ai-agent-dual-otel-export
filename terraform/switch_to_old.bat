@echo off
echo ========================================================================
echo Switching BACK to OLD/WORKING values
echo ========================================================================
echo.

REM Switch back to old configuration
copy terraform.tfvars.backup terraform.tfvars
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy old values
    exit /b 1
)

echo [OK] Switched back to old/working configuration
echo.

REM Show what will change
echo Previewing changes...
echo.
terraform plan

echo.
echo ========================================================================
echo Ready to apply OLD/WORKING values
echo ========================================================================
echo.
echo OLD/WORKING VALUES:
echo   - ngrok endpoint: https://tabetha-unelemental-bibulously.ngrok-free.dev
echo   - otel endpoint:  https://otel-tenant1.portal26.in:4318
echo   - tenant_id:      tenant1
echo   - user.id:        relusys
echo   - service names:  portal26_ngrok_agent / portal26_otel_agent
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
echo 4. Test agents: cd .. ^& python test_tracer_provider.py
echo.
echo [SUCCESS] Back to working configuration!
echo.
