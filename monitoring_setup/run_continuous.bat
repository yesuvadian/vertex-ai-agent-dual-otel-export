@echo off
REM Continuous Pull-Based Forwarder - Production Mode

echo ================================================================================
echo CONTINUOUS PULL-BASED FORWARDER
echo ================================================================================
echo This runs continuously, pulling logs and forwarding to Portal26
echo Press Ctrl+C to stop gracefully
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python continuous_forwarder.py

pause
