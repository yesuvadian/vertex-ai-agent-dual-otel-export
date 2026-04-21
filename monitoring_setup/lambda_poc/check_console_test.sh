#!/bin/bash

echo "=========================================="
echo "Checking AWS Lambda for Console Test"
echo "=========================================="
echo ""
echo "Looking for message ID: console-test-001"
echo ""

MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test \
  --since 5m \
  --region us-east-1 \
  --format short | grep -A 10 -B 10 "console-test-001" || echo "Message not found yet - wait 30 seconds and try again"

echo ""
echo "=========================================="
echo "Check GCP Cloud Logging"
echo "=========================================="
echo ""
echo "Run this to see Reasoning Engine logs:"
echo ""
echo "gcloud logging read 'resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND resource.labels.reasoning_engine_id=\"3783824681212051456\" AND textPayload:\"console-test-001\"' --limit 10 --project agentic-ai-integration-490716"
echo ""
