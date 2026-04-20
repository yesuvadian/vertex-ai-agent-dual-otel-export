# Multi-Destination Forwarder Guide

## Overview

Intelligent log routing to **Portal26 OTEL**, **AWS Kinesis**, or **AWS S3** based on log size and volume.

---

## Routing Strategy

### By Log Size:

```
Log Size              Destination    Reason
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
< 100 KB              Portal26       Real-time analytics
100 KB - 1 MB         Kinesis        Streaming processing
> 1 MB                S3             Archival/batch processing
```

### By Volume:

```
Volume                Destination    Reason
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
< 100 logs/min        Portal26       Low volume, real-time
> 100 logs/min        Kinesis        High throughput needed
Burst traffic         Kinesis        Handle spikes
```

### Priority Order:

1. **Very large logs (>1MB)** → Always S3
2. **High volume (>100/min)** → Kinesis (if available)
3. **Medium logs (100KB-1MB)** → Kinesis (if available)
4. **Small logs (<100KB)** → Portal26
5. **Fallback** → Kinesis → S3 → Drop

---

## Architecture

```
1000+ Agents (GCP)
    ↓
GCP Pub/Sub
    ↓
Multi-Destination Forwarder (AWS ECS)
    ├─ Analyze log size
    ├─ Check current volume
    └─ Route intelligently
         ├──→ Portal26 OTEL (small, real-time)
         ├──→ Kinesis (medium, high-volume)
         └──→ S3 (large, archival)
```

---

## Use Cases

### Portal26 OTEL (Real-Time Analytics):
- **Small logs** - Quick queries, agent interactions
- **Low latency** - Immediate visibility
- **Interactive analysis** - Dashboard, alerts
- **Cost** - Optimized for real-time queries

### AWS Kinesis (Streaming Processing):
- **Medium logs** - Longer traces, complex payloads
- **High throughput** - 100+ logs/min
- **Stream processing** - Lambda, Kinesis Analytics
- **Scalability** - Auto-scaling consumers

### AWS S3 (Archival/Batch):
- **Large logs** - Full request/response bodies
- **Long-term storage** - Compliance, auditing
- **Batch analytics** - Athena, EMR, Redshift
- **Cost** - Lowest storage cost

---

## Configuration

### Environment Variables:

```bash
# GCP
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=all-customers-logs-sub

# Portal26 OTEL
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
PORTAL26_TENANT_ID=tenant1
PORTAL26_USER_ID=relusys_terraform

# AWS Kinesis
KINESIS_STREAM_NAME=gcp-logs-stream
AWS_REGION=us-east-1

# AWS S3
S3_BUCKET_NAME=gcp-logs-archive
S3_PREFIX=gcp-logs/
AWS_REGION=us-east-1

# Routing Thresholds
SMALL_LOG_THRESHOLD=102400      # 100KB
LARGE_LOG_THRESHOLD=1048576     # 1MB
HIGH_VOLUME_THRESHOLD=100       # logs/min

# Batching
PORTAL26_BATCH_SIZE=20
KINESIS_BATCH_SIZE=100
S3_BATCH_SIZE=500
PORTAL26_BATCH_TIMEOUT=5
```

---

## AWS Setup

### 1. Create Kinesis Stream

```bash
aws kinesis create-stream \
  --stream-name gcp-logs-stream \
  --shard-count 2 \
  --region us-east-1

# Enable enhanced monitoring
aws kinesis enable-enhanced-monitoring \
  --stream-name gcp-logs-stream \
  --shard-level-metrics IncomingBytes,IncomingRecords,OutgoingBytes,OutgoingRecords \
  --region us-east-1
```

**Shard sizing:**
- 1 shard = 1MB/sec write, 2MB/sec read
- For 1000 agents: Start with 2 shards
- Auto-scale with Kinesis Data Streams on-demand mode

**Cost:**
- $0.015 per shard hour = ~$22/month per shard
- 2 shards = ~$44/month

---

### 2. Create S3 Bucket

