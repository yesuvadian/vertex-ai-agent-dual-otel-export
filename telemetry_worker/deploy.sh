#!/bin/bash
# Deploy telemetry worker to Cloud Run

set -e

# Configuration
PROJECT="${GCP_PROJECT:-portal26-telemetry-prod}"
SERVICE="telemetry-worker"
REGION="${GCP_REGION:-us-central1}"
SA_NAME="telemetry-worker"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"

echo "=========================================="
echo "Deploying Telemetry Worker to Cloud Run"
echo "=========================================="
echo "Project: $PROJECT"
echo "Service: $SERVICE"
echo "Region: $REGION"
echo "Service Account: $SA_EMAIL"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Error: Not logged in to gcloud. Run: gcloud auth login"
    exit 1
fi

# Set project
echo "Setting project to $PROJECT..."
gcloud config set project $PROJECT

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudtrace.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create service account if it doesn't exist
echo "Checking service account..."
if ! gcloud iam service-accounts describe $SA_EMAIL &> /dev/null; then
    echo "Creating service account $SA_EMAIL..."
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Telemetry Processing Worker"
else
    echo "Service account $SA_EMAIL already exists"
fi

# Deploy to Cloud Run
echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE \
  --source . \
  --project=$PROJECT \
  --region=$REGION \
  --platform=managed \
  --service-account=$SA_EMAIL \
  --set-env-vars="PORTAL26_ENDPOINT=${PORTAL26_ENDPOINT:-https://otel.portal26.ai/v1/traces}" \
  --set-secrets="PORTAL26_USERNAME=portal26-user:latest,PORTAL26_PASSWORD=portal26-pass:latest" \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=100 \
  --concurrency=80 \
  --cpu=2 \
  --memory=1Gi \
  --timeout=60s

# Get Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE \
  --project=$PROJECT \
  --region=$REGION \
  --format='value(status.url)')

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Cloud Run URL: $CLOUD_RUN_URL"
echo ""
echo "Next steps:"
echo "1. Create Pub/Sub subscription (if not exists):"
echo "   ./setup_pubsub.sh"
echo ""
echo "2. Test health endpoint:"
echo "   curl ${CLOUD_RUN_URL}/health"
echo ""
echo "3. View logs:"
echo "   gcloud run services logs read $SERVICE --project=$PROJECT --region=$REGION"
echo "=========================================="
