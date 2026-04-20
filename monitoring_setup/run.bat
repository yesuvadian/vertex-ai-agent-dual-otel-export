@echo off
REM Start Portal26 Forwarder on Windows

echo ================================================================================
echo Starting Portal26 Forwarder
echo ================================================================================
echo.

REM Activate venv if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Press Ctrl+C to stop
echo.

REM Run forwarder
python monitor_pubsub_to_portal26_v2.py

pause
