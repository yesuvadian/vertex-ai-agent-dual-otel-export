#!/bin/bash
# Deploy GCP Pub/Sub to AWS Lambda POC

set -e

echo "========================================"
echo "GCP Pub/Sub → AWS Lambda POC Deployment"
echo "========================================"
echo ""

# Configuration
FUNCTION_NAME="gcp-pubsub-test"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
REGION="us-east-1"
API_NAME="gcp-pubsub-api"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Configuration:"
echo "  Function: $FUNCTION_NAME"
echo "  Runtime: $RUNTIME"
echo "  Region: $REGION"
echo ""

# Step 1: Create deployment package
echo -e "${YELLOW}Step 1: Creating deployment package...${NC}"
if [ -f function.zip ]; then
    rm function.zip
fi

zip function.zip lambda_function.py
echo -e "${GREEN}✓ Deployment package created${NC}"
echo ""

# Step 2: Check if Lambda function exists
echo -e "${YELLOW}Step 2: Checking if Lambda function exists...${NC}"
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &> /dev/null; then
    echo "  Function exists. Updating..."

    # Update function code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION \
        --query 'FunctionArn' \
        --output text

    echo -e "${GREEN}✓ Lambda function updated${NC}"
else
    echo "  Function does not exist. Creating..."

    # Check if execution role exists
    ROLE_NAME="lambda-gcp-pubsub-role"
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null || echo "")

    if [ -z "$ROLE_ARN" ]; then
        echo "  Creating IAM role..."

        # Create trust policy
        cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

        # Create role
        ROLE_ARN=$(aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document file://trust-policy.json \
            --query 'Role.Arn' \
            --output text)

        # Attach basic execution policy
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

        echo "  Waiting 10 seconds for IAM role to propagate..."
        sleep 10

        rm trust-policy.json
        echo -e "${GREEN}✓ IAM role created${NC}"
    else
        echo "  Using existing IAM role: $ROLE_ARN"
    fi

    # Create Lambda function
    LAMBDA_ARN=$(aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://function.zip \
        --region $REGION \
        --timeout 30 \
        --memory-size 256 \
        --query 'FunctionArn' \
        --output text)

    echo -e "${GREEN}✓ Lambda function created${NC}"
fi
echo ""

# Step 3: Get Lambda ARN
echo -e "${YELLOW}Step 3: Getting Lambda ARN...${NC}"
LAMBDA_ARN=$(aws lambda get-function \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Configuration.FunctionArn' \
    --output text)

echo "  Lambda ARN: $LAMBDA_ARN"
echo -e "${GREEN}✓ Lambda ARN retrieved${NC}"
echo ""

# Step 4: Create or update API Gateway
echo -e "${YELLOW}Step 4: Setting up API Gateway...${NC}"

# Check if API exists
API_ID=$(aws apigatewayv2 get-apis --region $REGION --query "Items[?Name=='$API_NAME'].ApiId" --output text)

if [ -z "$API_ID" ]; then
    echo "  Creating new HTTP API..."

    # Create HTTP API with Lambda integration
    API_ID=$(aws apigatewayv2 create-api \
        --name $API_NAME \
        --protocol-type HTTP \
        --region $REGION \
        --query 'ApiId' \
        --output text)

    echo "  API created with ID: $API_ID"

    # Create integration
    INTEGRATION_ID=$(aws apigatewayv2 create-integration \
        --api-id $API_ID \
        --integration-type AWS_PROXY \
        --integration-uri $LAMBDA_ARN \
        --payload-format-version 2.0 \
        --region $REGION \
        --query 'IntegrationId' \
        --output text)

    echo "  Integration created with ID: $INTEGRATION_ID"

    # Create route
    aws apigatewayv2 create-route \
        --api-id $API_ID \
        --route-key 'POST /webhook' \
        --target integrations/$INTEGRATION_ID \
        --region $REGION \
        --query 'RouteId' \
        --output text > /dev/null

    echo "  Route created: POST /webhook"

    # Create auto-deploy stage
    aws apigatewayv2 create-stage \
        --api-id $API_ID \
        --stage-name '$default' \
        --auto-deploy \
        --region $REGION > /dev/null

    echo "  Stage created: \$default (auto-deploy)"

    echo -e "${GREEN}✓ API Gateway created${NC}"
else
    echo "  Using existing API Gateway: $API_ID"
    echo -e "${GREEN}✓ API Gateway already exists${NC}"
fi
echo ""

# Step 5: Add Lambda permission for API Gateway
echo -e "${YELLOW}Step 5: Adding API Gateway permissions...${NC}"

# Remove existing permission if it exists
aws lambda remove-permission \
    --function-name $FUNCTION_NAME \
    --statement-id AllowAPIGateway \
    --region $REGION &> /dev/null || true

# Add permission
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id AllowAPIGateway \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:*:$API_ID/*/*/webhook" \
    --region $REGION > /dev/null

echo -e "${GREEN}✓ Permission added${NC}"
echo ""

# Step 6: Get API endpoint
echo -e "${YELLOW}Step 6: Getting API endpoint...${NC}"
API_ENDPOINT=$(aws apigatewayv2 get-api \
    --api-id $API_ID \
    --region $REGION \
    --query 'ApiEndpoint' \
    --output text)

WEBHOOK_URL="$API_ENDPOINT/webhook"
echo ""
echo -e "${GREEN}========================================"
echo "✓ DEPLOYMENT SUCCESSFUL!"
echo "========================================${NC}"
echo ""
echo "Your webhook endpoint:"
echo -e "${GREEN}$WEBHOOK_URL${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the endpoint:"
echo "   curl -X POST $WEBHOOK_URL \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": {\"data\": \"SGVsbG8=\", \"messageId\": \"test-123\"}}'"
echo ""
echo "2. Configure GCP Pub/Sub:"
echo "   gcloud pubsub subscriptions create test-aws-lambda-push \\"
echo "     --topic test-topic \\"
echo "     --push-endpoint $WEBHOOK_URL \\"
echo "     --project agentic-ai-integration-490716"
echo ""
echo "3. Watch Lambda logs:"
echo "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
echo "4. Send test message from GCP:"
echo "   gcloud pubsub topics publish test-topic \\"
echo "     --message 'Hello from GCP!' \\"
echo "     --project agentic-ai-integration-490716"
echo ""

# Save endpoint to file
echo $WEBHOOK_URL > webhook_url.txt
echo "Webhook URL saved to: webhook_url.txt"
echo ""

# Clean up
rm function.zip

echo -e "${GREEN}Deployment complete!${NC}"
