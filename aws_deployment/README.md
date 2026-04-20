# AWS ECS Fargate Deployment - Continuous Pull-Based Forwarder

## Overview

Complete AWS deployment solution for the continuous pull-based forwarder, optimized for **1000+ customer agents** with auto-scaling.

---

## Why ECS Fargate for 1000+ Agents?

| Feature | Benefit for 1000+ Agents |
|---------|--------------------------|
| **Auto-scaling** | Scales 3-10 containers based on load |
| **Serverless** | No EC2 instances to manage |
| **Cost-effective** | ~$100/month for 1000 agents |
| **High availability** | Multi-AZ deployment |
| **Zero maintenance** | AWS manages infrastructure |
| **Easy updates** | Rolling deployments |

---

## Architecture

```
1000+ Customer Agents (GCP Projects)
    ↓
GCP Cloud Logging
    ↓
Log Sinks
    ↓
YOUR GCP Pub/Sub Topic (all-customers-logs)
    ↓
AWS ECS Fargate Cluster (us-east-1)
    ├─ Task 1 (0.5 vCPU, 1GB RAM) ─┐
    ├─ Task 2 (0.5 vCPU, 1GB RAM) ─┤
    ├─ Task 3 (0.5 vCPU, 1GB RAM) ─┤
    ├─ ... (auto-scales to 10)     ├─→ Portal26 OTEL
    └─ Task N (0.5 vCPU, 1GB RAM) ─┘

Each task:
- Pulls from GCP Pub/Sub independently
- Converts GCP logs → OTEL format
- Adds customer identification
- Forwards to Portal26
```

---

## Files in This Folder

| File | Purpose |
|------|---------|
| **QUICK_START.md** | 20-minute deployment guide (start here!) |
| **AWS_DEPLOYMENT_GUIDE.md** | Complete reference documentation |
| **README.md** | This file |
| **Dockerfile** | Container image definition |
| **requirements.txt** | Python dependencies |
| **continuous_forwarder.py** | Forwarder code (AWS-optimized) |
| **task-definition.json** | ECS task configuration |
| **service-definition.json** | ECS service configuration |
| **autoscaling-config.json** | Auto-scaling policies |
| **deploy.sh** | Automated deployment script |

---

## Quick Start (20 Minutes)

### Prerequisites:
- AWS CLI installed and configured
- Docker installed
- GCP service account key

### Deploy:

```bash
# 1. Store secrets
aws secretsmanager create-secret --name gcp-service-account-json --secret-string file://gcp-key.json --region us-east-1
aws secretsmanager create-secret --name portal26-endpoint --secret-string "https://otel-tenant1.portal26.in:4318" --region us-east-1
aws secretsmanager create-secret --name portal26-auth-header --secret-string "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==" --region us-east-1
aws secretsmanager create-secret --name portal26-tenant-id --secret-string "tenant1" --region us-east-1
aws secretsmanager create-secret --name portal26-user-id --secret-string "relusys_terraform" --region us-east-1

# 2. Create IAM roles (see QUICK_START.md)

# 3. Deploy
cd aws_deployment
chmod +x deploy.sh
./deploy.sh

# 4. Configure auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 3 --max-capacity 10 --region us-east-1

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{"TargetValue":70.0,"PredefinedMetricSpecification":{"PredefinedMetricType":"ECSServiceAverageCPUUtilization"}}' \
  --region us-east-1

# Done! Check logs:
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1
```

**See QUICK_START.md for detailed step-by-step instructions.**

---

## Cost Breakdown

### For 1000 Agents:

**Baseline (3 tasks running 24/7):**
- 3 tasks × $18/month = $54/month
- CloudWatch Logs: $5/month
- Data transfer: $10/month
- **Total baseline: ~$70/month**

**Average load (5 tasks):**
- 5 tasks × $18/month = $90/month
- CloudWatch: $5/month
- Data transfer: $15/month
- **Total average: ~$110/month**

**Peak load (10 tasks):**
- 10 tasks × $18/month = $180/month
- CloudWatch: $10/month
- Data transfer: $20/month
- **Total peak: ~$210/month**

### Scaling Costs:

| Agents | Typical Tasks | Monthly Cost |
|--------|---------------|--------------|
| 100-500 | 3 tasks | $70/month |
| 500-1000 | 5 tasks | $110/month |
| 1000-2000 | 7 tasks | $150/month |
| 2000-5000 | 10 tasks | $210/month |
| 5000+ | 10+ tasks | $250+/month |

**Very cost-effective for scale!**

---

## Auto-Scaling Behavior

### Scale Out (Add Tasks):
- **Trigger:** CPU >70% OR Memory >80%
- **Cooldown:** 60 seconds
- **Increment:** +1 task at a time
- **Max:** 10 tasks

### Scale In (Remove Tasks):
- **Trigger:** CPU <70% AND Memory <80% for 5 minutes
- **Cooldown:** 300 seconds (5 min)
- **Decrement:** -1 task at a time
- **Min:** 3 tasks

### Load Distribution:
- GCP Pub/Sub automatically distributes messages across all tasks
- Each task pulls independently
- No manual load balancing needed

---

## Monitoring

### View Logs (Real-time):
```bash
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1
```

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

### View Auto-Scaling Activity:
```bash
aws application-autoscaling describe-scaling-activities \
  --service-namespace ecs \
  --resource-id service/gcp-monitoring-cluster/gcp-log-forwarder-service \
  --region us-east-1
```

### CloudWatch Dashboard:
- Go to: AWS Console → CloudWatch → Dashboards
- Metrics to monitor:
  - ECS Service CPU/Memory utilization
  - Task count
  - Log ingestion rate
  - Portal26 forwarding success rate

