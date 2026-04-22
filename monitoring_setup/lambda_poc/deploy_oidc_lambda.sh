#!/bin/bash

# Deploy Lambda with OIDC authentication

set -e

REGION="us-east-1"
FUNCTION_NAME="gcp-pubsub-oidc"

echo "============================================================"
echo "Deploying Lambda with OIDC Authentication"
echo "============================================================"

# Install dependencies
echo "[1/5] Installing Python dependencies..."
pip install -r requirements_oidc.txt -t ./package --quiet

# Copy Lambda function
echo "[2/5] Packaging Lambda function..."
cp lambda_with_oidc.py package/
cd package
zip -r ../lambda_oidc.zip . -q
cd ..
rm -rf package

echo "[OK] Package created: lambda_oidc.zip"

# Create Lambda function
echo "[3/5] Creating Lambda function..."
aws lambda create-function \
  --function-name $FUNCTION_NAME \
  --runtime python3.11 \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-gcp-pubsub-role \
  --handler lambda_with_oidc.lambda_handler \
  --zip-file fileb://lambda_oidc.zip \
  --timeout 120 \
  --memory-size 256 \
  --region $REGION \
  --description "GCP Pub/Sub handler with OIDC JWT authentication" \
  2>/dev/null || {
    echo "[INFO] Function exists, updating code..."
    aws lambda update-function-code \
      --function-name $FUNCTION_NAME \
      --zip-file fileb://lambda_oidc.zip \
      --region $REGION \
      > /dev/null
  }

echo "[OK] Lambda function deployed"

# Wait for function to be active
echo "[4/5] Waiting for function to be ready..."
aws lambda wait function-active --function-name $FUNCTION_NAME --region $REGION

# Get or create Function URL
echo "[5/5] Getting Function URL..."
FUNCTION_URL=$(aws lambda get-function-url-config \
  --function-name $FUNCTION_NAME \
  --region $REGION \
  --query 'FunctionUrl' \
  --output text 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
    echo "[INFO] Creating Function URL..."
    echo "[WARN] You need to create Function URL manually via AWS Console"
    echo "       https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/$FUNCTION_NAME"
    FUNCTION_URL="[CREATE_VIA_CONSOLE]"
else
    echo "[OK] Function URL: $FUNCTION_URL"
fi

# Save configuration
cat > oidc_lambda_config.txt <<EOF
============================================================
Lambda with OIDC Authentication
============================================================
Generated: $(date)

Function Name: $FUNCTION_NAME
Function ARN: arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME
Region: $REGION
Runtime: Python 3.11

Function URL: $FUNCTION_URL

Auth Type: OIDC (Google Cloud JWT tokens)
Expected Issuer: https://accounts.google.com
Expected Audience: <Lambda Function URL>

============================================================
Next Steps
============================================================

1. If Function URL not created, create it via AWS Console:
   https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/$FUNCTION_NAME
   - Configuration → Function URL → Create
   - Auth type: NONE
   - Copy the URL

2. Update Lambda environment variable with Function URL:
   aws lambda update-function-configuration \\
     --function-name $FUNCTION_NAME \\
     --environment Variables="{LAMBDA_URL=<YOUR_FUNCTION_URL>}" \\
     --region $REGION

3. Create GCP service account for OIDC:
   bash setup_gcp_oidc.sh

4. Configure Pub/Sub subscription with OIDC:
   bash configure_pubsub_oidc.sh

5. Test end-to-end:
   python test_local.py

============================================================
EOF

cat oidc_lambda_config.txt

echo ""
echo "============================================================"
echo "Deployment Complete!"
echo "============================================================"
echo ""
echo "Configuration saved: oidc_lambda_config.txt"
echo ""
echo "Next: Create Function URL via AWS Console, then run setup_gcp_oidc.sh"
echo ""

# Cleanup
rm -f lambda_oidc.zip

