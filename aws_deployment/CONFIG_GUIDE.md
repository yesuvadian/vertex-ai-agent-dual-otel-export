# Configuration Guide - Multi-Destination Forwarder

## Quick Configuration with .env File

### For Local Testing:

```bash
# Copy example to .env
cp .env.example .env

# Edit with your values
nano .env
```

### For AWS ECS Deployment:

Use AWS Secrets Manager or ECS Environment Variables.

---

## Configuration Options

### 1. Enable/Disable Destinations

**Enable Portal26:**
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <your-token>
```

**Disable Portal26:**
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=
# Leave empty or comment out
```

**Enable Kinesis:**
```bash
KINESIS_STREAM_NAME=gcp-logs-stream
AWS_REGION=us-east-1
```

**Disable Kinesis:**
```bash
KINESIS_STREAM_NAME=
```

**Enable S3:**
```bash
S3_BUCKET_NAME=gcp-logs-archive
S3_PREFIX=gcp-logs/
AWS_REGION=us-east-1
```

**Disable S3:**
```bash
S3_BUCKET_NAME=
```

---

## 2. Routing Strategies (Pre-configured)

### Strategy A: Real-Time Focus

**Use case:** Need immediate visibility, most logs are small

```bash
# .env
SMALL_LOG_THRESHOLD=512000        # 500 KB
LARGE_LOG_THRESHOLD=2097152       # 2 MB
HIGH_VOLUME_THRESHOLD=200         # Tolerate higher volume

# Enables Portal26 destinations
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
KINESIS_STREAM_NAME=gcp-logs-stream
S3_BUCKET_NAME=gcp-logs-archive
```

**Result:**
- 80% → Portal26 (real-time)
- 15% → Kinesis (medium)
- 5% → S3 (large)

---

### Strategy B: Streaming Focus

**Use case:** Need processing pipeline, handle variable volume

```bash
# .env
SMALL_LOG_THRESHOLD=51200         # 50 KB
LARGE_LOG_THRESHOLD=524288        # 500 KB
HIGH_VOLUME_THRESHOLD=50          # Lower threshold

OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
KINESIS_STREAM_NAME=gcp-logs-stream
S3_BUCKET_NAME=gcp-logs-archive
```

**Result:**
- 30% → Portal26 (very small)
- 60% → Kinesis (most logs)
- 10% → S3 (large)

---

### Strategy C: Cost Optimization

**Use case:** Minimize costs, batch analytics acceptable

```bash
# .env
SMALL_LOG_THRESHOLD=10240         # 10 KB
LARGE_LOG_THRESHOLD=102400        # 100 KB
HIGH_VOLUME_THRESHOLD=20          # Aggressive

OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
KINESIS_STREAM_NAME=
S3_BUCKET_NAME=gcp-logs-archive
```

**Result:**
- 10% → Portal26 (tiny logs)
- 0% → Kinesis (disabled)
- 90% → S3 (most logs)

---

### Strategy D: Portal26 Only

**Use case:** All logs to Portal26, no AWS destinations

```bash
# .env
SMALL_LOG_THRESHOLD=10485760      # 10 MB (very high)
LARGE_LOG_THRESHOLD=104857600     # 100 MB (very high)
HIGH_VOLUME_THRESHOLD=1000        # Very high

OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
KINESIS_STREAM_NAME=
S3_BUCKET_NAME=
```

**Result:**
- 100% → Portal26
- 0% → Kinesis
- 0% → S3

---

### Strategy E: AWS Only (No Portal26)

**Use case:** Use AWS tools for analytics (Athena, Kinesis Analytics)

```bash
# .env
SMALL_LOG_THRESHOLD=524288        # 500 KB
LARGE_LOG_THRESHOLD=5242880       # 5 MB
HIGH_VOLUME_THRESHOLD=50

OTEL_EXPORTER_OTLP_ENDPOINT=
KINESIS_STREAM_NAME=gcp-logs-stream
S3_BUCKET_NAME=gcp-logs-archive
```

**Result:**
- 0% → Portal26 (disabled)
- 70% → Kinesis
- 30% → S3

---

### Strategy F: S3 Archival Only

**Use case:** Long-term storage, compliance, batch processing

```bash
# .env
SMALL_LOG_THRESHOLD=0
LARGE_LOG_THRESHOLD=0
HIGH_VOLUME_THRESHOLD=0

OTEL_EXPORTER_OTLP_ENDPOINT=
KINESIS_STREAM_NAME=
S3_BUCKET_NAME=gcp-logs-archive
```

**Result:**
- 0% → Portal26
- 0% → Kinesis
- 100% → S3

---

## 3. Performance Tuning

### High Throughput (Lower Latency)

```bash
# Smaller batches, more frequent sends
PORTAL26_BATCH_SIZE=10
KINESIS_BATCH_SIZE=50
S3_BATCH_SIZE=100
PORTAL26_BATCH_TIMEOUT=2
```

**Trade-off:**
- ✅ Lower latency (2-3 seconds)
- ❌ More API calls
- ❌ Higher cost

---

### High Efficiency (Lower Cost)

```bash
# Larger batches, less frequent sends
PORTAL26_BATCH_SIZE=50
KINESIS_BATCH_SIZE=500
S3_BATCH_SIZE=1000
PORTAL26_BATCH_TIMEOUT=10
```

