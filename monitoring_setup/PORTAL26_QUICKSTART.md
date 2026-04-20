# Portal26 Integration Quick Start

Forward GCP Vertex AI Reasoning Engine logs to Portal26 for unified observability.

## Architecture

```
GCP Vertex AI Reasoning Engine
    ↓ (logs)
GCP Cloud Logging
    ↓ (log sink)
GCP Pub/Sub (vertex-telemetry-topic)
    ↓ (pull subscription)
Monitor Script (AWS/Local)
    ↓ (OTEL HTTP)
Portal26 OTEL Endpoint
    ↓
Portal26 Dashboard
```

## Prerequisites

✅ GCP Log Sink configured (see `LOG_SINK_INTEGRATION_TEST.md`)
✅ Pub/Sub subscription created
✅ Portal26 account with OTEL endpoint URL
✅ GCP Service Account with Pub/Sub Subscriber role

## Local Setup (5 minutes)

### 1. Install dependencies
```bash
cd monitoring_setup
pip install -r requirements.txt
```

### 2. Configure environment
```bash
# Copy example
cp .env.example .env

# Edit .env with your values
nano .env
```

Required settings:
```bash
# GCP
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json

# Portal26
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.portal26.io
OTEL_SERVICE_NAME=gcp-vertex-monitor
```

### 3. Test connection
```bash
# Quick test (pulls for 30 seconds)
python monitor_pubsub.py
```

### 4. Start Portal26 forwarder
```bash
python monitor_pubsub_to_portal26.py
```

### 5. Verify in Portal26
- Open Portal26 dashboard
- Navigate to **Logs** section
- Filter: `service.name = "gcp-vertex-monitor"`
- You should see logs with:
  - `resource.reasoning_engine_id`
  - Trace IDs (if available)
  - Full log context

## AWS Deployment

See `AWS_DEPLOYMENT.md` for:
- EC2 instance deployment
- ECS Fargate deployment
- Lambda scheduled deployment

**Recommended:** EC2 with systemd service for 24/7 forwarding

## Configuration Options

### Batching
```bash
# Control how logs are sent to Portal26
PORTAL26_BATCH_SIZE=10      # Logs per batch (default: 10)
PORTAL26_BATCH_TIMEOUT=5    # Seconds before flush (default: 5)
```

**Tuning:**
- High-volume: Increase batch size (50-100) to reduce HTTP requests
- Low-latency: Decrease batch size (1-5) for real-time forwarding
- Balance: Default (10/5s) works for most cases

### Service Name
```bash
# Customize service identifier in Portal26
OTEL_SERVICE_NAME=my-vertex-monitor
```

Use different names for:
- Multiple environments (dev/staging/prod)
- Different GCP projects
- Different monitoring purposes

## Monitoring the Monitor

### Check if it's running
```bash
# Local
ps aux | grep monitor_pubsub_to_portal26

# EC2/systemd
sudo systemctl status portal26-forwarder

# Docker
docker ps | grep pubsub-monitor
```

### View logs
```bash
# Local
# Logs print to stdout

# EC2/systemd
sudo journalctl -u portal26-forwarder -f

# Docker
docker logs -f pubsub-monitor

# ECS
aws logs tail /ecs/pubsub-monitor --follow
```

### Check stats
Look for these log lines:
```
[PORTAL26] ✓ Sent 10 logs (total: 150)
--- Stats: 200 received | 150 forwarded | 0 errors ---
```

### Verify in Portal26
Query to see your logs:
```
service.name = "gcp-vertex-monitor" AND resource.reasoning_engine_id != ""
```

## Troubleshooting

### No logs appearing in Portal26

**Check 1: Are logs being pulled from Pub/Sub?**
```bash
# Should see "Queued" messages
python monitor_pubsub_to_portal26.py
```

**Check 2: Is Portal26 endpoint correct?**
```bash
# Test endpoint
curl -X POST ${OTEL_EXPORTER_OTLP_ENDPOINT}/v1/logs \
  -H "Content-Type: application/json" \
  -d '{"resourceLogs":[]}'

# Should return 200 OK or 202 Accepted
```

**Check 3: Any errors in logs?**
```bash
# Look for Portal26 errors
sudo journalctl -u portal26-forwarder | grep ERROR
```

### High error rate

**Portal26 timeout:**
```bash
# Increase request timeout (default: 10s)
# Edit monitor_pubsub_to_portal26.py line ~121:
response = requests.post(url, json=payload, headers=headers, timeout=30)
```

**Rate limiting:**
```bash
# Decrease batch size to reduce payload
PORTAL26_BATCH_SIZE=5
```

### Missing trace context

GCP logs only include trace IDs if:
1. Request has `X-Cloud-Trace-Context` header
2. Application uses Cloud Trace instrumentation
3. Logs are correlated with traces

This is automatically forwarded when available.

### Logs delayed

**Increase batch size for throughput:**
```bash
PORTAL26_BATCH_SIZE=50
PORTAL26_BATCH_TIMEOUT=10
```

**Check Pub/Sub subscription lag:**
```bash
gcloud pubsub subscriptions describe vertex-telemetry-subscription \
  --project=agentic-ai-integration-490716 \
  --format="table(numUndeliveredMessages)"
```

## Cost Optimization

### GCP Costs
- **Pub/Sub:** $0.40 per million messages
- **Log Sink:** Free (routing only)
- **Typical:** ~$5-10/month for moderate traffic

### AWS Costs (if deployed there)
- **EC2 t3.micro:** $7-10/month
- **ECS Fargate:** $15-20/month
- **Lambda:** $1-3/month (scheduled only)
- **Data transfer:** Minimal (logs compressed)

### Portal26 Costs
Check your Portal26 plan for:
- Log ingestion limits
- Retention period
- Query limits

## Security

### GCP Service Account
Minimum permissions required:
```bash
roles/pubsub.subscriber  # Read from subscription only
```

### AWS IAM (if deployed on AWS)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:gcp-pubsub-credentials-*"
    }
  ]
}
```

### Portal26 Authentication
If your endpoint requires auth:
```bash
# Add header to requests (edit monitor_pubsub_to_portal26.py)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ.get('PORTAL26_API_KEY')}"
}
```

## Next Steps

1. ✅ Deploy to production (AWS recommended)
2. ✅ Set up CloudWatch alarms for errors
3. ✅ Create Portal26 dashboards for your logs
4. ✅ Configure alerts in Portal26
5. ✅ Document endpoint for your team

## Support

- **GCP Issues:** Check `LOG_SINK_INTEGRATION_TEST.md`
- **AWS Deployment:** See `AWS_DEPLOYMENT.md`
- **Portal26 API:** Contact Portal26 support
- **Monitor Script:** Check logs and error messages

## Example Portal26 Queries

View all Reasoning Engine logs:
```
service.name = "gcp-vertex-monitor"
```

Filter by severity:
```
service.name = "gcp-vertex-monitor" AND severityText = "ERROR"
```

Find specific engine:
```
resource.reasoning_engine_id = "1234567890"
```

Trace specific request:
```
traceId = "abc123..."
```
