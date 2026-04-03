# Telemetry Worker - Implementation Status

**Date:** 2026-04-03  
**Status:** ✓ Complete - Ready for Testing

---

## Project Structure

```
telemetry_worker/
├── main.py                   # Flask app with Pub/Sub endpoint
├── trace_processor.py        # Core processing logic
├── trace_fetcher.py          # Cloud Trace API client
├── otel_transformer.py       # GCP → OTEL transformation
├── portal26_exporter.py      # Export to Portal26
├── dedup_cache.py           # Deduplication (Redis/memory)
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image
├── .env.example             # Environment template
├── .dockerignore            # Docker ignore rules
├── README.md                # Documentation
├── test_local.py            # Local testing script
├── deploy.sh                # Cloud Run deployment script
└── setup_pubsub.sh          # Pub/Sub setup script
```

---

## Implementation Details

### 1. Flask Application (main.py)

**Status:** ✓ Complete

**Endpoints:**
- `POST /process` - Pub/Sub push endpoint
- `GET /health` - Health check
- `GET /` - Service info

**Features:**
- Base64 decoding of Pub/Sub messages
- JSON parsing of log entries
- Error handling and retry logic
- Logging for debugging

---

### 2. Trace Processor (trace_processor.py)

**Status:** ✓ Complete

**Features:**
- Dynamic metadata extraction
- Tenant ID extraction from log labels
- Deduplication check
- Orchestrates fetch → transform → export flow
- Comprehensive error handling

**Key Method:**
```python
def process_log_entry(log_entry, attributes) -> dict:
    # Extract metadata (trace_id, tenant_id, project_id)
    # Check dedup cache
    # Fetch trace from Cloud Trace API
    # Transform to OTEL
    # Export to Portal26
    # Mark as processed
```

---

### 3. Trace Fetcher (trace_fetcher.py)

**Status:** ✓ Complete

**Features:**
- Cloud Trace API client
- Exponential backoff retry (2-5s delays)
- Cross-project trace fetching
- Error handling (404, 403, timeouts)

**Retry Configuration:**
- Initial delay: 2 seconds
- Max delay: 5 seconds
- Multiplier: 1.5x
- Total timeout: 30 seconds

---

### 4. OTEL Transformer (otel_transformer.py)

**Status:** ✓ Complete

**Features:**
- GCP TraceSpan → OTEL Span conversion
- Resource attributes (tenant_id, project_id, etc.)
- Span attributes from GCP labels
- Timestamp conversion (nanoseconds)
- Status code mapping

**Mapping:**
- trace_id: hex → bytes
- span_id: int → bytes (padded)
- timestamps: datetime → unix nano
- labels → attributes

---

### 5. Portal26 Exporter (portal26_exporter.py)

**Status:** ✓ Complete

**Features:**
- OTLP/HTTP protobuf export
- Basic authentication
- Tenant ID header (`X-Tenant-ID`)
- Batch export support
- Timeout handling (30s default)

**Request Format:**
```
POST /v1/traces
Content-Type: application/x-protobuf
Authorization: Basic <credentials>
X-Tenant-ID: <tenant_id>
```

---

### 6. Deduplication Cache (dedup_cache.py)

**Status:** ✓ Complete

**Features:**
- Redis support (distributed)
- In-memory fallback (single instance)
- TTL: 1 hour (configurable)
- Auto-cleanup for memory cache

**Usage:**
```python
cache.is_processed(trace_id)  # Check if processed
cache.mark_processed(trace_id)  # Mark as processed
```

---

### 7. Configuration (config.py)

**Status:** ✓ Complete

**Environment Variables:**
- PORTAL26_ENDPOINT (required)
- PORTAL26_USERNAME (required)
- PORTAL26_PASSWORD (required)
- REDIS_HOST (optional)
- DEDUP_CACHE_TTL (default: 3600)
- LOG_LEVEL (default: INFO)

---

### 8. Docker Support

**Status:** ✓ Complete

**Dockerfile features:**
- Python 3.11-slim base
- Non-root user
- Health check
- Gunicorn server
- Multi-worker support

**Build:**
```bash
docker build -t telemetry-worker .
```

---

### 9. Deployment Scripts

**Status:** ✓ Complete

**deploy.sh:**
- Deploy to Cloud Run
- Create service account
- Set environment variables
- Configure scaling

**setup_pubsub.sh:**
- Create Pub/Sub topic
- Create push subscription
- Grant IAM permissions
- Link to Cloud Run

---

### 10. Testing Tools

**Status:** ✓ Complete

**test_local.py:**
- Simulate Pub/Sub messages
- Test with real trace IDs
- Local development testing

**Usage:**
```bash
python test_local.py <project_id> <trace_id> <tenant_id>
```

---

## Key Features Implemented

### ✓ Dynamic Tenant Handling

- Tenant ID extracted from each log entry
- No restart needed for new tenants
- Stateless processing

### ✓ Deduplication

- Prevents duplicate trace fetching
- Reduces Cloud Trace API costs
- Redis or in-memory cache

### ✓ Retry Logic

- Exponential backoff
- Configurable delays
- Handles transient errors

### ✓ Error Handling

- Trace not found → log warning, continue
- Permission denied → log error, continue
- Export failure → log error, continue
- Unexpected error → return 500, retry

### ✓ Monitoring