**Trade-off:**
- ✅ Fewer API calls
- ✅ Lower cost
- ❌ Higher latency (10-15 seconds)

---

### Balanced (Recommended)

```bash
# Default values - good balance
PORTAL26_BATCH_SIZE=20
KINESIS_BATCH_SIZE=100
S3_BATCH_SIZE=500
PORTAL26_BATCH_TIMEOUT=5
```

**Trade-off:**
- ✅ Good latency (5-7 seconds)
- ✅ Reasonable API usage
- ✅ Moderate cost

---

## 4. Testing Different Configurations

### Local Testing:

```bash
# Edit .env with your configuration
nano .env

# Run locally
cd monitoring_setup
python multi_destination_forwarder.py

# Watch routing decisions
# Look for lines like:
# "Processed 10 | P26: 5, Kinesis: 3, S3: 2 | Last: portal26 (small_log_45KB)"
```

---

### AWS ECS Testing:

**Update task definition with new env vars:**

```bash
# Edit task-definition.json
# Update environment variables section

# Redeploy
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json

# Force new deployment
aws ecs update-service \
  --cluster gcp-monitoring-cluster \
  --service gcp-log-forwarder-service \
  --force-new-deployment \
  --region us-east-1

# Watch logs
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1
```

---

### A/B Testing:

**Run two ECS services with different configs:**

```bash
# Service 1: Real-time focus
# Use task definition: gcp-log-forwarder-realtime

# Service 2: Cost focus
# Use task definition: gcp-log-forwarder-cost

# Compare in Portal26 and CloudWatch metrics
```

---

## 5. Monitoring Configuration Impact

### CloudWatch Metrics:

**Create custom metrics to track routing:**

```python
# In multi_destination_forwarder.py, add:
import boto3
cloudwatch = boto3.client('cloudwatch')

def publish_routing_metrics():
    cloudwatch.put_metric_data(
        Namespace='GCPLogForwarder',
        MetricData=[
            {
                'MetricName': 'Portal26Count',
                'Value': stats['portal26_sent'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'KinesisCount',
                'Value': stats['kinesis_sent'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'S3Count',
                'Value': stats['s3_sent'],
                'Unit': 'Count'
            }
        ]
    )
```

---

### Portal26 Dashboard:

Query to see distribution:
```
source = "aws-ecs-multi-dest" 
| stats count by destination
```

---

## 6. Dynamic Configuration (Future)

**For runtime configuration changes without restart:**

### Option A: AWS AppConfig

```python
import boto3
appconfig = boto3.client('appconfig')

# Fetch config every 60 seconds
def load_config_from_appconfig():
    config = appconfig.get_configuration(
        Application='gcp-forwarder',
        Environment='production',
        Configuration='routing-config'
    )
    # Update thresholds dynamically
```

### Option B: S3 Config File

```python
import boto3
import json

s3 = boto3.client('s3')

def load_config_from_s3():
    obj = s3.get_object(Bucket='configs', Key='forwarder-config.json')
    config = json.loads(obj['Body'].read())
    # Update thresholds
```

---

## 7. Common Configuration Scenarios

### Scenario: "Too many logs in S3"

**Problem:** Most logs going to S3, want more in Portal26

**Solution:**
```bash
# Increase thresholds
LARGE_LOG_THRESHOLD=5242880       # 5 MB (was 1 MB)
HIGH_VOLUME_THRESHOLD=200         # (was 100)
```

---

### Scenario: "Portal26 costs too high"

**Problem:** Too many logs in Portal26

**Solution:**
```bash
# Decrease small threshold
SMALL_LOG_THRESHOLD=51200         # 50 KB (was 100 KB)

# Or disable Portal26 completely
OTEL_EXPORTER_OTLP_ENDPOINT=
```

---

### Scenario: "Need all errors in Portal26"

**Problem:** Want all errors in real-time, regardless of size

**Solution:** Modify routing logic in code:
```python
def route_log(log_entry, log_size):
    # Priority 0: All errors to Portal26
    severity = log_entry.get('severity', 'INFO')
    if severity in ['ERROR', 'CRITICAL', 'ALERT', 'EMERGENCY']:
        return 'portal26', 'error_severity'
    
    # ... rest of routing logic
```

---

### Scenario: "Burst traffic handling"

**Problem:** Traffic spikes causing issues

**Solution:**
```bash
# Lower high volume threshold to route to Kinesis faster
HIGH_VOLUME_THRESHOLD=50          # (was 100)

# Increase Kinesis batch size
KINESIS_BATCH_SIZE=500            # (was 100)
```

---

## 8. Configuration Best Practices

### ✅ DO:
- Start with default configuration
- Monitor distribution for 1 week
- Adjust based on actual patterns
- Document your configuration choices
- Version control your .env file (without secrets)
- Test configuration changes in dev first

### ❌ DON'T:
- Change all thresholds at once
- Set thresholds too low (< 10KB)
- Disable all destinations
- Commit secrets to git
- Change production config without testing

---

## Summary

**Easy configuration management with .env:**

✅ Change routing strategy without code changes  
✅ Enable/disable destinations easily  
✅ Tune for cost vs latency  
✅ Test different configurations  
✅ Pre-configured strategies included  

**Just edit .env file and restart!**
