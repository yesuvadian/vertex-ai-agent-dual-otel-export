#!/bin/bash
# Customer Onboarding Script
# Give this script to your customers to run in their GCP project

set -e

echo "=========================================="
echo "Customer Onboarding - Log Forwarding Setup"
echo "=========================================="
echo ""

# Customer must fill these variables
CUSTOMER_PROJECT_ID="YOUR-GCP-PROJECT-ID"
VENDOR_PROJECT_ID="agentic-ai-integration-490716"
VENDOR_TOPIC="all-customers-logs"
SINK_NAME="send-logs-to-vendor"

# Validate configuration
if [ "$CUSTOMER_PROJECT_ID" = "YOUR-GCP-PROJECT-ID" ]; then
    echo "ERROR: Please edit this script and set CUSTOMER_PROJECT_ID to your GCP project ID"
    exit 1
fi

echo "Configuration:"
echo "  Your Project: $CUSTOMER_PROJECT_ID"
echo "  Vendor Project: $VENDOR_PROJECT_ID"
echo "  Vendor Topic: $VENDOR_TOPIC"
echo ""
read -p "Is this correct? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "[1/3] Creating log sink in your project..."
gcloud logging sinks create $SINK_NAME \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --destination=pubsub.googleapis.com/projects/$VENDOR_PROJECT_ID/topics/$VENDOR_TOPIC \
  --project=$CUSTOMER_PROJECT_ID

if [ $? -eq 0 ]; then
    echo "SUCCESS: Log sink created"
else
    echo "ERROR: Failed to create log sink"
    exit 1
fi

echo ""
echo "[2/3] Getting service account identity..."
SERVICE_ACCOUNT=$(gcloud logging sinks describe $SINK_NAME \
  --project=$CUSTOMER_PROJECT_ID \
  --format="value(writerIdentity)")

if [ -z "$SERVICE_ACCOUNT" ]; then
    echo "ERROR: Could not retrieve service account"
    exit 1
fi

echo "SUCCESS: Service account retrieved"

echo ""
echo "[3/3] Verification..."
echo "Checking if log sink is active..."
SINK_STATUS=$(gcloud logging sinks describe $SINK_NAME \
  --project=$CUSTOMER_PROJECT_ID \
  --format="value(name)")

if [ -n "$SINK_STATUS" ]; then
    echo "SUCCESS: Log sink is active"
else
    echo "WARNING: Could not verify log sink status"
fi

echo ""
echo "============================================"
echo "SETUP COMPLETE!"
echo "============================================"
echo ""
echo "Next Steps:"
echo "1. Send the following information to your vendor:"
echo ""
echo "   Service Account:"
echo "   $SERVICE_ACCOUNT"
echo ""
echo "   Customer Project ID:"
echo "   $CUSTOMER_PROJECT_ID"
echo ""
echo "2. Wait for vendor to grant permission (usually within 24 hours)"
echo ""
echo "3. Your Reasoning Engine logs will automatically flow to vendor's monitoring"
echo ""
echo "To verify logs are being exported, run:"
echo "  gcloud logging read 'resource.type=\"aiplatform.googleapis.com/ReasoningEngine\"' --limit 5 --project=$CUSTOMER_PROJECT_ID"
echo ""
echo "To stop sending logs (revoke at any time):"
echo "  gcloud logging sinks delete $SINK_NAME --project=$CUSTOMER_PROJECT_ID"
echo ""
echo "============================================"
