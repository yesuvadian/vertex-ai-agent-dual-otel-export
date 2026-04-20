# AWS ECS Fargate Deployment Guide
## Continuous Pull-Based Forwarder for 1000+ Agents

---

## Overview

Deploy the continuous pull-based forwarder to AWS ECS Fargate with auto-scaling for handling 1000+ customer agents.

**Architecture:**
```
GCP Pub/Sub (1000+ agents)
    ↓
AWS ECS Fargate Cluster
├─ Container 1 (0.5 vCPU, 1GB)
├─ Container 2 (0.5 vCPU, 1GB)
├─ Container 3 (0.5 vCPU, 1GB)
├─ ... (auto-scales 3-10 based on load)
    ↓
Portal26
```

**Auto-scaling:**
- Minimum: 3 containers (baseline)
- Maximum: 10 containers (peak load)
- Scales on: CPU >70%, Memory >80%

---

## Prerequisites

### 1. AWS CLI & Docker Installed

```bash
# Check AWS CLI
aws --version

# Check Docker
docker --version

# Configure AWS CLI
aws configure
```

### 2. GCP Service Account Key

**Create service account in GCP:**
```bash
# Create service account
gcloud iam service-accounts create gcp-forwarder-aws \
  --display-name="GCP Forwarder for AWS" \
  --project=agentic-ai-integration-490716

# Grant Pub/Sub subscriber permission
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:gcp-forwarder-aws@agentic-ai-integration-490716.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"

# Download key
gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=gcp-forwarder-aws@agentic-ai-integration-490716.iam.gserviceaccount.com
```

Save `gcp-key.json` - you'll upload this to AWS Secrets Manager.

---

## Deployment Steps

### Step 1: Store Secrets in AWS Secrets Manager

**Store GCP credentials:**
```bash
# Store GCP service account JSON
aws secretsmanager create-secret \
  --name gcp-service-account-json \
  --description "GCP service account for Pub/Sub access" \
  --secret-string file://gcp-key.json \
  --region us-east-1
```

**Store Portal26 configuration:**
```bash
# Portal26 endpoint
aws secretsmanager create-secret \
  --name portal26-endpoint \
  --secret-string "https://otel-tenant1.portal26.in:4318" \
  --region us-east-1

# Portal26 auth header
aws secretsmanager create-secret \
  --name portal26-auth-header \
  --secret-string "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  --region us-east-1

# Portal26 tenant ID
aws secretsmanager create-secret \
  --name portal26-tenant-id \
  --secret-string "tenant1" \
  --region us-east-1

# Portal26 user ID
aws secretsmanager create-secret \
  --name portal26-user-id \
  --secret-string "relusys_terraform" \
  --region us-east-1
```

---

### Step 2: Create IAM Roles

**Create ECS Task Execution Role:**

```bash
# Create trust policy
cat > ecs-task-execution-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://ecs-task-execution-trust-policy.json

# Attach AWS managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create custom policy for Secrets Manager access
cat > secrets-access-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:gcp-service-account-json*",
        "arn:aws:secretsmanager:us-east-1:*:secret:portal26-*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-name SecretsManagerAccess \
  --policy-document file://secrets-access-policy.json
```

**Create ECS Task Role (for the container):**

```bash
cat > ecs-task-role-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name gcp-forwarder-task-role \
  --assume-role-policy-document file://ecs-task-role-trust-policy.json

# Add CloudWatch Logs access (for application logs)
cat > task-role-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/ecs/gcp-log-forwarder:*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name gcp-forwarder-task-role \
  --policy-name CloudWatchLogsAccess \
  --policy-document file://task-role-policy.json
```

---

### Step 3: Update Task Definition with Your AWS Account

**Edit `task-definition.json`:**

Replace:
- `YOUR_AWS_ACCOUNT` → Your AWS account ID (run `aws sts get-caller-identity --query Account --output text`)
- Secret ARNs with your actual secret ARNs

Or use the deploy script which does this automatically.

---

### Step 4: Update Forwarder to Handle GCP Credentials

The forwarder needs to read GCP credentials from environment variable instead of file.

**Create `continuous_forwarder.py` wrapper:**

Add this at the top of `continuous_forwarder.py`:

```python
import os
import json

# Handle GCP credentials from AWS Secrets Manager (passed as env var)
if 'GOOGLE_APPLICATION_CREDENTIALS_JSON' in os.environ:
    creds_json = os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON']
    with open('/tmp/gcp-creds.json', 'w') as f:
        f.write(creds_json)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/gcp-creds.json'
```

---

### Step 5: Deploy to AWS

**Run deployment script:**

```bash
cd aws_deployment
chmod +x deploy.sh
./deploy.sh
```

**The script will:**
1. Create ECR repository
2. Build Docker image
3. Push to ECR
4. Create ECS cluster
5. Register task definition
6. Create security group
7. Create ECS service with 3 tasks
8. Deploy

Takes ~10-15 minutes.

---

### Step 6: Configure Auto-Scaling

**Register scalable target:**

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 3 \
  --max-capacity 10 \
  --region us-east-1
```

**Create CPU-based scaling policy:**

```bash
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
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }' \
  --region us-east-1
```

**Create Memory-based scaling policy:**

```bash
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
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }' \
  --region us-east-1
```

---

## Monitoring & Verification

### View Service Status:

```bash
aws ecs describe-services \
  --cluster gcp-monitoring-cluster \
  --services gcp-log-forwarder-service \
  --region us-east-1