- Structured logging
- Health check endpoint
- Request/response logging

### ✓ Scalability

- Auto-scaling (1-100 instances)
- Concurrent request handling
- Batch export support

---

## What's Not Implemented (Future Enhancements)

### Batching

**Current:** One trace per Pub/Sub message  
**Enhancement:** Accumulate traces, batch export  
**Benefit:** Better throughput, lower cost

**Implementation:**
```python
# Add buffering logic
batch = []
for trace in traces:
    batch.append(trace)
    if len(batch) >= 100 or time_elapsed > 5:
        exporter.export_batch(batch, tenant_id)
        batch = []
```

### Metrics Export

**Current:** Logs only  
**Enhancement:** Export metrics to Cloud Monitoring  
**Metrics:**
- Traces processed per tenant
- Processing latency
- Error rates
- Cache hit rate

### Rate Limiting

**Current:** No rate limiting  
**Enhancement:** Limit per-tenant processing rate  
**Benefit:** Prevent single tenant from overwhelming

### Dead Letter Queue

**Current:** Failed messages retried by Pub/Sub  
**Enhancement:** Move failed messages to DLQ  
**Benefit:** Manual inspection of failures

### Unit Tests

**Current:** Manual testing only  
**Enhancement:** pytest test suite  
**Coverage:**
- Metadata extraction
- Transformation logic
- Error handling
- Cache behavior

---

## Testing Checklist

### Local Testing

- [x] Health endpoint responds
- [ ] Process endpoint accepts messages
- [ ] Metadata extraction works
- [ ] Trace fetching works
- [ ] Transformation produces valid OTEL
- [ ] Export to Portal26 succeeds
- [ ] Deduplication prevents duplicates

### Integration Testing

- [ ] Deploy to Cloud Run
- [ ] Create Pub/Sub subscription
- [ ] Test with real Vertex AI agent
- [ ] Verify trace appears in Portal26
- [ ] Test with multiple tenants
- [ ] Verify tenant isolation
- [ ] Check error handling

### Load Testing

- [ ] High message volume (1000+ msg/min)
- [ ] Auto-scaling works
- [ ] No message loss
- [ ] Acceptable latency (< 10s P95)
- [ ] Dedup cache effective

---

## Deployment Steps

### 1. Prerequisites

```bash
# Set environment
export GCP_PROJECT="portal26-telemetry-prod"
export GCP_REGION="us-central1"
export PORTAL26_ENDPOINT="https://otel.portal26.ai/v1/traces"

# Create secrets
echo -n "your_username" | gcloud secrets create portal26-user --data-file=-
echo -n "your_password" | gcloud secrets create portal26-pass --data-file=-
```

### 2. Deploy Cloud Run

```bash
cd telemetry_worker
chmod +x deploy.sh
./deploy.sh
```

### 3. Set up Pub/Sub

```bash
chmod +x setup_pubsub.sh
./setup_pubsub.sh
```

### 4. Test Deployment

```bash
# Get Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe telemetry-worker \
  --region=$GCP_REGION \
  --format='value(status.url)')

# Test health
curl ${CLOUD_RUN_URL}/health

# Expected: {"status":"healthy","service":"telemetry-worker","version":"1.0.0"}
```

### 5. Grant IAM Permissions (Per Client)

```bash
# For each client project
CLIENT_PROJECT="client-project-123"
SA_EMAIL="telemetry-worker@${GCP_PROJECT}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $CLIENT_PROJECT \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudtrace.user"
```

### 6. Test with Real Client

```bash
# Use existing gcp_traces_agent as test client
cd ../gcp_traces_agent_client
python view_traces.py --limit 1  # Get a trace ID

# Test with that trace
cd ../telemetry_worker
python test_local.py \
  agentic-ai-integration-490716 \
  <trace_id> \
  test_tenant \
  ${CLOUD_RUN_URL}/process
```

---

## Next Steps

### Immediate (Ready Now)

1. **Set Portal26 credentials**
   - Update .env.example with real endpoint/credentials
   - Create secrets in Secret Manager

2. **Deploy to Cloud Run**
   - Run ./deploy.sh
   - Verify deployment successful

3. **Set up Pub/Sub**
   - Run ./setup_pubsub.sh
   - Verify subscription created

4. **Test with existing agent**
   - Configure log sink on gcp_traces_agent project
   - Send test query
   - Verify trace in Portal26

### Short Term (Next Sprint)

1. **Add batching**
   - Implement buffer accumulation
   - Batch export logic

2. **Add metrics**
   - Export to Cloud Monitoring
   - Create dashboard

3. **Add tests**
   - Unit tests for components
   - Integration test suite

4. **Documentation**
   - Client onboarding guide
   - Troubleshooting guide

### Long Term (Roadmap)

1. **Rate limiting**
   - Per-tenant limits
   - Quota management

2. **Advanced features**
   - Dead letter queue
   - Trace sampling
   - Data enrichment

3. **Observability**
   - Distributed tracing of worker itself
   - Alerting on errors

---

## Summary

✓ **All core components implemented**  
✓ **Ready for deployment to Cloud Run**  
✓ **Ready for testing with real data**  
✓ **Documentation complete**

**Next Action:** Deploy and test with real Vertex AI agent

---

**Implementation Time:** ~2 hours  
**Lines of Code:** ~800 LOC  
**Test Coverage:** Manual (automated tests pending)
