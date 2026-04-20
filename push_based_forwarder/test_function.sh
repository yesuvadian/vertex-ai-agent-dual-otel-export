#!/bin/bash
# Test Cloud Function after deployment

set -e

PROJECT_ID="agentic-ai-integration-490716"
FUNCTION_NAME="vertex-to-portal26"
REGION="us-central1"

echo "========================================"
echo "Testing Cloud Function"
echo "========================================"
echo ""

# Check if function exists
echo "[1/3] Checking if function exists..."
gcloud functions describe $FUNCTION_NAME \
  --region $REGION \
  --gen2 \
  --project $PROJECT_ID \
  --format="value(name,state)"

echo ""
echo "[2/3] Viewing recent logs..."
gcloud functions logs read $FUNCTION_NAME \
  --region $REGION \
  --gen2 \
  --limit 10 \
  --project $PROJECT_ID

echo ""
echo "[3/3] Checking function metrics..."
echo ""
echo "To trigger the function:"
echo "  1. Go to your Reasoning Engine in GCP Console"
echo "  2. Send a test query"
echo "  3. Wait 1-2 minutes"
echo "  4. Run this script again to see logs"
echo ""
echo "To view logs in real-time:"
echo "  gcloud functions logs read $FUNCTION_NAME --region $REGION --gen2 --project $PROJECT_ID --follow"
echo ""
