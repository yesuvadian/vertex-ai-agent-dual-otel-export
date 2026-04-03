#!/bin/bash
# Quick start script for local testing

echo "========================================"
echo "Telemetry Worker - Local Testing"
echo "========================================"
echo ""

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Run: cp .env.portal26 .env"
    exit 1
fi

echo "Starting Flask app on port 8080..."
echo ""
echo "Next steps:"
echo "1. Open another terminal and run: ngrok http 8080"
echo "2. Copy the ngrok URL"
echo "3. Update Pub/Sub subscription with ngrok URL"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

# Start Flask app
python main.py
