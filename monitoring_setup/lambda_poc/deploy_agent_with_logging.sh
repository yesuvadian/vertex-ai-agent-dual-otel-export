#!/bin/bash

# Deploy Agent Builder agent that captures logs to Cloud Logging
# Then forwards to AWS Lambda

set -e

PROJECT_ID="agentic-ai-integration-490716"
REGION="us-central1"
AGENT_NAME="monitoring-agent-with-logs"

echo "=========================================="
echo "Deploy Agent Builder Agent with Logging"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo ""

echo "[STEP 1] Create agent in Agent Builder Console"
echo ""
echo "Go to: https://console.cloud.google.com/vertex-ai/agent-builder/agents?project=$PROJECT_ID"
echo ""
echo "1. Click 'CREATE AGENT'"
echo "2. Name: $AGENT_NAME"
echo "3. Model: Gemini 2.0 Flash"
echo "4. Instructions:"
echo "   'Analyze GCP monitoring messages for severity and anomalies."
echo "    Detect errors, warnings, and performance issues."
echo "    Forward analyzed messages to AWS Lambda.'"
echo ""
echo "5. Add Tools:"
echo "   - analyze_message: Analyze text for severity"
echo "   - forward_to_lambda: Send to AWS Lambda"
echo ""
echo "6. Click 'CREATE'"
echo ""

echo "[STEP 2] Configure Cloud Logging Export"
echo ""
echo "Agent Builder agents log to:"
echo "  resource.type=\"agent_builder.googleapis.com/Agent\""
echo ""

# Create log sink for Agent Builder logs
LOG_SINK_NAME="agent-builder-to-aws"
TOPIC_NAME="agent-builder-logs"

echo "Creating Pub/Sub topic for Agent Builder logs..."
if ! gcloud pubsub topics describe $TOPIC_NAME --project $PROJECT_ID &>/dev/null; then
    gcloud pubsub topics create $TOPIC_NAME --project $PROJECT_ID
    echo "[OK] Topic created: $TOPIC_NAME"
else
    echo "[OK] Topic exists: $TOPIC_NAME"
fi

echo ""
echo "Creating push subscription to AWS Lambda..."
SUBSCRIPTION_NAME="agent-builder-to-lambda"
AWS_LAMBDA_URL="https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/"

if gcloud pubsub subscriptions describe $SUBSCRIPTION_NAME --project $PROJECT_ID &>/dev/null; then
    echo "Subscription exists, recreating..."
    gcloud pubsub subscriptions delete $SUBSCRIPTION_NAME --project $PROJECT_ID --quiet
fi

gcloud pubsub subscriptions create $SUBSCRIPTION_NAME \
  --topic $TOPIC_NAME \
  --push-endpoint $AWS_LAMBDA_URL \
  --project $PROJECT_ID

echo "[OK] Push subscription created"
echo ""

echo "Creating log sink for Agent Builder logs..."
if gcloud logging sinks describe $LOG_SINK_NAME --project $PROJECT_ID &>/dev/null; then
    echo "Log sink exists, deleting..."
    gcloud logging sinks delete $LOG_SINK_NAME --project $PROJECT_ID --quiet
fi

# Create log sink for Agent Builder
gcloud logging sinks create $LOG_SINK_NAME \
  pubsub.googleapis.com/projects/$PROJECT_ID/topics/$TOPIC_NAME \
  --log-filter='resource.type="agent_builder.googleapis.com/Agent" OR
                resource.type="aiplatform.googleapis.com/Agent" OR
                logName=~"agent"' \
  --project $PROJECT_ID

echo "[OK] Log sink created"
echo ""

# Grant permissions
SINK_SA=$(gcloud logging sinks describe $LOG_SINK_NAME --project $PROJECT_ID --format 'value(writerIdentity)')
echo "Granting permissions to: $SINK_SA"

gcloud pubsub topics add-iam-policy-binding $TOPIC_NAME \
  --member=$SINK_SA \
  --role=roles/pubsub.publisher \
  --project $PROJECT_ID

echo "[OK] Permissions granted"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Agent Builder logs will flow:"
echo "  Agent Builder Agent"
echo "    -> Cloud Logging"
echo "    -> Pub/Sub ($TOPIC_NAME)"
echo "    -> AWS Lambda"
echo "    -> Portal26"
echo ""
echo "Test your agent in:"
echo "  https://console.cloud.google.com/vertex-ai/agent-builder/agents?project=$PROJECT_ID"
echo ""
echo "Check Lambda logs:"
echo "  MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test --since 5m --region us-east-1"
echo ""
