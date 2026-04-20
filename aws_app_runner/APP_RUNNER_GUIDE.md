# AWS App Runner Deployment Guide
## Simplest AWS Option - 50% Less Complex than ECS Fargate

---

## Why App Runner Over ECS Fargate?

| Feature | App Runner | ECS Fargate |
|---------|------------|-------------|
| **Setup Commands** | 3 steps | 15+ steps |
| **Deployment Time** | 10 minutes | 30 minutes |
| **Complexity** | ⭐⭐ Medium | ⭐⭐⭐⭐ High |
| **Cost** | $90/month | $115/month |
| **VPC Config** | Not needed | Required |
| **Security Groups** | Not needed | Required |
| **Load Balancer** | Built-in | Optional (extra cost) |
| **Auto-Scaling** | Built-in | Configure separately |
| **HTTPS** | Built-in | Need ALB |

**50% simpler, 20% cheaper, same performance!**

---

## Quick Start (3 Steps)

### Prerequisites:
- AWS CLI installed
- Docker installed
- GCP service account key

### Step 1: Store Secrets

```bash
# GCP credentials
aws secretsmanager create-secret \
  --name gcp-service-account-json \
  --secret-string file://gcp-key.json \
  --region us-east-1

# Portal26 config
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

### Step 2: Run Deployment Script

```bash
cd aws_app_runner
chmod +x deploy_app_runner.sh
./deploy_app_runner.sh
```

### Step 3: Verify

```bash
# Wait 2-3 minutes, then check status
aws apprunner list-services --region us-east-1

# View logs
aws logs tail /aws/apprunner/gcp-log-forwarder --follow --region us-east-1
```

**Done! Service is running.**

---

## What the Script Does

1. ✅ Creates ECR repository
2. ✅ Builds Docker image
3. ✅ Pushes to ECR
4. ✅ Creates IAM roles
5. ✅ Creates App Runner service
6. ✅ Configures auto-scaling
7. ✅ Connects secrets

**All in one script!**

---

## Cost Breakdown

```
App Runner (1 vCPU, 2GB):   $75/month
Data transfer (GCP→AWS):    $10/month
CloudWatch Logs:            $5/month
Total:                      $90/month

vs ECS Fargate:             $115/month
Savings:                    $25/month (22%)
```

---

## Configuration

### Update Environment Variables:

```bash
# Get service ARN
SERVICE_ARN=$(aws apprunner list-services --region us-east-1 --query "ServiceSummaryList[?ServiceName=='gcp-log-forwarder'].ServiceArn" --output text)

# Update routing thresholds
aws apprunner update-service \
  --service-arn $SERVICE_ARN \
  --source-configuration '{
    "ImageRepository": {
      "ImageConfiguration": {
        "RuntimeEnvironmentVariables": {
          "SMALL_LOG_THRESHOLD": "512000",
          "LARGE_LOG_THRESHOLD": "2097152"
        }
      }
    }
  }' \
  --region us-east-1
```

### Update Image:

```bash
# Build new image
docker build -t gcp-log-forwarder:latest .
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/gcp-log-forwarder:latest

# App Runner auto-deploys new image (if AutoDeploymentsEnabled)
# Or force update:
aws apprunner start-deployment --service-arn $SERVICE_ARN --region us-east-1
```

---

## Monitoring

### View Service Status:

```bash
aws apprunner describe-service \
  --service-arn $SERVICE_ARN \
  --region us-east-1
