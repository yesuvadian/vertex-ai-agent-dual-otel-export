# Deploying GCP Pub/Sub Monitoring on AWS

## Overview

This is a **hybrid cloud setup** - monitoring GCP Vertex AI logs from AWS infrastructure and forwarding to Portal26 OTEL endpoint for observability.

**Flow:** GCP Pub/Sub → AWS Monitor → Portal26 OTEL Endpoint

## Prerequisites

1. **GCP Service Account** with Pub/Sub permissions
2. **Service Account JSON key** 
3. **AWS Account** with EC2/ECS access
4. **Portal26 OTEL Endpoint** URL (e.g., `https://otel.portal26.io`)
5. **Portal26 API Key** (if authentication required)

## Authentication Setup

### 1. Create GCP Service Account

```bash
# Create service account
gcloud iam service-accounts create pubsub-monitor \
  --display-name="Pub/Sub Monitor for AWS" \
  --project=agentic-ai-integration-490716

# Grant Pub/Sub permissions
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:pubsub-monitor@agentic-ai-integration-490716.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"

# Create and download key
gcloud iam service-accounts keys create gcp-credentials.json \
  --iam-account=pubsub-monitor@agentic-ai-integration-490716.iam.gserviceaccount.com
```

### 2. Store Credentials in AWS

**Option A: AWS Secrets Manager** (recommended)
```bash
# Upload to Secrets Manager
aws secretsmanager create-secret \
  --name gcp-pubsub-credentials \
  --secret-string file://gcp-credentials.json \
  --region us-east-1

# Then delete local file
rm gcp-credentials.json
```

**Option B: AWS Systems Manager Parameter Store**
```bash
aws ssm put-parameter \
  --name /monitoring/gcp-credentials \
  --type SecureString \
  --value file://gcp-credentials.json \
  --region us-east-1
```

### 3. Store Portal26 Configuration

```bash
# Store Portal26 endpoint
aws secretsmanager create-secret \
  --name portal26-otel-endpoint \
  --secret-string "https://otel.portal26.io" \
  --region us-east-1

# Store Portal26 API key (if required)
aws secretsmanager create-secret \
  --name portal26-api-key \
  --secret-string "your-api-key-here" \
  --region us-east-1
```

---

## Deployment Options

## Option 1: EC2 Instance (Portal26 Forwarder)

**Best for:** Long-running continuous monitoring with Portal26 integration

### Setup Steps

1. **Launch EC2 instance**
   - AMI: Ubuntu 22.04 or Amazon Linux 2023
   - Type: t3.micro (sufficient for monitoring)
   - Security Group: Allow outbound HTTPS (443) to GCP
   - IAM Role: With SecretsManager read permission

2. **Install dependencies**
```bash
# SSH into instance
ssh -i key.pem ec2-user@<instance-ip>

# Install Python and dependencies
sudo yum update -y
sudo yum install python3 python3-pip git -y
pip3 install google-cloud-pubsub python-dotenv

# Clone your code
git clone <your-repo>
cd ai_agent_projectgcp/monitoring_setup
```

3. **Configure credentials and Portal26**
```bash
# Fetch GCP credentials from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id gcp-pubsub-credentials \
  --query SecretString \
  --output text > /home/ec2-user/gcp-credentials.json

# Fetch Portal26 endpoint
PORTAL26_ENDPOINT=$(aws secretsmanager get-secret-value \
  --secret-id portal26-otel-endpoint \
  --query SecretString \
  --output text)

# Create .env file
cat > /home/ec2-user/ai_agent_projectgcp/monitoring_setup/.env << EOF
GOOGLE_APPLICATION_CREDENTIALS=/home/ec2-user/gcp-credentials.json
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription
OTEL_EXPORTER_OTLP_ENDPOINT=${PORTAL26_ENDPOINT}
OTEL_SERVICE_NAME=gcp-vertex-monitor
PORTAL26_BATCH_SIZE=10
PORTAL26_BATCH_TIMEOUT=5
EOF
```

4. **Create systemd service for Portal26 forwarder**
```bash
# Create service file
sudo tee /etc/systemd/system/portal26-forwarder.service > /dev/null << 'EOF'
[Unit]
Description=GCP Pub/Sub to Portal26 Forwarder
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/ai_agent_projectgcp/monitoring_setup
EnvironmentFile=/home/ec2-user/ai_agent_projectgcp/monitoring_setup/.env
ExecStart=/usr/bin/python3 monitor_pubsub_to_portal26.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable portal26-forwarder
sudo systemctl start portal26-forwarder
sudo systemctl status portal26-forwarder
```

5. **View logs and verify Portal26 forwarding**
```bash
# View service logs
sudo journalctl -u portal26-forwarder -f

# Check for successful forwarding
sudo journalctl -u portal26-forwarder | grep "Sent.*logs"

# Monitor stats
sudo journalctl -u portal26-forwarder | grep "Stats:"
```

6. **Verify in Portal26 dashboard**
   - Log into Portal26 UI
   - Navigate to Logs section
   - Filter by `service.name = "gcp-vertex-monitor"`
   - Verify logs from `reasoning_engine_id` are appearing

---

## Option 2: ECS Fargate (Container-based)

**Best for:** Scalable, managed infrastructure

### 1. Create Dockerfile

