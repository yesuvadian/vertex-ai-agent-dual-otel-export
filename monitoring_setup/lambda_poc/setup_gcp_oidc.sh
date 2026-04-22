#!/bin/bash

# Setup GCP OIDC authentication for Pub/Sub to AWS Lambda

set -e

PROJECT_ID="agentic-ai-integration-490716"
TOPIC_NAME="reasoning-engine-logs-topic"
LAMBDA_URL="https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor.lambda-url.us-east-1.on.aws/"
SERVICE_ACCOUNT_NAME="pubsub-oidc-invoker"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "============================================================"
echo "Setup GCP OIDC Authentication for Pub/Sub"
echo "============================================================"
echo "Project: $PROJECT_ID"
echo "Lambda URL: $LAMBDA_URL"
echo ""

# Create service account
echo "[1/4] Creating service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name="Pub/Sub OIDC Token Generator" \
  --description="Service account for generating OIDC tokens for Pub/Sub push subscriptions" \
  --project=$PROJECT_ID \
  2>/dev/null || echo "[OK] Service account already exists"

echo "[OK] Service account: $SERVICE_ACCOUNT_EMAIL"

# Grant token creator role (allows creating OIDC tokens)
echo "[2/4] Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --condition=None \
  > /dev/null 2>&1 || true

echo "[OK] Granted roles/iam.serviceAccountTokenCreator"

# Delete old subscription if exists
echo "[3/4] Creating Pub/Sub subscription with OIDC..."
gcloud pubsub subscriptions delete reasoning-engine-to-oidc \
  --project=$PROJECT_ID \
  --quiet \
  2>/dev/null || true

# Create subscription with OIDC authentication
gcloud pubsub subscriptions create reasoning-engine-to-oidc \
  --topic=$TOPIC_NAME \
  --push-endpoint="$LAMBDA_URL" \
  --push-auth-service-account=$SERVICE_ACCOUNT_EMAIL \
  --push-auth-token-audience="$LAMBDA_URL" \
  --ack-deadline=10 \
  --message-retention-duration=7d \
  --project=$PROJECT_ID

echo "[OK] Subscription created: reasoning-engine-to-oidc"

# Verify configuration
echo "[4/4] Verifying configuration..."
gcloud pubsub subscriptions describe reasoning-engine-to-oidc \
  --project=$PROJECT_ID \
  --format=json > /tmp/subscription_config.json

echo ""
echo "Subscription Configuration:"
python3 -c "
import json
with open('/tmp/subscription_config.json') as f:
    config = json.load(f)
    print(f\"  Topic: {config['topic']}\")
    print(f\"  Push Endpoint: {config['pushConfig']['pushEndpoint']}\")
    if 'oidcToken' in config['pushConfig']:
        print(f\"  OIDC Service Account: {config['pushConfig']['oidcToken']['serviceAccountEmail']}\")
        print(f\"  OIDC Audience: {config['pushConfig']['oidcToken'].get('audience', 'N/A')}\")
    print(f\"  State: {config['state']}\")
"

rm -f /tmp/subscription_config.json

echo ""
echo "============================================================"
echo "OIDC Setup Complete!"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "  Subscription: reasoning-engine-to-oidc"
echo "  Lambda URL: $LAMBDA_URL"
echo "  OIDC Audience: $LAMBDA_URL"
echo ""
echo "How it works:"
echo "  1. Pub/Sub generates OIDC JWT token using service account"
echo "  2. Token added as 'Authorization: Bearer <JWT>' header"
echo "  3. Lambda validates JWT signature and audience"
echo "  4. If valid -> process message, else reject"
echo ""
echo "Test with:"
echo "  python test_local.py"
echo ""
echo "Wait 1-2 minutes, then check Lambda logs:"
echo "  MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-oidc --since 5m --region us-east-1"
echo ""
