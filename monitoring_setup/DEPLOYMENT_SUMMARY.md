# GCP Pub/Sub → Portal26 Monitoring - Deployment Summary

## What You Have

Complete monitoring solution to forward GCP Vertex AI Reasoning Engine logs to Portal26 OTEL endpoint.

### Files Overview

| File | Purpose |
|------|---------|
| **monitor_pubsub_to_portal26.py** | ⭐ Main forwarder - GCP → Portal26 |
| monitor_pubsub_continuous.py | Local log archival (24/7) |
| monitor_pubsub_scheduled.py | Batch collection (hourly) |
| monitor_pubsub_alerts.py | Real-time alerting |
| monitor_pubsub.py | Original test script |
| **Dockerfile** | Container image for AWS ECS/Docker |
| **requirements.txt** | Python dependencies |
| **.env.example** | Configuration template |
| **AWS_DEPLOYMENT.md** | AWS deployment guide (EC2/ECS/Lambda) |
| **PORTAL26_QUICKSTART.md** | 5-minute setup guide |
| **README.md** | Overview of all approaches |
| monitor-pubsub.service | Linux systemd service |
| scheduled-monitoring.xml | Windows Task Scheduler |

## Quick Start (Local)

```bash
# 1. Install
cd monitoring_setup
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
nano .env  # Add your Portal26 endpoint

# 3. Run
python monitor_pubsub_to_portal26.py
```

## Production Deployment (AWS)

### Option 1: EC2 (Recommended)
- **Setup time:** 10 minutes
- **Cost:** ~$10/month
- **Best for:** Reliable 24/7 forwarding

```bash
# Launch t3.micro instance
# Install dependencies
# Configure systemd service
# See AWS_DEPLOYMENT.md for details
```

### Option 2: ECS Fargate
- **Setup time:** 20 minutes
- **Cost:** ~$15-20/month
- **Best for:** Managed, scalable infrastructure

```bash
# Build Docker image
docker build -t pubsub-monitor .

# Push to ECR
# Deploy ECS service
# See AWS_DEPLOYMENT.md for details
```

### Option 3: Lambda
- **Setup time:** 15 minutes
- **Cost:** ~$1-3/month
- **Best for:** Scheduled batch collection only
- **Limitation:** 15-minute timeout (not for continuous)

## Configuration

### Required Environment Variables

```bash
# GCP
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json

# Portal26
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.portal26.io
OTEL_SERVICE_NAME=gcp-vertex-monitor
```

### Optional Tuning

```bash
# Batching (default: 10 logs per 5 seconds)
PORTAL26_BATCH_SIZE=10
PORTAL26_BATCH_TIMEOUT=5

# Increase for high volume
PORTAL26_BATCH_SIZE=50
PORTAL26_BATCH_TIMEOUT=10
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ GCP Vertex AI Reasoning Engine                              │
│ - Executes queries                                           │
│ - Generates logs                                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ GCP Cloud Logging                                            │
│ - Collects all logs                                          │
│ - Log Sink filters reasoning engine logs                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ GCP Pub/Sub Topic: vertex-telemetry-topic                   │
│ - Buffers log messages                                       │
│ - Subscription: vertex-telemetry-subscription                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Monitor Script (AWS or Local)                                │
│ - Pulls messages from Pub/Sub                                │
│ - Converts to OTEL format                                    │
│ - Batches for efficiency                                     │
│ - Preserves trace context                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP POST (OTEL JSON)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Portal26 OTEL Endpoint                                       │
│ - Receives logs via OTLP HTTP                                │
│ - Stores in Portal26 platform                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Portal26 Dashboard                                           │
│ - Query logs                                                 │
│ - View traces                                                │
│ - Set up alerts                                              │
│ - Analyze trends                                             │
└─────────────────────────────────────────────────────────────┘
```

## Features

✅ **OTEL Compliant** - Standard observability format
✅ **Trace Preservation** - Maintains GCP trace IDs
✅ **Batched Transmission** - Efficient network usage
✅ **Automatic Retry** - Handles transient failures
✅ **Resource Attribution** - Preserves reasoning_engine_id
✅ **Severity Mapping** - GCP → OTEL severity levels
✅ **Real-time** - Continuous streaming
✅ **Hybrid Cloud** - GCP logs, AWS deployment, Portal26 storage

## Monitoring

### Check if running
```bash
# Local
ps aux | grep monitor_pubsub

# EC2
sudo systemctl status portal26-forwarder

# Docker
docker ps | grep pubsub-monitor
```

### View logs
```bash
# Local - stdout

# EC2
sudo journalctl -u portal26-forwarder -f

# Docker
docker logs -f pubsub-monitor
```

### Verify in Portal26
```
service.name = "gcp-vertex-monitor"
```

## Troubleshooting

### No logs in Portal26
1. Check if script is running
2. Verify Portal26 endpoint URL
3. Check for errors in logs
4. Test endpoint connectivity

### High error rate
1. Check Portal26 service status
2. Verify network connectivity
3. Review authentication (if required)
4. Adjust batch size/timeout

### Logs delayed
1. Increase batch size for throughput
2. Check Pub/Sub subscription lag
3. Verify AWS/local network speed

## Cost Estimate (Monthly)

| Component | Cost |
|-----------|------|
| GCP Pub/Sub | $5-10 |
| AWS EC2 t3.micro | $7-10 |
| AWS ECS Fargate | $15-20 |
| AWS Lambda | $1-3 |
| Portal26 | Per your plan |
| **Total (EC2)** | **~$15-20/month** |

## Security

- GCP credentials stored in AWS Secrets Manager
- Minimal IAM permissions (Pub/Sub subscriber only)
- HTTPS encryption for Portal26 transmission
- No credentials in code/logs
- Service account key rotation (90 days)

## Next Steps

1. **Test locally** - 5 minutes
   ```bash
   python monitor_pubsub_to_portal26.py
   ```

2. **Deploy to AWS** - Follow AWS_DEPLOYMENT.md

3. **Verify in Portal26** - Check dashboard for logs

4. **Set up monitoring** - CloudWatch alarms for failures

5. **Create dashboards** - Portal26 queries and visualizations

6. **Document for team** - Share Portal26 queries

## Support Resources

- **PORTAL26_QUICKSTART.md** - Quick setup guide
- **AWS_DEPLOYMENT.md** - Production deployment
- **README.md** - All monitoring options
- **LOG_SINK_INTEGRATION_TEST.md** - GCP setup

## Example Queries (Portal26)

### All logs
```
service.name = "gcp-vertex-monitor"
```

### Errors only
```
service.name = "gcp-vertex-monitor" AND severityText = "ERROR"
```

### Specific engine
```
resource.reasoning_engine_id = "your-engine-id"
```

### With trace
```
service.name = "gcp-vertex-monitor" AND traceId != ""
```

## Success Criteria

✅ Script running continuously
✅ Logs appearing in Portal26 within 10 seconds
✅ Trace IDs preserved (when available)
✅ No errors in monitor logs
✅ Pub/Sub subscription not backing up

---

**Ready to deploy!** Start with local test, then proceed to AWS deployment.
