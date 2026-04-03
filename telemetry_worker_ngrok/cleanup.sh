#!/bin/bash
# Cleanup script - restore Pub/Sub to Cloud Run

echo "========================================"
echo "Cleanup: Restoring Pub/Sub to Cloud Run"
echo "========================================"
echo ""

CLOUD_RUN_URL="https://telemetry-worker-961756870884.us-central1.run.app"

echo "Updating Pub/Sub subscription to point back to Cloud Run..."
gcloud pubsub subscriptions update telemetry-processor \
  --push-endpoint="${CLOUD_RUN_URL}/process" \
  --project=agentic-ai-integration-490716

ENDPOINT=$(gcloud pubsub subscriptions describe telemetry-processor \
  --project=agentic-ai-integration-490716 \
  --format="value(pushConfig.pushEndpoint)")

echo ""
if [ "$ENDPOINT" = "${CLOUD_RUN_URL}/process" ]; then
    echo "✓ Pub/Sub restored to Cloud Run"
    echo "✓ Endpoint: $ENDPOINT"
else
    echo "✗ Restore failed"
    echo "Current endpoint: $ENDPOINT"
fi

echo ""
echo "Don't forget to:"
echo "1. Stop Flask (Ctrl+C in Terminal 1)"
echo "2. Stop ngrok (Ctrl+C in Terminal 2)"
echo ""
echo "========================================"