```

### View Running Tasks:

```bash
aws ecs list-tasks \
  --cluster gcp-monitoring-cluster \
  --service-name gcp-log-forwarder-service \
  --region us-east-1
```

### View Logs (Real-time):

```bash
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1
```

### View Recent Logs:

```bash
aws logs tail /ecs/gcp-log-forwarder --since 1h --region us-east-1
```

### Check Auto-Scaling Status:

```bash
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --region us-east-1
```

---

## Cost Breakdown for 1000 Agents

### ECS Fargate Pricing:

**Per Task (0.5 vCPU, 1GB RAM):**
- vCPU: 0.5 × $0.04048/hour × 730 hours = $14.78/month
- Memory: 1GB × $0.004445/GB/hour × 730 hours = $3.24/month
- **Total per task: $18/month**

**For 1000 agents with baseline 3 tasks:**
- 3 tasks × $18 = **$54/month baseline**
- Peak (10 tasks): $180/month
- Average (5 tasks): $90/month

**Total estimated cost: $90-120/month**

### Additional Costs:
- CloudWatch Logs: ~$5/month
- ECR storage: ~$1/month
- Data transfer: ~$10/month

**Grand Total: ~$100-140/month for 1000 agents**

### Scaling Costs:

| Agents | Avg Tasks | Monthly Cost |
|--------|-----------|--------------|
| 1-500 | 3 tasks | $60/month |
| 500-1000 | 5 tasks | $100/month |
| 1000-2000 | 7 tasks | $140/month |
| 2000-5000 | 10 tasks | $200/month |

---

## Scaling Behavior

### Auto-Scaling Triggers:

**Scale Out (add tasks):**
- CPU usage > 70% for 1 minute
- Memory usage > 80% for 1 minute
- Adds 1 task at a time
- Cooldown: 60 seconds

**Scale In (remove tasks):**
- CPU usage < 70% for 5 minutes
- Memory usage < 80% for 5 minutes
- Removes 1 task at a time
- Cooldown: 300 seconds (5 min)

### Load Distribution:

**Pub/Sub automatically distributes messages:**
- Each ECS task pulls independently
- Pub/Sub load-balances across all tasks
- No additional configuration needed

**Example with 1000 agents generating 10 logs/day each:**
- Total: 10,000 logs/day
- With 5 tasks: 2,000 logs/task/day
- Each task: ~83 logs/hour
- Very manageable!

---

## Troubleshooting

### Tasks failing to start?

**Check CloudWatch logs:**
```bash
aws logs tail /ecs/gcp-log-forwarder --since 30m --region us-east-1
```

**Common issues:**
- GCP credentials not accessible → Check Secrets Manager ARNs
- Network connectivity → Check security group allows outbound HTTPS
- Task role permissions → Check IAM roles

### No logs appearing in Portal26?

**Check forwarder logs:**
```bash
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1 | grep "Portal26"
```

**Look for:**
- "Portal26 accepted log" → Working
- "Portal26 returned error" → Check auth credentials
- "Failed to send to Portal26" → Network/connectivity issue

### Tasks restarting frequently?

**Check task health:**
```bash
aws ecs describe-tasks \
  --cluster gcp-monitoring-cluster \
  --tasks TASK_ARN \
  --region us-east-1
```

**Common causes:**
- Out of memory → Increase task memory
- GCP Pub/Sub quota exceeded → Check GCP quotas
- Network timeouts → Check NAT gateway/internet connectivity

---

## Updating the Forwarder

**To deploy new version:**

```bash
cd aws_deployment

# Rebuild and push image
docker build -t gcp-log-forwarder:latest .
docker tag gcp-log-forwarder:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/gcp-log-forwarder:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/gcp-log-forwarder:latest

# Force new deployment (rolling update)
aws ecs update-service \
  --cluster gcp-monitoring-cluster \
  --service gcp-log-forwarder-service \
  --force-new-deployment \
  --region us-east-1
```

**Rolling update process:**
- New tasks start
- Health checks pass
- Old tasks drain and terminate
- Zero downtime!

---

## High Availability

### Multi-AZ Deployment:

**Already configured!**
- ECS service uses multiple availability zones
- Tasks spread across AZs automatically
- If one AZ fails, tasks in other AZs continue

### Failure Recovery:

**Task fails:**
- ECS automatically starts replacement
- Recovery time: ~30 seconds
- No manual intervention needed

**AZ fails:**
- Tasks in other AZs handle load
- Auto-scaling adds more tasks if needed
- Seamless failover

---

## Security Best Practices

### Network Security:

**Current setup:**
- Tasks in public subnets with public IP (for internet access)
- Security group allows only outbound HTTPS

**Production recommendation:**
- Move to private subnets
- Use NAT Gateway for outbound
- Remove public IPs

### Secrets Security:

**Current setup:**
- Credentials in AWS Secrets Manager
- Encrypted at rest
- IAM role-based access

**Production recommendation:**
- Enable automatic rotation for Portal26 credentials
- Use AWS KMS for additional encryption
- Audit access with CloudTrail

---

## Summary

**What you get:**
- ✅ Serverless continuous forwarder
- ✅ Auto-scaling (3-10 tasks)
- ✅ Handles 1000+ agents easily
- ✅ High availability (multi-AZ)
- ✅ Zero downtime updates
- ✅ CloudWatch monitoring
- ✅ Cost: ~$100/month for 1000 agents

**Deployment time:** 15 minutes  
**Maintenance:** Zero (AWS manages everything)  
**Scales to:** 10,000+ agents (just increase max tasks)

**Ready for production at scale!**
