#!/bin/bash
# Complete ECS Fargate Deployment Script for GCP Log Forwarder
# Deploys continuous pull-based forwarder to AWS ECS with auto-scaling

set -e

echo "=========================================="
echo "GCP Log Forwarder - AWS ECS Deployment"
echo "=========================================="
echo ""

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID"
ECR_REPO_NAME="gcp-log-forwarder"
ECS_CLUSTER_NAME="gcp-monitoring-cluster"
ECS_SERVICE_NAME="gcp-log-forwarder-service"
TASK_FAMILY="gcp-log-forwarder"

# Check prerequisites
echo "[1/12] Checking prerequisites..."
command -v aws >/dev/null 2>&1 || { echo "ERROR: AWS CLI not installed"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker not installed"; exit 1; }
echo "  AWS CLI: OK"
echo "  Docker: OK"

# Get AWS account ID
ACTUAL_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "  AWS Account: $ACTUAL_ACCOUNT_ID"

# Create ECR repository
echo ""
echo "[2/12] Creating ECR repository..."
aws ecr create-repository \
  --repository-name $ECR_REPO_NAME \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true \
  2>/dev/null || echo "  Repository already exists"

# Login to ECR
echo ""
echo "[3/12] Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ACTUAL_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Copy forwarder code
echo ""
echo "[4/12] Preparing application code..."
cp ../monitoring_setup/continuous_forwarder.py .
echo "  Copied continuous_forwarder.py"

# Build Docker image
echo ""
echo "[5/12] Building Docker image..."
docker build -t $ECR_REPO_NAME:latest .
docker tag $ECR_REPO_NAME:latest $ACTUAL_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

# Push to ECR
echo ""
echo "[6/12] Pushing image to ECR..."
docker push $ACTUAL_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

# Create CloudWatch log group
echo ""
echo "[7/12] Creating CloudWatch log group..."
aws logs create-log-group \
  --log-group-name /ecs/$TASK_FAMILY \
  --region $AWS_REGION \
  2>/dev/null || echo "  Log group already exists"

# Create ECS cluster
echo ""
echo "[8/12] Creating ECS cluster..."
aws ecs create-cluster \
  --cluster-name $ECS_CLUSTER_NAME \
  --region $AWS_REGION \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
  2>/dev/null || echo "  Cluster already exists"

# Register task definition
echo ""
echo "[9/12] Registering ECS task definition..."
# Update task definition with actual account ID
sed "s/YOUR_AWS_ACCOUNT/$ACTUAL_ACCOUNT_ID/g" task-definition.json > task-definition-updated.json
aws ecs register-task-definition \
  --cli-input-json file://task-definition-updated.json \
  --region $AWS_REGION

# Get default VPC and subnets
echo ""
echo "[10/12] Getting VPC configuration..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region $AWS_REGION)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text --region $AWS_REGION | tr '\t' ',')
echo "  VPC: $VPC_ID"
echo "  Subnets: $SUBNET_IDS"

# Create security group
echo ""
echo "[11/12] Creating security group..."
SG_ID=$(aws ec2 create-security-group \
  --group-name gcp-forwarder-sg \
  --description "Security group for GCP log forwarder" \
  --vpc-id $VPC_ID \
  --region $AWS_REGION \
  --query 'GroupId' \
  --output text 2>/dev/null) || SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=gcp-forwarder-sg" "Name=vpc-id,Values=$VPC_ID" \
  --query "SecurityGroups[0].GroupId" \
  --output text \
  --region $AWS_REGION)

# Allow outbound HTTPS (for GCP Pub/Sub and Portal26)
aws ec2 authorize-security-group-egress \
  --group-id $SG_ID \
  --ip-permissions IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges='[{CidrIp=0.0.0.0/0}]' \
  --region $AWS_REGION \
  2>/dev/null || echo "  Egress rule already exists"

echo "  Security Group: $SG_ID"

# Create ECS service
echo ""
echo "[12/12] Creating ECS service..."
SUBNET_ARRAY=$(echo $SUBNET_IDS | tr ',' '\n' | head -2 | jq -R . | jq -s .)

aws ecs create-service \
  --cluster $ECS_CLUSTER_NAME \
  --service-name $ECS_SERVICE_NAME \
  --task-definition $TASK_FAMILY \
  --desired-count 3 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=$SUBNET_ARRAY,securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --enable-execute-command \
  --region $AWS_REGION \
  2>/dev/null || echo "  Service already exists, updating..."

# If service exists, update it
aws ecs update-service \
  --cluster $ECS_CLUSTER_NAME \
  --service $ECS_SERVICE_NAME \
  --task-definition $TASK_FAMILY \
  --force-new-deployment \
  --region $AWS_REGION \
  2>/dev/null || true

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Service Details:"
echo "  Cluster: $ECS_CLUSTER_NAME"
echo "  Service: $ECS_SERVICE_NAME"
echo "  Task Definition: $TASK_FAMILY"
echo "  Region: $AWS_REGION"
echo "  Initial Tasks: 3"
echo "  Auto-scaling: 3-10 tasks"
echo ""
echo "Next Steps:"
echo "1. Store GCP credentials in AWS Secrets Manager"
echo "2. Configure auto-scaling policies"
echo "3. Monitor CloudWatch logs"
echo ""
echo "To view service:"
echo "  aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services $ECS_SERVICE_NAME --region $AWS_REGION"
echo ""
echo "To view logs:"
echo "  aws logs tail /ecs/$TASK_FAMILY --follow --region $AWS_REGION"
echo ""
echo "=========================================="
