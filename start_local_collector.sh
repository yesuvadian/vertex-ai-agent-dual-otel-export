#!/bin/bash

# Quick Start Script for Local OTEL Collector

echo "===================================================================="
echo "LOCAL OTEL COLLECTOR - QUICK START"
echo "===================================================================="
echo ""

# Check Docker
echo "[1/4] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker not found! Please install Docker Desktop."
    echo "Download: https://docs.docker.com/desktop/install/"
    exit 1
fi
echo "[OK] Docker is installed"
echo ""

# Create data directory
echo "[2/4] Creating data directory..."
mkdir -p otel-data
echo "[OK] Data directory ready"
echo ""

# Start collector
echo "[3/4] Starting OTEL Collector..."
docker-compose -f docker-compose-otel-collector.yml up -d
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to start collector"
    exit 1
fi
echo "[OK] Collector started"
echo ""

# Wait for collector to be ready
echo "Waiting for collector to initialize..."
sleep 3
echo ""

# Check collector status
echo "[4/4] Checking collector status..."
if docker ps | grep -q "otel-collector"; then
    echo "[OK] Collector is running"
    docker ps | grep otel-collector
else
    echo "[WARNING] Collector may not be running"
fi
echo ""

echo "===================================================================="
echo "NEXT STEPS:"
echo "===================================================================="
echo ""
echo "1. Start ngrok in a NEW terminal:"
echo "   ngrok http 4318"
echo ""
echo "2. Copy the ngrok HTTPS URL (e.g., https://abc123.ngrok.io)"
echo ""
echo "3. Update Cloud Run with the ngrok URL:"
echo "   gcloud run services update ai-agent --region=us-central1 \\"
echo "     --update-env-vars=\"OTEL_EXPORTER_OTLP_ENDPOINT=https://YOUR_NGROK_URL\""
echo ""
echo "4. Send test request:"
echo "   TOKEN=\$(gcloud auth print-identity-token)"
echo "   curl -X POST https://ai-agent-czvzx73drq-uc.a.run.app/chat \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"message\": \"Test local collector\"}'"
echo ""
echo "5. View data:"
echo "   - Collector logs: docker logs local-otel-collector -f"
echo "   - ngrok requests: http://localhost:4040"
echo "   - Local files: ls -la otel-data/"
echo ""
echo "===================================================================="
echo ""
