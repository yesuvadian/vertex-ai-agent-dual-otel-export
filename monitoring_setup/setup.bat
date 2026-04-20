@echo off
REM Windows Setup Script for Portal26 Integration

echo ================================================================================
echo Portal26 Integration - Windows Setup
echo ================================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/5] Python detected
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [2/5] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [2/5] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo [4/5] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Check .env file
echo [5/5] Checking configuration...
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please create .env from .env.example
    pause
    exit /b 1
)
echo [OK] Configuration file found
echo.

echo ================================================================================
echo Setup Complete!
echo ================================================================================
echo.
echo Next steps:
echo   1. Test connection: python test_portal26_connection.py
echo   2. Start forwarder: python monitor_pubsub_to_portal26_v2.py
echo.
pause
