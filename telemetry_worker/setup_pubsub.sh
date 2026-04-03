#!/bin/bash
# Set up Pub/Sub topic and subscription for telemetry worker

set -e

# Configuration
PROJECT="${GCP_PROJECT:-portal26-telemetry-prod}"
TOPIC="vertex-telemetry-topic"
SUBSCRIPTION="telemetry-processor"
SERVICE="telemetry-worker"
REGION="${GCP_REGION:-us-central1}"
SA_EMAIL="telemetry-worker@${PROJECT}.iam.gserviceaccount.com"

echo "=========================================="
echo "Setting up Pub/Sub Infrastructure"
echo "=========================================="
echo "Project: $PROJECT"
echo "Topic: $TOPIC"
echo "Subscription: $SUBSCRIPTION"
echo "=========================================="
echo ""

# Set project
gcloud config set project $PROJECT

# Enable Pub/Sub API
echo "Enabling Pub/Sub API..."
gcloud services enable pubsub.googleapis.com

# Create topic if it doesn't exist
echo "Checking Pub/Sub topic..."
if ! gcloud pubsub topics describe $TOPIC &> /dev/null; then
    echo "Creating Pub/Sub topic $TOPIC..."
    gcloud pubsub topics create $TOPIC \
        --message-retention-duration=7d
else
    echo "Topic $TOPIC already exists"
fi

# Get Cloud Run URL
echo "Getting Cloud Run service URL..."
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE \
  --project=$PROJECT \
  --region=$REGION \
  --format='value(status.url)')

if [ -z "$CLOUD_RUN_URL" ]; then
    echo "Error: Cloud Run service $SERVICE not found"
    echo "Deploy the service first with: ./deploy.sh"
    exit 1
fi

echo "Cloud Run URL: $CLOUD_RUN_URL"

# Create subscription if it doesn't exist
echo "Checking Pub/Sub subscription..."
if ! gcloud pubsub subscriptions describe $SUBSCRIPTION &> /dev/null; then
    echo "Creating Pub/Sub subscription $SUBSCRIPTION..."
    gcloud pubsub subscriptions create $SUBSCRIPTION \
        --topic=$TOPIC \
        --push-endpoint="${CLOUD_RUN_URL}/process" \
        --ack-deadline=60 \
        --max-delivery-attempts=5 \
        --min-retry-delay=10s \
        --max-retry-delay=600s
else
    echo "Subscription $SUBSCRIPTION already exists"
    echo "Updating push endpoint..."
    gcloud pubsub subscriptions update $SUBSCRIPTION \
        --push-endpoint="${CLOUD_RUN_URL}/process"
fi

# Grant Pub/Sub subscriber role to service account
echo "Granting Pub/Sub subscriber role..."
gcloud pubsub subscriptions add-iam-policy-binding $SUBSCRIPTION \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/pubsub.subscriber" \
    --project=$PROJECT

echo ""
echo "=========================================="
echo "Pub/Sub Setup Complete!"
echo "=========================================="
echo "Topic: projects/$PROJECT/topics/$TOPIC"
echo "Subscription: projects/$PROJECT/subscriptions/$SUBSCRIPTION"
echo "Push Endpoint: ${CLOUD_RUN_URL}/process"
echo ""
echo "Next steps:"
echo "1. Test by publishing a message:"
echo "   gcloud pubsub topics publish $TOPIC --message='test'"
echo ""
echo "2. View subscription details:"
echo "   gcloud pubsub subscriptions describe $SUBSCRIPTION"
echo ""
echo "3. Monitor message delivery:"
echo "   gcloud pubsub subscriptions pull $SUBSCRIPTION --auto-ack --limit=10"
echo "=========================================="