**File:** `monitoring_setup/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy monitoring scripts
COPY monitor_pubsub_continuous.py .
COPY monitor_pubsub_scheduled.py .
COPY monitor_pubsub_alerts.py .

# Create log directory
RUN mkdir -p /app/pubsub_logs

# Default to continuous monitoring
CMD ["python", "monitor_pubsub_continuous.py"]
```

### 2. Create requirements.txt
```
google-cloud-pubsub==2.18.4
python-dotenv==1.0.0
```

### 3. Build and push to ECR
```bash
# Create ECR repository
aws ecr create-repository --repository-name pubsub-monitor --region us-east-1

# Build image
docker build -t pubsub-monitor monitoring_setup/

# Tag and push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag pubsub-monitor:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/pubsub-monitor:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/pubsub-monitor:latest
```

### 4. Create ECS Task Definition

**File:** `monitoring_setup/ecs-task-definition.json`
```json
{
  "family": "pubsub-monitor",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::<account>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<account>:role/ecsTaskRole",
  "containerDefinitions": [{
    "name": "monitor",
    "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/pubsub-monitor:latest",
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/pubsub-monitor",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "secrets": [{
      "name": "GOOGLE_APPLICATION_CREDENTIALS_JSON",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:<account>:secret:gcp-pubsub-credentials"
    }],
    "environment": [
      {"name": "GCP_PROJECT_ID", "value": "agentic-ai-integration-490716"},
      {"name": "PUBSUB_SUBSCRIPTION", "value": "vertex-telemetry-subscription"}
    ]
  }]
}
```

### 5. Deploy ECS Service
```bash
# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/pubsub-monitor

# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster default \
  --service-name pubsub-monitor \
  --task-definition pubsub-monitor \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## Option 3: Lambda + EventBridge (Scheduled)

**Best for:** Scheduled periodic pulls (cost-effective)

**Note:** Lambda has 15-minute timeout, so this works for scheduled pulls only

### 1. Create Lambda deployment package

```bash
cd monitoring_setup
mkdir lambda-package
pip install google-cloud-pubsub -t lambda-package/
cp monitor_pubsub_scheduled.py lambda-package/lambda_function.py
cd lambda-package && zip -r ../lambda-function.zip . && cd ..
```

### 2. Create Lambda function

```bash
# Create IAM role for Lambda
aws iam create-role \
  --role-name lambda-pubsub-monitor \
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name lambda-pubsub-monitor \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name lambda-pubsub-monitor \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

# Create function
aws lambda create-function \
  --function-name pubsub-monitor \
  --runtime python3.11 \
  --role arn:aws:iam::<account>:role/lambda-pubsub-monitor \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-function.zip \
  --timeout 900 \
  --memory-size 512 \
  --environment Variables={GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-creds.json}
```

### 3. Schedule with EventBridge

```bash
# Create EventBridge rule (hourly)
aws events put-rule \
  --name pubsub-monitor-hourly \
  --schedule-expression "rate(1 hour)"

# Add Lambda as target
aws events put-targets \
  --rule pubsub-monitor-hourly \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:<account>:function:pubsub-monitor"

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
  --function-name pubsub-monitor \
  --statement-id EventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:<account>:rule/pubsub-monitor-hourly
```

---

## Cost Comparison

| Option | Monthly Cost (estimate) | Best For |
|--------|------------------------|----------|
| **EC2 t3.micro** | ~$7-10 | Continuous monitoring, full control |
| **ECS Fargate** | ~$15-20 | Managed, scalable, container-based |
| **Lambda (hourly)** | ~$1-3 | Scheduled pulls only, most cost-effective |

---

## Monitoring & Logs

### EC2/ECS Logs
```bash
# EC2 systemd logs
sudo journalctl -u monitor-pubsub -f

# ECS CloudWatch logs
aws logs tail /ecs/pubsub-monitor --follow
```

### Lambda Logs
```bash
aws logs tail /aws/lambda/pubsub-monitor --follow
```

### Store logs in S3
```python
# Add to monitoring scripts:
import boto3

s3 = boto3.client('s3')
s3.upload_file(
    log_file, 
    'my-monitoring-bucket', 
    f'pubsub-logs/{datetime.now().strftime("%Y/%m/%d")}/{filename}'
)
```

---

## Security Best Practices

1. **Never commit GCP credentials** to git
2. **Use AWS Secrets Manager** for credential storage
3. **Rotate service account keys** every 90 days
4. **Restrict IAM policies** to minimum required permissions
5. **Enable VPC endpoints** for AWS services (no internet routing)
6. **Use security groups** to restrict outbound traffic to GCP IPs only

---

## Troubleshooting

### Connection Issues
```bash
# Test GCP connectivity from AWS
curl -I https://pubsub.googleapis.com

# Test authentication
python3 -c "from google.cloud import pubsub_v1; print(pubsub_v1.SubscriberClient())"
```

### Permission Issues
```bash
# Verify GCP service account permissions
gcloud projects get-iam-policy agentic-ai-integration-490716 \
  --flatten="bindings[].members" \
  --filter="bindings.members:pubsub-monitor@*"
```

### Network Issues
- Ensure AWS security groups allow outbound HTTPS (443)
- Check VPC route tables have internet gateway route
- Verify GCP API is enabled: `gcloud services list --enabled`

---

## Next Steps

1. Choose deployment option based on your needs
2. Set up GCP service account and download credentials
3. Store credentials in AWS Secrets Manager
4. Deploy using one of the options above
5. Monitor logs to verify data collection
6. Set up CloudWatch alarms for failures
