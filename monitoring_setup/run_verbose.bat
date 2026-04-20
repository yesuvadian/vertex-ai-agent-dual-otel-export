@echo off
REM Verbose Portal26 Forwarder - See logs being sent to Portal26

echo ================================================================================
echo VERBOSE PORTAL26 FORWARDER
echo ================================================================================
echo This will show all logs being forwarded to Portal26
echo Press Ctrl+C to stop
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python monitor_to_portal26_verbose.py

pause
