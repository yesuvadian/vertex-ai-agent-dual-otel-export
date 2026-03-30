#!/bin/bash

# Deployment script for AI Agent to Google Cloud Run

set -e  # Exit on error

# Configuration
PROJECT_ID="agentic-ai-integration-490716"
REGION="us-central1"
SERVICE_NAME="ai-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=========================================="
echo "Deploying AI Agent to Google Cloud Run"
echo "=========================================="
echo ""
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "Setting project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo ""
echo "Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    generativelanguage.googleapis.com

# Build the container image
echo ""
echo "Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}" \
    --set-env-vars="GOOGLE_CLOUD_API_KEY=$(grep GOOGLE_CLOUD_API_KEY .env | cut -d '=' -f2)" \
    --set-env-vars="OTEL_SERVICE_NAME=ai-agent" \
    --set-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=$(grep OTEL_EXPORTER_OTLP_ENDPOINT .env | cut -d '=' -f2)" \
    --set-env-vars="OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf" \
    --set-env-vars="OTEL_EXPORTER_OTLP_HEADERS=$(grep OTEL_EXPORTER_OTLP_HEADERS .env | cut -d '=' -f2)" \
    --set-env-vars="OTEL_TRACES_EXPORTER=otlp" \
    --set-env-vars="OTEL_METRICS_EXPORTER=otlp" \
    --set-env-vars="OTEL_LOGS_EXPORTER=otlp" \
    --set-env-vars="OTEL_METRIC_EXPORT_INTERVAL=1000" \
    --set-env-vars="OTEL_LOGS_EXPORT_INTERVAL=500" \
    --set-env-vars="OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=production" \
    --set-env-vars="AGENT_MODE=manual" \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 300

# Get the service URL
echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')

echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test your deployment:"
echo "  curl ${SERVICE_URL}/status"
echo ""
echo "  curl -X POST ${SERVICE_URL}/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"What is the weather in Tokyo?\"}'"
echo ""
