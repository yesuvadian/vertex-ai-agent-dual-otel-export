# Vertex AI Telemetry Worker

Cloud Run worker that processes Vertex AI telemetry logs and exports to Portal26.

## Architecture

```
Pub/Sub → Cloud Run Worker → Cloud Trace API → Transform → Portal26
```

## Components

- **main.py** - Flask application with Pub/Sub endpoint
- **trace_processor.py** - Core processing logic
- **trace_fetcher.py** - Cloud Trace API client
- **otel_transformer.py** - GCP to OTEL format conversion
- **portal26_exporter.py** - Export to Portal26 backend
- **dedup_cache.py** - Deduplication cache (Redis/memory)
- **config.py** - Configuration management

## Setup

### Prerequisites

- Python 3.11+
- GCP service account with `roles/cloudtrace.user` on client projects
- Portal26 credentials

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run locally:**
```bash
python main.py
```

4. **Test health endpoint:**
```bash
curl http://localhost:8080/health
```

### Docker Build

```bash
docker build -t telemetry-worker .
docker run -p 8080:8080 --env-file .env telemetry-worker
```

## Deployment

### Deploy to Cloud Run

```bash
# Set variables
PROJECT="portal26-telemetry-prod"
SERVICE="telemetry-worker"
REGION="us-central1"
SA_EMAIL="telemetry-worker@${PROJECT}.iam.gserviceaccount.com"

# Deploy
gcloud run deploy $SERVICE \
  --source . \
  --project=$PROJECT \
  --region=$REGION \
  --platform=managed \
  --service-account=$SA_EMAIL \
  --set-env-vars="PORTAL26_ENDPOINT=https://otel.portal26.ai/v1/traces" \
  --set-secrets="PORTAL26_USERNAME=portal26-user:latest,PORTAL26_PASSWORD=portal26-pass:latest" \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=100 \
  --concurrency=80 \
  --cpu=2 \
  --memory=1Gi \
  --timeout=60s
```

### Create Pub/Sub Subscription

```bash
# Get Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE \
  --project=$PROJECT \
  --region=$REGION \
  --format='value(status.url)')

# Create push subscription
gcloud pubsub subscriptions create telemetry-processor \
  --topic=vertex-telemetry-topic \
  --project=$PROJECT \
  --push-endpoint="${CLOUD_RUN_URL}/process" \
  --ack-deadline=60 \
  --max-delivery-attempts=5
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORTAL26_ENDPOINT` | Yes | - | Portal26 OTEL endpoint |
| `PORTAL26_USERNAME` | Yes | - | Portal26 username |
| `PORTAL26_PASSWORD` | Yes | - | Portal26 password |
| `PORTAL26_TIMEOUT` | No | 30 | Request timeout (seconds) |
| `GCP_PROJECT` | No | - | GCP project ID |
| `GCP_LOCATION` | No | us-central1 | GCP location |
| `REDIS_HOST` | No | - | Redis host (for dedup) |
| `REDIS_PORT` | No | 6379 | Redis port |
| `DEDUP_CACHE_TTL` | No | 3600 | Cache TTL (seconds) |
| `LOG_LEVEL` | No | INFO | Log level |
| `PORT` | No | 8080 | Server port |

### IAM Permissions

**Service Account needs:**
- `roles/cloudtrace.user` on each client project (to fetch traces)
- `roles/pubsub.subscriber` on Pub/Sub subscription (to receive messages)

## API Endpoints

### POST /process

Process Pub/Sub message (push endpoint)

**Request:**
```json
{
  "message": {
    "data": "<base64-encoded-log-entry>",
    "attributes": {...},
    "messageId": "12345"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "tenant_id": "tenant_abc",
  "trace_id": "a1b2c3d4..."
}
```

### GET /health

Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "telemetry-worker",
  "version": "1.0.0"
}
```

## Processing Flow

1. **Receive** - Pub/Sub push delivers log entry
2. **Extract** - Parse trace_id, tenant_id, project_id
3. **Dedup** - Check if already processed
4. **Fetch** - Get full trace from Cloud Trace API
5. **Transform** - Convert GCP format to OTEL
6. **Export** - Send to Portal26 with tenant_id
7. **Cache** - Mark as processed

## Dynamic Tenant Handling

- New tenants automatically picked up
- No restart needed
- Tenant ID extracted from log labels
- Each message processed independently

## Error Handling

- **Trace not found (404)** - Log warning, return 200 (ack message)
- **Permission denied (403)** - Log error, return 200 (ack message)
- **Export failure** - Log error, return 200 (ack message, no retry)
- **Unexpected error** - Log error, return 500 (retry message)

## Monitoring

### Key Metrics

- Request count by tenant
- Processing latency (P50, P95, P99)
- Error rate by error type
- Cloud Trace API calls
- Export success rate

### Logs

```bash
# View logs
gcloud run services logs read telemetry-worker \
  --project=$PROJECT \
  --region=$REGION \
  --limit=100

# Filter by tenant
gcloud run services logs read telemetry-worker \
  --project=$PROJECT \
  --region=$REGION \
  --limit=100 | grep "tenant_abc"
```

## Testing

### Test with Sample Message

```bash
# Create test log entry
cat > test_log.json <<EOF
{
  "insertId": "test123",
  "timestamp": "2026-04-03T10:00:00Z",
  "trace": "projects/client-project/traces/abc123def456",
  "labels": {
    "tenant_id": "test_tenant"
  },
  "resource": {
    "type": "aiplatform.googleapis.com/ReasoningEngine",
    "labels": {
      "project_id": "client-project",
      "reasoning_engine_id": "8081657304514035712",
      "location": "us-central1"
    }
  }
}
EOF

# Encode and send
DATA=$(cat test_log.json | base64)
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d "{\"message\":{\"data\":\"$DATA\",\"messageId\":\"test\"}}"
```

## Troubleshooting

### Worker not receiving messages

1. Check Pub/Sub subscription exists and is push-type
2. Verify Cloud Run URL in subscription endpoint
3. Check Cloud Run service is running
4. Verify `allow-unauthenticated` is set

### Permission denied errors

1. Check service account has `roles/cloudtrace.user` on client project
2. Verify service account is attached to Cloud Run service
3. Test with `gcloud auth` using service account key

### Export failures

1. Check Portal26 endpoint is correct
2. Verify Portal26 credentials
3. Test endpoint with curl
4. Check Portal26 backend logs

### High latency

1. Increase Cloud Run CPU/memory
2. Increase max-instances for auto-scaling
3. Enable Redis for faster dedup
4. Check Cloud Trace API quota

## Cost Optimization

- Use Redis for dedup (avoid duplicate API calls)
- Adjust Cloud Run min-instances (0 for dev, 1+ for prod)
- Right-size CPU/memory based on load
- Monitor Cloud Trace API usage

## Development

### Run tests

```bash
# Coming soon
pytest tests/
```

### Format code

```bash
black *.py
```

### Lint

```bash
pylint *.py
```

## License

Internal use only - Portal26
