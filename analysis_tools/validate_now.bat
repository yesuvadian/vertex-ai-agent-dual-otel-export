@echo off
REM Quick Validation Script for Windows
REM Runs analyzer and triggers test invocations

echo ========================================
echo Real Data Validation - Quick Start
echo ========================================
echo.

REM Check if in correct directory
if not exist "log_pattern_analyzer.py" (
    echo ERROR: Please run this script from the analysis_tools directory
    echo.
    echo Usage:
    echo   cd C:\Yesu\ai_agent_projectgcp\analysis_tools
    echo   validate_now.bat
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -c "import google.cloud.pubsub_v1" 2>nul
if errorlevel 1 (
    echo Installing google-cloud-pubsub...
    pip install google-cloud-pubsub
)

python -c "import vertexai" 2>nul
if errorlevel 1 (
    echo Installing vertexai...
    pip install vertexai
)

python -c "from dotenv import load_dotenv" 2>nul
if errorlevel 1 (
    echo Installing python-dotenv...
    pip install python-dotenv
)

echo Dependencies OK
echo.

REM Check for .env file
if not exist ".env" (
    if exist "..\monitoring_setup\.env" (
        echo [2/3] Copying .env from monitoring_setup...
        copy "..\monitoring_setup\.env" ".env" >nul
    ) else (
        echo Creating default .env...
        (
            echo GCP_PROJECT_ID=agentic-ai-integration-490716
            echo PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription
            echo ANALYSIS_DURATION=180
        ) > .env
    )
)

echo Configuration OK
echo.

echo [3/3] Ready to start validation
echo.
echo ========================================
echo INSTRUCTIONS:
echo ========================================
echo.
echo This script will open TWO command windows:
echo.
echo   Window 1: Log Analyzer (captures logs)
echo   Window 2: Test Generator (triggers your agent)
echo.
echo The analyzer will run for 3 minutes, then show results.
echo.
echo ========================================
echo.
set /p CONFIRM="Start validation now? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Starting analyzer in new window...
start "Log Analyzer" cmd /k "python log_pattern_analyzer.py"

echo Waiting 5 seconds for analyzer to start...
timeout /t 5 /nobreak >nul

echo.
echo Starting test invocations in new window...
echo.
echo IMPORTANT: Edit the command in the new window with your Reasoning Engine ID!
echo.
start "Test Invocations" cmd /k "echo Edit this command with your Reasoning Engine ID: && echo. && echo python test_agent_invocations.py --engine projects/961756870884/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID --count 5 --delay 10 && echo. && echo Then press Enter to run..."

echo.
echo ========================================
echo VALIDATION STARTED!
echo ========================================
echo.
echo Two windows opened:
echo   1. Log Analyzer - Running now
echo   2. Test Invocations - Edit and run
echo.
echo After 3 minutes, the analyzer will show results.
echo.
echo Look for a file named: log_analysis_report_YYYYMMDD_HHMMSS.json
echo.
echo To visualize:
echo   python trace_visualizer.py REPORT_FILE.json 0
echo.
echo ========================================

pause
