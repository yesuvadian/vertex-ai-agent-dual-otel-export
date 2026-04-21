#!/bin/bash
# Deploy Lambda with Function URL (no API Gateway needed)
# Direct HTTPS endpoint for GCP Pub/Sub

set -e

echo "========================================"
echo "Lambda with Function URL Deployment"
echo "========================================"
echo ""

# Configuration
FUNCTION_NAME="gcp-pubsub-test"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
REGION="us-east-1"

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
    echo "  Function exists. Updating code..."

    # Update function code
    LAMBDA_ARN=$(aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION \
        --query 'FunctionArn' \
        --output text)

    echo -e "${GREEN}✓ Lambda function code updated${NC}"
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

# Step 3: Create or get Function URL
echo -e "${YELLOW}Step 3: Setting up Lambda Function URL...${NC}"

# Check if Function URL exists
FUNCTION_URL=$(aws lambda get-function-url-config \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'FunctionUrl' \
    --output text 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
    echo "  Creating Function URL..."

    # Create Function URL with NONE auth (for testing)
    FUNCTION_URL=$(aws lambda create-function-url-config \
        --function-name $FUNCTION_NAME \
        --auth-type NONE \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)

    echo -e "${GREEN}✓ Function URL created${NC}"

    # Add permission for public access
    echo "  Adding resource-based policy for public access..."
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id FunctionURLAllowPublicAccess \
        --action lambda:InvokeFunctionUrl \
        --principal "*" \
        --function-url-auth-type NONE \
        --region $REGION &> /dev/null || echo "  (Permission may already exist)"

    echo -e "${GREEN}✓ Public access enabled${NC}"
else
    echo "  Function URL already exists: $FUNCTION_URL"
    echo -e "${GREEN}✓ Using existing Function URL${NC}"
fi
echo ""

# Get Lambda details
echo -e "${YELLOW}Step 4: Getting Lambda details...${NC}"
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "  Lambda ARN: $LAMBDA_ARN"
echo "  AWS Account: $ACCOUNT_ID"
echo -e "${GREEN}✓ Lambda details retrieved${NC}"
echo ""

# Clean up
rm -f function.zip

echo ""
echo -e "${GREEN}========================================"
echo "✓ DEPLOYMENT SUCCESSFUL!"
echo "========================================${NC}"
echo ""
echo "Lambda Function URL (Direct HTTPS endpoint):"
echo -e "${GREEN}$FUNCTION_URL${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the Function URL:"
echo "   curl -X POST $FUNCTION_URL \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": {\"data\": \"SGVsbG8=\", \"messageId\": \"test-123\"}}'"
echo ""
echo "2. Watch Lambda logs:"
echo "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
echo "3. Configure GCP Pub/Sub:"
echo "   gcloud pubsub subscriptions create test-aws-lambda-push \\"
echo "     --topic test-topic \\"
echo "     --push-endpoint $FUNCTION_URL \\"
echo "     --project agentic-ai-integration-490716"
echo ""
echo "4. Send test message from GCP:"
echo "   gcloud pubsub topics publish test-topic \\"
echo "     --message 'Hello from GCP!' \\"
echo "     --project agentic-ai-integration-490716"
echo ""

# Save URL to file
echo $FUNCTION_URL > function_url.txt
echo "Function URL saved to: function_url.txt"
echo ""

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "⚠️  Note: Function URL has NO authentication for testing."
echo "    Add OIDC authentication for production use."
