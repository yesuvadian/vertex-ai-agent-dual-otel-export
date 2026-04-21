#!/bin/bash
# Deploy Lambda function only (no API Gateway)
# GCP Pub/Sub will invoke Lambda directly via AWS EventBridge or similar

set -e

echo "========================================"
echo "AWS Lambda Deployment (No API Gateway)"
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

# Get Lambda details
echo -e "${YELLOW}Step 3: Getting Lambda details...${NC}"
echo "  Lambda ARN: $LAMBDA_ARN"
echo ""

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "  AWS Account ID: $ACCOUNT_ID"
echo -e "${GREEN}✓ Lambda details retrieved${NC}"
echo ""

# Clean up
rm -f function.zip

echo ""
echo -e "${GREEN}========================================"
echo "✓ DEPLOYMENT SUCCESSFUL!"
echo "========================================${NC}"
echo ""
echo "Lambda Function Details:"
echo "  Name: $FUNCTION_NAME"
echo "  ARN: $LAMBDA_ARN"
echo "  Region: $REGION"
echo ""
echo "Next steps:"
echo ""
echo "1. Test Lambda directly:"
echo "   aws lambda invoke \\"
echo "     --function-name $FUNCTION_NAME \\"
echo "     --payload '{\"message\":{\"data\":\"SGVsbG8=\",\"messageId\":\"test\"}}' \\"
echo "     response.json"
echo "   cat response.json"
echo ""
echo "2. Watch Lambda logs:"
echo "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
echo "3. Configure GCP Pub/Sub (to be implemented):"
echo "   - Option A: Use AWS EventBridge for GCP integration"
echo "   - Option B: Use Lambda Function URL (if enabled)"
echo "   - Option C: Add API Gateway later"
echo ""

echo -e "${GREEN}Deployment complete!${NC}"
