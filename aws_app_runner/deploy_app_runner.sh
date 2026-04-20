#!/bin/bash
# AWS App Runner Deployment Script
# Simplest AWS deployment - 50% less complex than ECS Fargate

set -e

echo "=========================================="
echo "AWS App Runner Deployment"
echo "=========================================="
echo ""

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_NAME="gcp-log-forwarder"
APP_RUNNER_SERVICE_NAME="gcp-log-forwarder"
ROLE_NAME="AppRunnerGCPForwarderRole"

echo "Configuration:"
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo "  Region: $AWS_REGION"
echo "  Service: $APP_RUNNER_SERVICE_NAME"
echo ""

# Step 1: Create ECR repository
echo "[1/7] Creating ECR repository..."
aws ecr create-repository \
  --repository-name $ECR_REPO_NAME \
  --region $AWS_REGION \
  2>/dev/null || echo "  Repository already exists"

# Step 2: Login to ECR
echo ""
echo "[2/7] Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Step 3: Copy and build
echo ""
echo "[3/7] Building Docker image..."
cp ../aws_deployment/multi_destination_forwarder.py .
cp ../aws_deployment/requirements-multi.txt requirements.txt
cp ../aws_deployment/Dockerfile.multi Dockerfile

docker build -t $ECR_REPO_NAME:latest .

# Step 4: Tag and push
echo ""
echo "[4/7] Pushing to ECR..."
docker tag $ECR_REPO_NAME:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

# Step 5: Create IAM role for App Runner
echo ""
echo "[5/7] Creating IAM roles..."

# Instance role trust policy
cat > instance-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "tasks.apprunner.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create instance role
aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document file://instance-trust-policy.json \
  2>/dev/null || echo "  Role already exists"

# Attach policies
cat > instance-role-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:gcp-*",
        "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:portal26-*",
        "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:kinesis-*",
        "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:s3-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords"
      ],
      "Resource": "arn:aws:kinesis:$AWS_REGION:$AWS_ACCOUNT_ID:stream/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::*/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name AppRunnerForwarderPolicy \
  --policy-document file://instance-role-policy.json

# Create access role for ECR
cat > access-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "build.apprunner.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
  --role-name AppRunnerECRAccessRole \
  --assume-role-policy-document file://access-trust-policy.json \
  2>/dev/null || echo "  ECR access role already exists"

aws iam attach-role-policy \
  --role-name AppRunnerECRAccessRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess \
  2>/dev/null || true

echo "  IAM roles created"

# Step 6: Check if secrets exist
echo ""
echo "[6/7] Checking secrets..."
SECRETS_NEEDED=(
  "gcp-service-account-json"
  "portal26-endpoint"
  "portal26-auth-header"
  "portal26-tenant-id"
  "portal26-user-id"
)

MISSING_SECRETS=()
for secret in "${SECRETS_NEEDED[@]}"; do
  if ! aws secretsmanager describe-secret --secret-id $secret --region $AWS_REGION >/dev/null 2>&1; then
    MISSING_SECRETS+=($secret)
  fi
done

