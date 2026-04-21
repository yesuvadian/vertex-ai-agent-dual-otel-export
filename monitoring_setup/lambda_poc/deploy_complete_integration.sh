#!/bin/bash

# Complete integration: Pub/Sub -> Cloud Function -> Reasoning Engine -> AWS Lambda
# All logs captured automatically by Cloud Logging

set -e

PROJECT_ID="agentic-ai-integration-490716"
REGION="us-central1"
REASONING_ENGINE_ID="3783824681212051456"
FUNCTION_NAME="pubsub-reasoning-trigger"
TOPIC_NAME="test-topic"

echo "=========================================="
echo "Deploying Complete Integration"
echo "=========================================="
echo "Architecture:"
echo "  Pub/Sub (test-topic)"
echo "      ↓"
echo "  Cloud Function (pubsub-reasoning-trigger)"
echo "      ↓"
echo "  Vertex AI Reasoning Engine (3783824681212051456)"
echo "      ↓ (AI Analysis)"
echo "  AWS Lambda"
echo "      ↓"
echo "  Portal26 OTEL"
echo ""
echo "All logs captured in Cloud Logging automatically!"
echo ""

# Step 1: Deploy Cloud Function
echo "[1/3] Deploying Cloud Function..."
cd pubsub_trigger

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime python311 \
  --region $REGION \
  --source . \
  --entry-point pubsub_to_reasoning_engine \
  --trigger-topic $TOPIC_NAME \
  --set-env-vars PROJECT_ID=$PROJECT_ID,LOCATION=$REGION,REASONING_ENGINE_ID=$REASONING_ENGINE_ID \
  --memory 512MB \
  --timeout 300s \
  --max-instances 10 \
  --project $PROJECT_ID

cd ..

echo ""
echo "[OK] Cloud Function deployed"
echo ""

# Step 2: Test the integration
echo "[2/3] Testing integration..."
gcloud pubsub topics publish $TOPIC_NAME \
  --message "Test message with ERROR from integration test" \
  --project $PROJECT_ID

echo ""
echo "[OK] Test message published"
echo ""

# Step 3: Show how to view logs
echo "[3/3] View logs:"
echo ""
echo "Cloud Function logs:"
echo "  gcloud functions logs read $FUNCTION_NAME --region $REGION --project $PROJECT_ID --limit 50"
echo ""
echo "Reasoning Engine logs:"
echo "  gcloud logging read 'resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND resource.labels.reasoning_engine_id=\"$REASONING_ENGINE_ID\"' --limit 50 --project $PROJECT_ID"
echo ""
echo "AWS Lambda logs:"
echo "  MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test --since 5m --region us-east-1"
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "All logs automatically flow to Cloud Logging"
echo "Configure log sink to forward to Portal26"
echo ""