```bash
aws s3 mb s3://gcp-logs-archive --region us-east-1

# Enable versioning (optional)
aws s3api put-bucket-versioning \
  --bucket gcp-logs-archive \
  --versioning-configuration Status=Enabled

# Set lifecycle policy (move to Glacier after 90 days)
cat > lifecycle-policy.json <<EOF
{
  "Rules": [{
    "Id": "archive-old-logs",
    "Status": "Enabled",
    "Transitions": [{
      "Days": 90,
      "StorageClass": "GLACIER"
    }],
    "Expiration": {
      "Days": 365
    }
  }]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket gcp-logs-archive \
  --lifecycle-configuration file://lifecycle-policy.json
```

**Cost:**
- S3 Standard: $0.023 per GB/month
- Glacier: $0.004 per GB/month
- For 10GB/day: ~$7/month (Standard), ~$1/month (Glacier after 90 days)

---

### 3. Update IAM Roles

**Task Role needs Kinesis + S3 permissions:**

```bash
cat > kinesis-s3-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords"
      ],
      "Resource": "arn:aws:kinesis:us-east-1:*:stream/gcp-logs-stream"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::gcp-logs-archive/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name gcp-forwarder-task-role \
  --policy-name KinesisS3Access \
  --policy-document file://kinesis-s3-policy.json
```

---

### 4. Update Secrets Manager

```bash
aws secretsmanager create-secret \
  --name kinesis-stream-name \
  --secret-string "gcp-logs-stream" \
  --region us-east-1

aws secretsmanager create-secret \
  --name s3-bucket-name \
  --secret-string "gcp-logs-archive" \
  --region us-east-1
```

---

### 5. Update Task Definition

**Add to `task-definition.json`:**

```json
{
  "environment": [
    {
      "name": "KINESIS_STREAM_NAME",
      "value": "gcp-logs-stream"
    },
    {
      "name": "S3_BUCKET_NAME",
      "value": "gcp-logs-archive"
    },
    {
      "name": "S3_PREFIX",
      "value": "gcp-logs/"
    },
    {
      "name": "AWS_REGION",
      "value": "us-east-1"
    },
    {
      "name": "SMALL_LOG_THRESHOLD",
      "value": "102400"
    },
    {
      "name": "LARGE_LOG_THRESHOLD",
      "value": "1048576"
    },
    {
      "name": "HIGH_VOLUME_THRESHOLD",
      "value": "100"
    }
  ]
}
```

---

### 6. Update Dockerfile

**Change CMD in Dockerfile:**

```dockerfile
# Change from:
CMD ["python", "-u", "continuous_forwarder.py"]

# To:
CMD ["python", "-u", "multi_destination_forwarder.py"]
```

---

### 7. Deploy

```bash
cd aws_deployment
./deploy.sh
```

---

## Monitoring

### Check Routing Distribution:

**ECS Logs:**
```bash
aws logs tail /ecs/gcp-log-forwarder --follow --region us-east-1 | grep "HEALTH"
```

**Output:**
```
[HEALTH] Uptime: 1.5h
  Total Received:  1523
  Portal26:        845   (55%)
  Kinesis:         523   (34%)
  S3:              155   (11%)
  Errors:          0
  Current Volume:  78/min
```

---

### Portal26 Query:

```
# All logs from multi-dest forwarder
source = "aws-ecs-multi-dest" AND destination = "portal26"

# Count by customer
source = "aws-ecs-multi-dest" | stats count by customer.project_id
```

---

### Kinesis Monitoring:

```bash
# Check stream status
aws kinesis describe-stream \
  --stream-name gcp-logs-stream \
  --region us-east-1

# Get metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Kinesis \
  --metric-name IncomingRecords \
  --dimensions Name=StreamName,Value=gcp-logs-stream \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-1
```

---

### S3 Monitoring:

```bash
# List recent files
aws s3 ls s3://gcp-logs-archive/gcp-logs/ --recursive --human-readable | tail -20

# Check bucket size
aws s3 ls s3://gcp-logs-archive --recursive --summarize | grep "Total Size"

# Query with Athena (if configured)
# See: https://docs.aws.amazon.com/athena/latest/ug/querying.html
```

---

## Processing Downstream Data

### From Kinesis (Real-Time):

**Lambda Consumer Example:**

```python
import json
import boto3

def lambda_handler(event, context):
    for record in event['Records']:
        # Decode Kinesis record
        payload = json.loads(record['kinesis']['data'])
        
        log = payload['log']
        client_info = log.get('_client_info', {})
        
        # Process log
        print(f"Customer: {client_info['customer_project_id']}")
        print(f"Severity: {log.get('severity')}")
        
        # Send to alerts, metrics, etc.
```