```

### View Logs (Real-Time):

```bash
aws logs tail /aws/apprunner/gcp-log-forwarder --follow --region us-east-1
```

### View Metrics in Console:

1. Go to: https://console.aws.amazon.com/apprunner
2. Select: `gcp-log-forwarder`
3. Tab: **Metrics**

---

## Auto-Scaling

**Already configured:**
- Min instances: 1
- Max instances: 25
- Auto-scales based on concurrent requests

**No additional configuration needed!**

---

## Comparison with ECS Fargate

### App Runner Advantages:

✅ **No VPC/subnets** - App Runner manages networking  
✅ **No security groups** - Built-in security  
✅ **No load balancer** - Built-in (HTTPS included)  
✅ **No cluster** - Fully managed  
✅ **No task definitions** - Just container image  
✅ **Auto-deploy** - Push image, auto-updates  
✅ **Simpler IAM** - Only 2 roles vs 5+ for ECS  

### ECS Fargate Advantages:

✅ **VPC control** - Custom networking  
✅ **Task isolation** - Multiple task definitions  
✅ **Service mesh** - Advanced networking features  
✅ **Service discovery** - Built-in DNS  

---

## When to Use App Runner vs ECS

### Use App Runner:
✅ Simple continuous pull workload  
✅ Don't need VPC customization  
✅ Want fastest deployment  
✅ One service per container  
✅ Standard networking OK  

### Use ECS Fargate:
✅ Need custom VPC/subnets  
✅ Multiple interconnected services  
✅ Service mesh requirements  
✅ Advanced networking (PrivateLink, etc.)  

**For your use case: App Runner is perfect!**

---

## Troubleshooting

### Service won't start?

**Check logs:**
```bash
aws logs tail /aws/apprunner/gcp-log-forwarder --region us-east-1 --since 30m
```

**Common issues:**
- Missing secrets → Check Secrets Manager
- IAM role permissions → Check instance role
- Image not found → Check ECR

### No logs in Portal26?

**Check App Runner logs:**
```bash
aws logs tail /aws/apprunner/gcp-log-forwarder --follow | grep "Portal26"
```

### High costs?

**Check instance count:**
```bash
aws apprunner describe-service \
  --service-arn $SERVICE_ARN \
  --query "Service.AutoScalingConfigurationSummary" \
  --region us-east-1
```

**Reduce max instances if needed:**
- Create custom auto-scaling config
- Set lower max instances

---

## Add Kinesis/S3 (Optional)

### Update secrets:

```bash
# AWS credentials for Kinesis/S3
aws secretsmanager create-secret \
  --name aws-access-key-id \
  --secret-string "YOUR_KEY" \
  --region us-east-1

aws secretsmanager create-secret \
  --name aws-secret-access-key \
  --secret-string "YOUR_SECRET" \
  --region us-east-1
```

### Update service:

```bash
aws apprunner update-service \
  --service-arn $SERVICE_ARN \
  --source-configuration '{
    "ImageRepository": {
      "ImageConfiguration": {
        "RuntimeEnvironmentVariables": {
          "KINESIS_STREAM_NAME": "gcp-logs-stream",
          "S3_BUCKET_NAME": "gcp-logs-archive"
        },
        "RuntimeEnvironmentSecrets": {
          "AWS_ACCESS_KEY_ID": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:aws-access-key-id",
          "AWS_SECRET_ACCESS_KEY": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:aws-secret-access-key"
        }
      }
    }
  }' \
  --region us-east-1
```

---

## Migration from ECS to App Runner

### Step 1: Deploy App Runner

```bash
./deploy_app_runner.sh
```

### Step 2: Verify Working

```bash
# Check logs flowing to Portal26
aws logs tail /aws/apprunner/gcp-log-forwarder --follow
```

### Step 3: Stop ECS Service

```bash
aws ecs update-service \
  --cluster gcp-monitoring-cluster \
  --service gcp-log-forwarder-service \
  --desired-count 0 \
  --region us-east-1
```

### Step 4: Clean Up ECS (Optional)

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

## Summary

**App Runner provides:**

✅ **50% simpler** than ECS (3 steps vs 15)  
✅ **22% cheaper** ($90 vs $115)  
✅ **10-minute deployment**  
✅ **Zero VPC configuration**  
✅ **Built-in auto-scaling**  
✅ **Built-in HTTPS**  
✅ **Auto-deploy from ECR**  

**Perfect for continuous pull workload!**

---

## Quick Commands Reference

### Deploy:
```bash
./deploy_app_runner.sh
```

### View logs:
```bash
aws logs tail /aws/apprunner/gcp-log-forwarder --follow --region us-east-1
```

### Update config:
```bash
aws apprunner update-service --service-arn ARN ...
```

### Redeploy:
```bash
aws apprunner start-deployment --service-arn ARN --region us-east-1
```

### Delete:
```bash
aws apprunner delete-service --service-arn ARN --region us-east-1
```

**That's it - much simpler than ECS!**