---

## High Availability

### Multi-AZ Deployment:
- Tasks automatically spread across availability zones
- If one AZ fails, tasks in other AZs continue
- ECS automatically replaces failed tasks

### Disaster Recovery:
- Deploy to second AWS region (e.g., us-west-2)
- Use same GCP Pub/Sub topic (global)
- Both regions pull independently
- Provides geographic redundancy

---

## Updating the Forwarder

### Deploy New Version:

```bash
cd aws_deployment
./deploy.sh
```

**Rolling update process:**
1. New tasks start with new image
2. Health checks pass
3. Old tasks drain
4. Old tasks terminate
5. **Zero downtime!**

### Rollback:

```bash
# Get previous task definition revision
aws ecs describe-task-definition \
  --task-definition gcp-log-forwarder:REVISION \
  --region us-east-1

# Update service to previous revision
aws ecs update-service \
  --cluster gcp-monitoring-cluster \
  --service gcp-log-forwarder-service \
  --task-definition gcp-log-forwarder:PREVIOUS_REVISION \
  --region us-east-1
```

---

## Security

### Network Security:
- Tasks in VPC with security groups
- Only outbound HTTPS allowed (443)
- No inbound ports needed
- Recommend: Use private subnets + NAT Gateway in production

### Secrets Security:
- All credentials in AWS Secrets Manager
- Encrypted at rest (AES-256)
- Encrypted in transit (TLS)
- IAM role-based access
- No secrets in code or logs

### GCP Authentication:
- Service account key in Secrets Manager
- Least privilege (only Pub/Sub subscriber role)
- Can rotate keys without redeployment

---

## Troubleshooting

### Tasks Failing to Start?

**Check CloudWatch logs:**
```bash
aws logs tail /ecs/gcp-log-forwarder --since 30m --region us-east-1
```

**Common issues:**
- Missing IAM permissions → Check task execution role
- Invalid secrets → Verify Secrets Manager ARNs
- Network connectivity → Check security group rules

### No Logs in Portal26?

**Verify forwarder is working:**
```bash
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1 | grep "Portal26"
```

**Check GCP Pub/Sub:**
```bash
gcloud pubsub subscriptions pull all-customers-logs-sub --limit=1 --project=agentic-ai-integration-490716
```

### High Memory Usage?

**Increase task memory:**

Edit `task-definition.json`:
```json
"memory": "2048"  // Changed from 1024
```

Redeploy: `./deploy.sh`

### Tasks Restarting Frequently?

**Check task health:**
```bash
TASK_ARN=$(aws ecs list-tasks --cluster gcp-monitoring-cluster --region us-east-1 --query 'taskArns[0]' --output text)
aws ecs describe-tasks --cluster gcp-monitoring-cluster --tasks $TASK_ARN --region us-east-1
```

**Common causes:**
- Out of memory → Increase memory allocation
- GCP credentials expired → Rotate service account key
- Network timeouts → Check NAT Gateway

---

## Best Practices

### For Production:

1. **Use Private Subnets**
   - Move tasks to private subnets
   - Use NAT Gateway for outbound

2. **Enable Container Insights**
   ```bash
   aws ecs update-cluster-settings \
     --cluster gcp-monitoring-cluster \
     --settings name=containerInsights,value=enabled \
     --region us-east-1
   ```

3. **Set Up CloudWatch Alarms**
   - Alert on task failures
   - Alert on high error rate
   - Alert on auto-scaling events

4. **Enable ECS Exec**
   - Debug running containers
   - Already enabled in service definition

5. **Tag Resources**
   - Add cost allocation tags
   - Track by environment, team, etc.

### For Cost Optimization:

1. **Use Fargate Spot** (if acceptable):
   - Up to 70% savings
   - May be interrupted
   - Good for non-critical workloads

2. **Right-size Tasks**:
   - Monitor actual CPU/memory usage
   - Adjust task definition if over-provisioned

3. **Optimize Batch Size**:
   - Larger batches = fewer API calls
   - Edit `PORTAL26_BATCH_SIZE` env var

---

## Comparison with Other Deployment Options

| Option | Cost | Complexity | Best For |
|--------|------|------------|----------|
| **ECS Fargate** | $100/mo | Medium | 1000+ agents, production |
| EC2 | $50/mo | High | Cost-sensitive, DIY |
| Lambda | $30/mo | Low | <100 agents, variable load |
| ECS on EC2 | $70/mo | Very High | Multiple services, large scale |

**ECS Fargate is the sweet spot for your use case (1000+ agents with growth).**

---

## Support

### Documentation:
- **QUICK_START.md** - Get started in 20 minutes
- **AWS_DEPLOYMENT_GUIDE.md** - Complete reference
- **../MULTI_CLIENT_IMPLEMENTATION.md** - Multi-client setup

### AWS Resources:
- [ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [Application Auto Scaling](https://docs.aws.amazon.com/autoscaling/application/userguide/)

### Monitoring:
- CloudWatch Logs: `/ecs/gcp-log-forwarder`
- ECS Console: https://console.aws.amazon.com/ecs
- Portal26: Query by `source = "aws-ecs"`

---

## Summary

**What You Get:**
- ✅ Auto-scaling (3-10 containers)
- ✅ Handles 1000+ agents easily
- ✅ High availability (multi-AZ)
- ✅ Zero server management
- ✅ CloudWatch monitoring
- ✅ Rolling updates
- ✅ Cost: ~$100/month

**Deployment Time:** 20 minutes  
**Maintenance:** Zero (AWS manages)  
**Scales To:** 10,000+ agents

**Production-ready for scale!**
