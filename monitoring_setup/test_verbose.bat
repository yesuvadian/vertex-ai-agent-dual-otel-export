@echo off
REM Verbose Pub/Sub Monitor - See what logs are coming in

echo ================================================================================
echo VERBOSE PUB/SUB MONITOR
echo ================================================================================
echo This will show all logs received from Pub/Sub (60 seconds)
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python monitor_pubsub_verbose.py

pause