**Deploy Lambda:**
```bash
aws lambda create-function \
  --function-name process-gcp-logs \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-kinesis-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip

# Add Kinesis trigger
aws lambda create-event-source-mapping \
  --function-name process-gcp-logs \
  --event-source-arn arn:aws:kinesis:us-east-1:ACCOUNT:stream/gcp-logs-stream \
  --starting-position LATEST
```

---

### From S3 (Batch Analytics):

**Athena Query Example:**

```sql
-- Create external table
CREATE EXTERNAL TABLE gcp_logs (
  timestamp string,
  source string,
  destination string,
  log struct<
    severity: string,
    textPayload: string,
    resource: struct<
      type: string,
      labels: map<string, string>
    >,
    _client_info: struct<
      customer_project_id: string,
      customer_id: string
    >
  >
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://gcp-logs-archive/gcp-logs/';

-- Query logs
SELECT 
  log._client_info.customer_project_id as customer,
  log.severity,
  COUNT(*) as count
FROM gcp_logs
WHERE year = '2026' AND month = '04'
GROUP BY log._client_info.customer_project_id, log.severity
ORDER BY count DESC;
```

---

## Cost Comparison

### Scenario: 1000 Agents, 10,000 logs/day

**Average log size: 50KB**

### All to Portal26:
- Portal26 ingestion: Variable (check pricing)
- **Pros:** Real-time analytics
- **Cons:** Higher cost for large logs

### Smart Routing (Recommended):
```
Portal26:  5,000 logs/day (small, <100KB)
Kinesis:   3,000 logs/day (medium, 100KB-1MB)
S3:        2,000 logs/day (large, >1MB)
```

**Monthly Costs:**
- Portal26: Optimized for small logs
- Kinesis: $44/month (2 shards)
- S3: $7/month (10GB/month storage)
- **Total infrastructure: ~$50/month + Portal26 costs**

### All to S3:
- S3: $7/month
- **Pros:** Cheapest storage
- **Cons:** No real-time analytics, requires batch processing

---

## Tuning Thresholds

### Adjust for Your Use Case:

**More to Portal26 (Real-Time Focus):**
```bash
SMALL_LOG_THRESHOLD=512000      # 500KB (increased)
LARGE_LOG_THRESHOLD=2097152     # 2MB (increased)
HIGH_VOLUME_THRESHOLD=200       # Tolerate more volume
```

**More to Kinesis (Streaming Focus):**
```bash
SMALL_LOG_THRESHOLD=51200       # 50KB (decreased)
LARGE_LOG_THRESHOLD=524288      # 500KB (decreased)
HIGH_VOLUME_THRESHOLD=50        # Lower threshold
```

**More to S3 (Cost Focus):**
```bash
SMALL_LOG_THRESHOLD=10240       # 10KB (very small)
LARGE_LOG_THRESHOLD=102400      # 100KB (decreased)
HIGH_VOLUME_THRESHOLD=20        # Aggressive
```

---

## Troubleshooting

### All logs going to S3?

**Check:**
- Log sizes might be larger than expected
- Volume might be high

**Fix:**
- Increase `LARGE_LOG_THRESHOLD`
- Increase `HIGH_VOLUME_THRESHOLD`

### High Kinesis costs?

**Check:**
- Number of shards
- Data volume

**Fix:**
- Switch to on-demand mode (pay per GB)
- Reduce `KINESIS_BATCH_SIZE` for smaller batches
- Increase thresholds to send less to Kinesis

### Logs not appearing in Portal26?

**Check:**
- Portal26 endpoint accessible?
- Auth credentials correct?
- Logs might be routing to Kinesis/S3 instead

**Debug:**
```bash
aws logs tail /ecs/gcp-log-forwarder --follow | grep "portal26"
```

---

## Summary

**Multi-destination routing provides:**

✅ **Cost optimization** - Right destination for right log size  
✅ **Performance** - Real-time for small, batch for large  
✅ **Scalability** - Handle volume spikes gracefully  
✅ **Flexibility** - Configure per use case  
✅ **Future-proof** - Easy to add new destinations

**Best for:** 1000+ agents with varying log sizes and volumes

**Deploy time:** 30 minutes (with Kinesis + S3 setup)
