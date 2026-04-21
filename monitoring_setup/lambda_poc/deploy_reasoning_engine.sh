#!/bin/bash

# Deploy Vertex AI Reasoning Engine to Cloud Run
# Integrates GCP Pub/Sub -> Reasoning Engine -> AWS Lambda

set -e

# Configuration
PROJECT_ID="agentic-ai-integration-490716"
REGION="us-central1"
SERVICE_NAME="monitoring-reasoning-agent"
AWS_LAMBDA_URL="https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/"

echo "=========================================="
echo "Deploying Reasoning Engine"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Step 1: Build and push container
echo "[1/5] Building container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --project $PROJECT_ID \
  --quiet

echo ""
echo "[OK] Container built successfully"
echo ""

# Step 2: Deploy to Cloud Run
echo "[2/5] Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars PROJECT_ID=$PROJECT_ID,AWS_LAMBDA_URL=$AWS_LAMBDA_URL \
  --project $PROJECT_ID \
  --quiet

echo ""
echo "[OK] Cloud Run service deployed"
echo ""

# Step 3: Get service URL
echo "[3/5] Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"
echo ""

# Step 4: Test health endpoint
echo "[4/5] Testing health endpoint..."
curl -s $SERVICE_URL/health | python -m json.tool
echo ""

# Step 5: Update Pub/Sub subscription
echo "[5/5] Updating Pub/Sub subscription..."

# Check if old subscription exists
if gcloud pubsub subscriptions describe aws-lambda-push-sub --project $PROJECT_ID &>/dev/null; then
    echo "Deleting old subscription: aws-lambda-push-sub"
    gcloud pubsub subscriptions delete aws-lambda-push-sub --project $PROJECT_ID --quiet
fi

# Create service account for Pub/Sub -> Cloud Run
SA_NAME="pubsub-reasoning-invoker"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Create service account if it doesn't exist
if ! gcloud iam service-accounts describe $SA_EMAIL --project $PROJECT_ID &>/dev/null; then
    echo "Creating service account: $SA_EMAIL"
    gcloud iam service-accounts create $SA_NAME \
      --display-name "Pub/Sub to Reasoning Engine Invoker" \
      --project $PROJECT_ID
fi

# Grant Cloud Run invoker permission
echo "Granting Cloud Run invoker permission..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.invoker" \
  --region=$REGION \
  --project=$PROJECT_ID \
  --quiet

# Create new push subscription
echo "Creating Pub/Sub subscription: reasoning-engine-sub"
gcloud pubsub subscriptions create reasoning-engine-sub \
  --topic test-topic \
  --push-endpoint $SERVICE_URL \
  --push-auth-service-account $SA_EMAIL \
  --project $PROJECT_ID

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Architecture:"
echo "  GCP Pub/Sub (test-topic)"
echo "      ↓"
echo "  Reasoning Engine ($SERVICE_URL)"
echo "      ↓ (AI Analysis + Enrichment)"
echo "  AWS Lambda ($AWS_LAMBDA_URL)"
echo "      ↓"
echo "  Portal26 OTEL Endpoint"
echo ""
echo "Test the integration:"
echo "  gcloud pubsub topics publish test-topic \\"
echo "    --message 'Test ERROR message from GCP' \\"
echo "    --project $PROJECT_ID"
echo ""
echo "View Reasoning Engine logs:"
echo "  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" \\"
echo "    --limit 50 \\"
echo "    --project $PROJECT_ID"
echo ""
