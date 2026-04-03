#!/bin/bash
# Test script for ngrok setup

echo "========================================"
echo "Testing Telemetry Worker with ngrok"
echo "========================================"
echo ""

# Check if ngrok URL is provided
if [ -z "$1" ]; then
    echo "Usage: ./test_ngrok.sh <NGROK_URL>"
    echo ""
    echo "Example:"
    echo "  ./test_ngrok.sh https://abc123.ngrok.io"
    echo ""
    echo "Steps:"
    echo "1. Start Flask: python main.py"
    echo "2. Start ngrok: ngrok http 8080"
    echo "3. Copy ngrok URL"
    echo "4. Run this script with the URL"
    exit 1
fi

NGROK_URL=$1
echo "ngrok URL: $NGROK_URL"
echo ""

# Step 1: Test health endpoint
echo "Step 1: Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" ${NGROK_URL}/health)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Health check passed (200)"
else
    echo "✗ Health check failed ($HTTP_CODE)"
    exit 1
fi
echo ""

# Step 2: Update Pub/Sub subscription
echo "Step 2: Updating Pub/Sub subscription..."
gcloud pubsub subscriptions update telemetry-processor \
  --push-endpoint="${NGROK_URL}/process" \
  --project=agentic-ai-integration-490716

ENDPOINT=$(gcloud pubsub subscriptions describe telemetry-processor \
  --project=agentic-ai-integration-490716 \
  --format="value(pushConfig.pushEndpoint)")

if [ "$ENDPOINT" = "${NGROK_URL}/process" ]; then
    echo "✓ Pub/Sub updated successfully"
else
    echo "✗ Pub/Sub update failed"
    exit 1
fi
echo ""

# Step 3: Get a trace ID
echo "Step 3: Getting a recent trace ID..."
cd ../gcp_traces_agent_client
TRACE_ID=$(python view_traces.py --hours 24 --limit 1 --no-filter 2>&1 | grep "Trace ID:" | head -1 | awk '{print $3}')
cd ../telemetry_worker_ngrok

if [ -z "$TRACE_ID" ]; then
    echo "✗ No traces found. Using test trace ID..."
    TRACE_ID="677b68ce5e429ca85cdc16ef54631ee6"
fi
echo "Using trace ID: $TRACE_ID"
echo ""

# Step 4: Test direct POST
echo "Step 4: Testing direct POST to worker..."
python test_local.py \
  agentic-ai-integration-490716 \
  $TRACE_ID \
  test_tenant_ngrok \
  ${NGROK_URL}/process

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Check Flask logs (Terminal 1) for processing details"
echo "2. Check ngrok dashboard: http://localhost:4040"
echo "3. Test with real agent:"
echo "   https://console.cloud.google.com/vertex-ai/agents/agent-engines/8081657304514035712"
echo "4. Watch logs in Flask terminal"
echo ""
echo "When done, run:"
echo "  ./cleanup.sh"