if [ ${#MISSING_SECRETS[@]} -ne 0 ]; then
  echo "  WARNING: Missing secrets:"
  for secret in "${MISSING_SECRETS[@]}"; do
    echo "    - $secret"
  done
  echo ""
  echo "  Create secrets before deploying:"
  echo "  aws secretsmanager create-secret --name SECRET_NAME --secret-string VALUE --region $AWS_REGION"
  echo ""
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Step 7: Create App Runner service
echo ""
echo "[7/7] Creating App Runner service..."

# Get role ARNs
INSTANCE_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME"
ACCESS_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/AppRunnerECRAccessRole"

aws apprunner create-service \
  --service-name $APP_RUNNER_SERVICE_NAME \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$AWS_ACCOUNT_ID'.dkr.ecr.'$AWS_REGION'.amazonaws.com/'$ECR_REPO_NAME':latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "RuntimeEnvironmentVariables": {
          "GCP_PROJECT_ID": "agentic-ai-integration-490716",
          "PUBSUB_SUBSCRIPTION": "all-customers-logs-sub",
          "OTEL_SERVICE_NAME": "gcp-vertex-monitor",
          "SMALL_LOG_THRESHOLD": "102400",
          "LARGE_LOG_THRESHOLD": "1048576",
          "HIGH_VOLUME_THRESHOLD": "100",
          "PORTAL26_BATCH_SIZE": "20",
          "KINESIS_BATCH_SIZE": "100",
          "S3_BATCH_SIZE": "500",
          "AWS_REGION": "'$AWS_REGION'"
        },
        "RuntimeEnvironmentSecrets": {
          "GOOGLE_APPLICATION_CREDENTIALS_JSON": "arn:aws:secretsmanager:'$AWS_REGION':'$AWS_ACCOUNT_ID':secret:gcp-service-account-json",
          "OTEL_EXPORTER_OTLP_ENDPOINT": "arn:aws:secretsmanager:'$AWS_REGION':'$AWS_ACCOUNT_ID':secret:portal26-endpoint",
          "OTEL_EXPORTER_OTLP_HEADERS": "arn:aws:secretsmanager:'$AWS_REGION':'$AWS_ACCOUNT_ID':secret:portal26-auth-header",
          "PORTAL26_TENANT_ID": "arn:aws:secretsmanager:'$AWS_REGION':'$AWS_ACCOUNT_ID':secret:portal26-tenant-id",
          "PORTAL26_USER_ID": "arn:aws:secretsmanager:'$AWS_REGION':'$AWS_ACCOUNT_ID':secret:portal26-user-id"
        },
        "Port": "8080"
      }
    },
    "AutoDeploymentsEnabled": true,
    "AuthenticationConfiguration": {
      "AccessRoleArn": "'$ACCESS_ROLE_ARN'"
    }
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB",
    "InstanceRoleArn": "'$INSTANCE_ROLE_ARN'"
  }' \
  --auto-scaling-configuration-arn "arn:aws:apprunner:$AWS_REGION:aws:autoscalingconfiguration/HighAvailability/1/00000000000000000000000000000001" \
  --region $AWS_REGION \
  2>/dev/null || {
    echo "  Service already exists, updating..."
    SERVICE_ARN=$(aws apprunner list-services --region $AWS_REGION --query "ServiceSummaryList[?ServiceName=='$APP_RUNNER_SERVICE_NAME'].ServiceArn" --output text)

    aws apprunner update-service \
      --service-arn $SERVICE_ARN \
      --source-configuration '{
        "ImageRepository": {
          "ImageIdentifier": "'$AWS_ACCOUNT_ID'.dkr.ecr.'$AWS_REGION'.amazonaws.com/'$ECR_REPO_NAME':latest",
          "ImageRepositoryType": "ECR",
          "ImageConfiguration": {
            "RuntimeEnvironmentVariables": {
              "GCP_PROJECT_ID": "agentic-ai-integration-490716",
              "PUBSUB_SUBSCRIPTION": "all-customers-logs-sub",
              "SMALL_LOG_THRESHOLD": "102400",
              "LARGE_LOG_THRESHOLD": "1048576"
            }
          }
        }
      }' \
      --region $AWS_REGION
  }

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Service Details:"
echo "  Service: $APP_RUNNER_SERVICE_NAME"
echo "  Region: $AWS_REGION"
echo "  Image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest"
echo ""
echo "Next Steps:"
echo "1. Wait 2-3 minutes for service to start"
echo ""
echo "2. Check service status:"
echo "   aws apprunner list-services --region $AWS_REGION"
echo ""
echo "3. View logs:"
echo "   aws logs tail /aws/apprunner/$APP_RUNNER_SERVICE_NAME --follow --region $AWS_REGION"
echo ""
echo "4. Check Portal26 for logs"
echo ""
echo "To update configuration:"
echo "  aws apprunner update-service --service-arn SERVICE_ARN ..."
echo ""
echo "To delete service:"
echo "  aws apprunner delete-service --service-arn SERVICE_ARN --region $AWS_REGION"
echo ""
echo "=========================================="

# Cleanup temp files
rm -f instance-trust-policy.json instance-role-policy.json access-trust-policy.json
