# Quick Start - Deploy to AWS ECS Fargate

Deploy continuous pull-based forwarder for 1000+ agents in under 20 minutes.

---

## Prerequisites (5 minutes)

### 1. Install AWS CLI & Docker

```bash
# Install AWS CLI
# Download from: https://aws.amazon.com/cli/

# Install Docker
# Download from: https://www.docker.com/products/docker-desktop/

# Configure AWS CLI
aws configure
# Enter: AWS Access Key, Secret Key, Region (us-east-1), Output format (json)
```

### 2. Get GCP Service Account Key

```bash
# Create service account
gcloud iam service-accounts create gcp-forwarder-aws \
  --display-name="GCP Forwarder for AWS" \
  --project=agentic-ai-integration-490716

# Grant Pub/Sub permission
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:gcp-forwarder-aws@agentic-ai-integration-490716.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"

# Download key
gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=gcp-forwarder-aws@agentic-ai-integration-490716.iam.gserviceaccount.com

# Save this file - you'll need it in Step 2
```

---

## Step 1: Store Secrets (2 minutes)

```bash
cd aws_deployment

# Store GCP credentials
aws secretsmanager create-secret \
  --name gcp-service-account-json \
  --secret-string file://gcp-key.json \
  --region us-east-1

# Store Portal26 config
aws secretsmanager create-secret \
  --name portal26-endpoint \
  --secret-string "https://otel-tenant1.portal26.in:4318" \
  --region us-east-1

aws secretsmanager create-secret \
  --name portal26-auth-header \
  --secret-string "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  --region us-east-1

aws secretsmanager create-secret \
  --name portal26-tenant-id \
  --secret-string "tenant1" \
  --region us-east-1

aws secretsmanager create-secret \
  --name portal26-user-id \
  --secret-string "relusys_terraform" \
  --region us-east-1
```

---

## Step 2: Create IAM Roles (3 minutes)

**Task Execution Role:**

```bash
# Create trust policy
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://trust-policy.json

# Attach AWS managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Grant Secrets Manager access
cat > secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": ["arn:aws:secretsmanager:us-east-1:*:secret:gcp-*", "arn:aws:secretsmanager:us-east-1:*:secret:portal26-*"]
  }]
}
EOF

aws iam put-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-name SecretsAccess \
  --policy-document file://secrets-policy.json
```

**Task Role:**

```bash
aws iam create-role \
  --role-name gcp-forwarder-task-role \
  --assume-role-policy-document file://trust-policy.json

# Grant CloudWatch Logs access
cat > logs-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
    "Resource": "arn:aws:logs:us-east-1:*:log-group:/ecs/gcp-log-forwarder:*"
  }]
}
EOF

aws iam put-role-policy \
  --role-name gcp-forwarder-task-role \
  --policy-name LogsAccess \
  --policy-document file://logs-policy.json
```

---

## Step 3: Deploy (10 minutes)

```bash
chmod +x deploy.sh
./deploy.sh
```

**The script will:**
- Create ECR repository
- Build Docker image
- Push to ECR
- Create ECS cluster
- Deploy service with 3 tasks
- Configure networking

**Wait for:** "DEPLOYMENT COMPLETE!"

---

## Step 4: Configure Auto-Scaling (2 minutes)

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 3 \
  --max-capacity 10 \
  --region us-east-1

# CPU-based scaling
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }' \
  --region us-east-1

# Memory-based scaling
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name memory-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 80.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageMemoryUtilization"
    }
  }' \
  --region us-east-1
```

---

## Step 5: Verify (2 minutes)

**Check service status:**

```bash
aws ecs describe-services \
  --cluster gcp-monitoring-cluster \
  --services gcp-log-forwarder-service \
  --region us-east-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

Expected output:
```json
{
  "Status": "ACTIVE",
  "Running": 3,
  "Desired": 3
}
```

**Check logs:**

```bash
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1
```

Look for:
```
Starting continuous pull from: projects/agentic-ai-integration-490716/subscriptions/all-customers-logs-sub
Sent 10 logs to Portal26 (total: 10)
```

**Check Portal26:**

Query: `service.name = "gcp-vertex-monitor" AND source = "aws-ecs"`

---

## Done!

**You now have:**
- ✅ 3 ECS Fargate tasks running
- ✅ Auto-scaling (3-10 tasks)
- ✅ CloudWatch logging
- ✅ High availability (multi-AZ)
- ✅ Zero server management

**Cost:** ~$60/month baseline (3 tasks)

**Scales to:** 1000+ agents easily

---

## Common Commands

### View real-time logs:
```bash
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1
```

### Check running tasks:
```bash
aws ecs list-tasks --cluster gcp-monitoring-cluster --region us-east-1
```

### Scale manually:
```bash
aws ecs update-service \
  --cluster gcp-monitoring-cluster \
  --service gcp-log-forwarder-service \
  --desired-count 5 \
  --region us-east-1
```

### Update forwarder code:
```bash
./deploy.sh  # Rebuilds and redeploys
```

### Stop service:
```bash
aws ecs update-service \
  --cluster gcp-monitoring-cluster \
  --service gcp-log-forwarder-service \
  --desired-count 0 \
  --region us-east-1
```

### Delete everything:
```bash
# Delete service
aws ecs delete-service \
  --cluster gcp-monitoring-cluster \
  --service gcp-log-forwarder-service \
  --force \
  --region us-east-1

# Delete cluster
aws ecs delete-cluster \
  --cluster gcp-monitoring-cluster \
  --region us-east-1
```

---

## Troubleshooting

### Tasks not starting?

**Check logs:**
```bash
aws logs tail /ecs/gcp-log-forwarder --since 10m --region us-east-1
```

**Check task details:**
```bash
TASK_ARN=$(aws ecs list-tasks --cluster gcp-monitoring-cluster --region us-east-1 --query 'taskArns[0]' --output text)
aws ecs describe-tasks --cluster gcp-monitoring-cluster --tasks $TASK_ARN --region us-east-1
```

### No logs in Portal26?

**Verify forwarder is pulling:**
```bash
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1 | grep "Processed"
```

**Check GCP Pub/Sub has messages:**
```bash
gcloud pubsub subscriptions pull all-customers-logs-sub --limit=1 --project=agentic-ai-integration-490716
```

### High costs?

**Check running tasks:**
```bash
aws ecs describe-services \
  --cluster gcp-monitoring-cluster \
  --services gcp-log-forwarder-service \
  --region us-east-1 \
  --query 'services[0].runningCount'
```

**Reduce max capacity if needed:**
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 5 \
  --region us-east-1
```

---

## Next Steps

1. ✅ **Monitor** - Check CloudWatch logs daily for first week
2. ✅ **Optimize** - Adjust auto-scaling thresholds based on actual load
3. ✅ **Alert** - Set up CloudWatch alarms for task failures
4. ✅ **Backup** - Deploy to second region for disaster recovery

**Production-ready for 1000+ agents!**
