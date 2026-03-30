#!/bin/bash
# Test both deployed agents

PROJECT_ID="agentic-ai-integration-490716"
REGION="us-central1"
RESOURCE_ID_LOCAL="1402185738425991168"
RESOURCE_ID_TEL="9130362698993762304"

TOKEN=$(gcloud auth print-access-token)

echo "================================"
echo "Testing portal26GCPLocal"
echo "================================"
echo ""

curl -X POST \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${RESOURCE_ID_LOCAL}:query" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What is the weather in Tokyo?"
    }
  }'

echo ""
echo ""
echo "================================"
echo "Testing portal26GCPTel"
echo "================================"
echo ""

curl -X POST \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${RESOURCE_ID_TEL}:query" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What is the weather in London?"
    }
  }'

echo ""
echo ""
echo "================================"
echo "Telemetry Monitoring"
echo "================================"
echo ""
echo "portal26GCPLocal telemetry:"
echo "  - ngrok UI:     http://localhost:4040"
echo "  - Local files:  otel-data/*.json"
echo "  - Portal26:     https://portal26.in (filter: service.name=portal26GCPLocal)"
echo ""
echo "portal26GCPTel telemetry:"
echo "  - Portal26:     https://portal26.in (filter: service.name=portal26GCPTel)"
echo ""
