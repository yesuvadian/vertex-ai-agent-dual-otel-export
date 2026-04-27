@echo off
REM Auto-set GOOGLE_APPLICATION_CREDENTIALS for Windows

set KEY_FILE=appengine-sa-key.json

REM Check if key file exists
if not exist "%KEY_FILE%" (
    echo ERROR: %KEY_FILE% not found!
    echo Please generate your service account key first.
    exit /b 1
)

REM Set the environment variable
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\%KEY_FILE%

echo.
echo [OK] Credentials set successfully!
echo      GOOGLE_APPLICATION_CREDENTIALS=%GOOGLE_APPLICATION_CREDENTIALS%
echo.
echo Note: This variable is only set for the current terminal session.
echo Run this script again if you open a new terminal.
echo.
