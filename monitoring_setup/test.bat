@echo off
REM Quick test script for Windows

echo ================================================================================
echo Testing Portal26 Connection
echo ================================================================================
echo.

REM Activate venv if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run test
python test_portal26_connection.py

echo.
pause
