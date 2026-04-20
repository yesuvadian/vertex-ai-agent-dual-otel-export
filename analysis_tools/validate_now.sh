#!/bin/bash
# Quick Validation Script for Linux/Mac
# Runs analyzer and triggers test invocations

set -e

echo "========================================"
echo "Real Data Validation - Quick Start"
echo "========================================"
echo ""

# Check if in correct directory
if [ ! -f "log_pattern_analyzer.py" ]; then
    echo "ERROR: Please run this script from the analysis_tools directory"
    echo ""
    echo "Usage:"
    echo "  cd analysis_tools"
    echo "  ./validate_now.sh"
    exit 1
fi

# Check Python
if ! command -v python &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python not found. Please install Python."
        exit 1
    fi
    alias python=python3
fi

echo "[1/3] Checking dependencies..."
python -c "import google.cloud.pubsub_v1" 2>/dev/null || {
    echo "Installing google-cloud-pubsub..."
    pip install google-cloud-pubsub
}

python -c "import vertexai" 2>/dev/null || {
    echo "Installing vertexai..."
    pip install vertexai
}

python -c "from dotenv import load_dotenv" 2>/dev/null || {
    echo "Installing python-dotenv..."
    pip install python-dotenv
}

echo "Dependencies OK"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f "../monitoring_setup/.env" ]; then
        echo "[2/3] Copying .env from monitoring_setup..."
        cp ../monitoring_setup/.env .env
    else
        echo "Creating default .env..."
        cat > .env << EOF
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription
ANALYSIS_DURATION=180
EOF
    fi
fi

echo "Configuration OK"
echo ""

echo "[3/3] Ready to start validation"
echo ""
echo "========================================"
echo "INSTRUCTIONS:"
echo "========================================"
echo ""
echo "This script will open TWO terminals:"
echo ""
echo "  Terminal 1: Log Analyzer (captures logs)"
echo "  Terminal 2: Test Generator (triggers your agent)"
echo ""
echo "The analyzer will run for 3 minutes, then show results."
echo ""
echo "========================================"
echo ""
read -p "Start validation now? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Starting analyzer in new terminal..."

# Detect terminal type and open accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell application "Terminal" to do script "cd '"$PWD"' && python log_pattern_analyzer.py"'
    sleep 3
    osascript -e 'tell application "Terminal" to do script "cd '"$PWD"' && echo \"Edit this command with your Reasoning Engine ID:\" && echo \"\" && echo \"python test_agent_invocations.py --engine projects/961756870884/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID --count 5 --delay 10\""'
elif command -v gnome-terminal &> /dev/null; then
    # Linux with GNOME
    gnome-terminal -- bash -c "python log_pattern_analyzer.py; exec bash"
    sleep 3
    gnome-terminal -- bash -c "echo 'Edit this command with your Reasoning Engine ID:'; echo ''; echo 'python test_agent_invocations.py --engine projects/961756870884/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID --count 5 --delay 10'; exec bash"
elif command -v xterm &> /dev/null; then
    # Linux with xterm
    xterm -e "python log_pattern_analyzer.py; bash" &
    sleep 3
    xterm -e "echo 'Edit this command with your Reasoning Engine ID:'; echo ''; echo 'python test_agent_invocations.py --engine projects/961756870884/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID --count 5 --delay 10'; bash" &
else
    echo "Could not detect terminal. Running in current terminal..."
    echo ""
    echo "Please open another terminal and run:"
    echo "  cd $PWD"
    echo "  python test_agent_invocations.py --engine YOUR_ENGINE_ID --count 5 --delay 10"
    echo ""
    read -p "Press Enter to start analyzer..."
    python log_pattern_analyzer.py
    exit 0
fi

echo ""
echo "========================================"
echo "VALIDATION STARTED!"
echo "========================================"
echo ""
echo "Two terminals opened:"
echo "  1. Log Analyzer - Running now"
echo "  2. Test Invocations - Edit and run"
echo ""
echo "After 3 minutes, the analyzer will show results."
echo ""
echo "Look for a file named: log_analysis_report_YYYYMMDD_HHMMSS.json"
echo ""
echo "To visualize:"
echo "  python trace_visualizer.py REPORT_FILE.json 0"
echo ""
echo "========================================"
