#!/bin/bash

# Forward Vertex AI Reasoning Engine logs to AWS Lambda
# Architecture: Reasoning Engine → Cloud Logging → Log Sink → Pub/Sub → AWS Lambda

set -e

PROJECT_ID="agentic-ai-integration-490716"
REGION="us-central1"
REASONING_ENGINE_ID="3783824681212051456"
AWS_LAMBDA_URL="https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/"

# Topic and subscription names
REASONING_LOGS_TOPIC="reasoning-engine-logs-topic"
REASONING_LOGS_SUB="reasoning-engine-logs-to-aws"
LOG_SINK_NAME="reasoning-engine-to-pubsub"

echo "=========================================="
echo "Setup Reasoning Engine Logs → AWS Lambda"
echo "=========================================="
echo "Architecture:"
echo "  Vertex AI Reasoning Engine"
echo "      ↓ (automatic logs)"
echo "  Cloud Logging"
echo "      ↓ (log sink)"
echo "  Pub/Sub Topic ($REASONING_LOGS_TOPIC)"
echo "      ↓ (push subscription)"
echo "  AWS Lambda"
echo "      ↓"
echo "  Portal26 OTEL"
echo ""

# Step 1: Create Pub/Sub topic for Reasoning Engine logs
echo "[1/4] Creating Pub/Sub topic for Reasoning Engine logs..."
if gcloud pubsub topics describe $REASONING_LOGS_TOPIC --project $PROJECT_ID &>/dev/null; then
    echo "Topic already exists: $REASONING_LOGS_TOPIC"
else
    gcloud pubsub topics create $REASONING_LOGS_TOPIC --project $PROJECT_ID
    echo "[OK] Topic created"
fi
echo ""

# Step 2: Create push subscription to AWS Lambda
echo "[2/4] Creating push subscription to AWS Lambda..."
if gcloud pubsub subscriptions describe $REASONING_LOGS_SUB --project $PROJECT_ID &>/dev/null; then
    echo "Subscription already exists, deleting and recreating..."
    gcloud pubsub subscriptions delete $REASONING_LOGS_SUB --project $PROJECT_ID --quiet
fi

gcloud pubsub subscriptions create $REASONING_LOGS_SUB \
  --topic $REASONING_LOGS_TOPIC \
  --push-endpoint $AWS_LAMBDA_URL \
  --project $PROJECT_ID

echo "[OK] Push subscription created"
echo ""

# Step 3: Create log sink to forward Reasoning Engine logs to Pub/Sub
echo "[3/4] Creating log sink for Reasoning Engine logs..."

# Delete existing sink if it exists
if gcloud logging sinks describe $LOG_SINK_NAME --project $PROJECT_ID &>/dev/null; then
    echo "Log sink already exists, deleting and recreating..."
    gcloud logging sinks delete $LOG_SINK_NAME --project $PROJECT_ID --quiet
fi

# Create log sink with filter for Reasoning Engine
gcloud logging sinks create $LOG_SINK_NAME \
  pubsub.googleapis.com/projects/$PROJECT_ID/topics/$REASONING_LOGS_TOPIC \
  --log-filter="resource.type=\"aiplatform.googleapis.com/ReasoningEngine\"
AND resource.labels.reasoning_engine_id=\"$REASONING_ENGINE_ID\"" \
  --project $PROJECT_ID

echo "[OK] Log sink created"
echo ""

# Step 4: Grant Pub/Sub publisher permission to the sink's service account
echo "[4/4] Granting permissions..."

# Get the sink's service account
SINK_SA=$(gcloud logging sinks describe $LOG_SINK_NAME \
  --project $PROJECT_ID \
  --format 'value(writerIdentity)')

echo "Sink service account: $SINK_SA"

# Grant pubsub.publisher role to the sink's service account
gcloud pubsub topics add-iam-policy-binding $REASONING_LOGS_TOPIC \
  --member=$SINK_SA \
  --role=roles/pubsub.publisher \
  --project $PROJECT_ID

echo "[OK] Permissions granted"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Log Flow:"
echo "  1. Reasoning Engine logs → Cloud Logging (automatic)"
echo "  2. Cloud Logging → Pub/Sub ($REASONING_LOGS_TOPIC) via log sink"
echo "  3. Pub/Sub → AWS Lambda via push subscription"
echo "  4. Lambda → Portal26 OTEL endpoint"
echo ""
echo "Test the integration:"
echo ""
echo "1. Query Reasoning Engine:"
echo "   python - <<EOF"
echo "   import vertexai"
echo "   from vertexai.preview import reasoning_engines"
echo "   vertexai.init(project='$PROJECT_ID', location='$REGION', staging_bucket='gs://$PROJECT_ID-reasoning-engine')"
echo "   engine = reasoning_engines.ReasoningEngine('projects/961756870884/locations/$REGION/reasoningEngines/$REASONING_ENGINE_ID')"
echo "   result = engine.query(message={'data': 'VGVzdA==', 'messageId': 'test-123', 'publishTime': '2026-04-21T10:00:00Z'})"
echo "   print(result)"
echo "   EOF"
echo ""
echo "2. Wait 1-2 minutes for logs to flow"
echo ""
echo "3. Check Lambda logs:"
echo "   MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test --since 5m --region us-east-1"
echo ""
echo "4. Verify log sink:"
echo "   gcloud logging sinks describe $LOG_SINK_NAME --project $PROJECT_ID"
echo ""
echo "5. Check Pub/Sub metrics:"
echo "   gcloud pubsub topics describe $REASONING_LOGS_TOPIC --project $PROJECT_ID"
echo ""
