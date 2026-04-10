@echo off
REM Test OTEL injection without deploying to Vertex AI

echo Testing OTEL Injection (Dry Run)
echo ================================
echo.
echo This will show how the agent code is modified without actually deploying.
echo.

REM Run the test injection script
python scripts\test_injection.py ^
  --source-dir "..\my_agent" ^
  --portal26-endpoint "https://portal26.example.com/test-client" ^
  --service-name "sample-weather-agent"

echo.
echo Test complete! The original agent file was NOT modified.
echo All changes were made in a temporary directory which has been cleaned up.

pause
