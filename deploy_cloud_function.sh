#!/bin/bash

# Deploy AI Agent as Cloud Function using Vertex AI agent code

set -e

PROJECT_ID="agentic-ai-integration-490716"
REGION="us-central1"
FUNCTION_NAME="ai-agent-vertexai"

echo "=========================================="
echo "Deploying AI Agent as Cloud Function"
echo "=========================================="
echo ""
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Function: ${FUNCTION_NAME}"
echo ""

# Create main.py for Cloud Function
echo "Creating Cloud Function entry point..."
cat > main.py << 'EOF'
import functions_framework
from agent_vertexai import query
import json

@functions_framework.http
def query_agent(request):
    """HTTP Cloud Function entry point"""
    request_json = request.get_json(silent=True)

    if not request_json or 'user_input' not in request_json:
        return {'error': 'Missing user_input parameter'}, 400

    user_input = request_json['user_input']

    try:
        result = query(user_input)
        return result, 200
    except Exception as e:
        return {'error': str(e)}, 500
EOF

echo "[OK] Created main.py"

# Create requirements.txt for Cloud Function
echo "Creating requirements.txt..."
cat > requirements_cloudfunction.txt << 'EOF'
functions-framework
google-genai
google-cloud-aiplatform
python-dotenv
EOF

echo "[OK] Created requirements_cloudfunction.txt"

# Deploy Cloud Function
echo ""
echo "Deploying to Google Cloud Functions..."

gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime=python311 \
  --region=${REGION} \
  --source=. \
  --entry-point=query_agent \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}" \
  --set-env-vars="GOOGLE_CLOUD_API_KEY=$(grep GOOGLE_CLOUD_API_KEY .env | cut -d '=' -f2)" \
  --set-env-vars="OTEL_SERVICE_NAME=ai-agent-vertexai" \
  --set-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=$(grep OTEL_EXPORTER_OTLP_ENDPOINT .env | cut -d '=' -f2)" \
  --set-env-vars="OTEL_EXPORTER_OTLP_HEADERS=$(grep OTEL_EXPORTER_OTLP_HEADERS .env | cut -d '=' -f2)" \
  --set-env-vars="OTEL_TRACES_EXPORTER=otlp" \
  --set-env-vars="OTEL_METRICS_EXPORTER=otlp" \
  --set-env-vars="OTEL_LOGS_EXPORTER=otlp" \
  --memory=512MB \
  --timeout=300s

# Get function URL
FUNCTION_URL=$(gcloud functions describe ${FUNCTION_NAME} --region=${REGION} --gen2 --format='value(serviceConfig.uri)')

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Function URL: ${FUNCTION_URL}"
echo ""
echo "Test your deployment:"
echo ""
echo "  curl -X POST ${FUNCTION_URL} \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_input\": \"What is the weather in Tokyo?\"}'"
echo ""
