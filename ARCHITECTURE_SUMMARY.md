# Architecture Quick Summary

## The Flow in 10 Steps

```
1. User sends query to Vertex AI Agent
   ↓
2. Agent executes → generates traces → Cloud Trace stores them
   ↓
3. Cloud Logging receives log with trace reference
   ↓
4. Log Sink exports to Pub/Sub (cross-project)
   ↓
5. Pub/Sub pushes to Worker (HTTP POST)
   ↓
6. Worker decodes message, extracts trace ID
   ↓
7. Worker fetches COMPLETE trace from Cloud Trace API
   ↓
8. Worker transforms GCP format → OpenTelemetry format
   ↓
9. Worker exports to Portal26 (OTLP/HTTP with auth)
   ↓
10. Portal26 stores and displays trace
```

---

## Key Components (5 Main Pieces)

### 1. **Source** - Vertex AI Reasoning Engine
- Runs AI agent workflows
- Auto-generates traces
- Location: Client project

### 2. **Transport** - Cloud Logging + Pub/Sub
- Logging captures trace references
- Pub/Sub delivers across projects
- Location: Client → Telemetry project

### 3. **Processor** - Telemetry Worker (Flask)
- Receives Pub/Sub messages
- Fetches full traces
- Transforms and exports
- Location: Telemetry project (Cloud Run or local)

### 4. **Storage** - Cloud Trace
- Stores complete trace data
- Provides API access
- Location: Client project

### 5. **Destination** - Portal26
- Receives OTEL traces
- Provides observability UI
- Location: External service

---

## Why Each Component?

| Component | Why Not Alternatives? |
|-----------|----------------------|
| **Pub/Sub (Push)** | vs Direct: Need async processing, retry logic, scaling |
| **Cloud Trace API** | vs Log data: Logs only have reference, need full spans |
| **OTEL Format** | vs GCP: Portal26 expects OTEL, vendor-neutral |
| **Cloud Run** | vs VM: Auto-scaling, pay-per-use, managed |
| **Stateless** | vs Stateful: Scales better, retry-safe, simpler |

---

## Critical Design Decisions

### 1. **Cross-Project Architecture**
**Problem:** Multiple clients, each with own GCP project  
**Solution:** Central telemetry project fetches traces from client projects  
**Benefit:** Single deployment, centralized observability

### 2. **Dynamic Tenant Extraction**
**Problem:** New tenants/clients being added frequently  
**Solution:** Extract tenant_id from each message at runtime  
**Benefit:** No restart needed, automatic multi-tenant support

### 3. **Span ID Conversion Fix**
**Problem:** GCP uses decimal IDs (e.g., "7816615611132699434")  
**Solution:** Convert decimal → int → 16-char hex → bytes  
**Impact:** Critical for OTEL compatibility

### 4. **Two-Phase Processing**
**Problem:** Logs only contain trace reference, not full data  
**Solution:** First get trace ID from log, then fetch full trace  
**Benefit:** Complete span hierarchy and timing data

---

## Data Transformations

### Log Entry → Metadata
```python
{
  "trace": "projects/proj/traces/58c0122e..."  # Reference
  "labels": {"tenant_id": "tenant1"}
}
↓
{
  "trace_id": "58c0122e...",
  "project_id": "proj",
  "tenant_id": "tenant1"
}
```

### GCP Trace → OTEL Trace
```python
GCP Span:
{
  "span_id": "7816615611132699434",  # Decimal string
  "start_time": Timestamp(...),      # DateTime object
  "labels": {"key": "value"}         # Dict
}
↓
OTEL Span:
{
  "span_id": b'lmi napi',            # 8 bytes (hex)
  "start_time_unix_nano": 1234567..., # Nanoseconds
  "attributes": [KeyValue(...)]       # Protobuf
}
```

### OTEL → Portal26
```python
ResourceSpans (protobuf)
↓
HTTP POST /v1/traces
Content-Type: application/x-protobuf
Authorization: Basic <base64>
Body: <serialized-protobuf>
↓
HTTP 200 OK
```

---

## Current vs Production Setup

### Development (Current - Port 8082)
```
Pub/Sub → ngrok → Flask (localhost:8082) → Portal26
```
**Pros:** 
- Easy debugging (local logs)
- Fast iteration (no deployment)
- See requests in real-time

**Cons:**
- Single instance (no scaling)
- ngrok URL changes on restart
- Not production-ready

### Production (Cloud Run)
```
Pub/Sub → Cloud Run (auto-scaled) → Portal26
```
**Pros:**
- Auto-scaling (1-100 instances)
- High availability
- Managed infrastructure
- Static URL

**Cons:**
- Logs in Cloud Logging (less immediate)
- Needs IAM permissions
- Deployment step required

---

## Performance Characteristics

| Metric | Current | Expected Production |
|--------|---------|-------------------|
| **Latency** | ~5 seconds | ~3 seconds |
| **Throughput** | ~10 traces/min | ~1000 traces/min |
| **Availability** | 0% (local) | 99.9% (Cloud Run) |
| **Cost** | $0 | ~$5-20/month |

**Latency Breakdown:**
- Pub/Sub delivery: ~100ms
- Fetch from Cloud Trace: ~4s
- Transform to OTEL: ~100ms
- Export to Portal26: ~500ms

---

## Security Model

### Authentication Chain
```
1. Pub/Sub → Worker
   - Dev: None (public ngrok)
   - Prod: IAM token verification

2. Worker → Cloud Trace API
   - Application Default Credentials
   - Needs: roles/cloudtrace.user

3. Worker → Portal26
   - Basic Authentication
   - Username + Password in headers
```

### Data Flow Security
```
Client Project (Private)
    ↓ IAM-controlled log sink
Pub/Sub (Private)
    ↓ Push subscription
Worker (IAM-protected)
    ↓ HTTPS + Basic Auth
Portal26 (External, authenticated)
```

---

## Key Configuration Points

### Environment Variables (.env)
```bash
# Portal26
PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318/v1/traces
PORTAL26_USERNAME=titaniam
PORTAL26_PASSWORD=helloworld

# Resource attributes (tags)
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1

# Optional
REDIS_HOST=localhost  # For dedup cache
REDIS_PORT=6379
```

### Pub/Sub Subscription
```bash
gcloud pubsub subscriptions update telemetry-processor \
  --push-endpoint="<WORKER_URL>/process" \
  --ack-deadline=600
```

### Log Sink Filter
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
resource.labels.reasoning_engine_id="8081657304514035712"
```

---

## Monitoring Points

### What to Monitor

**1. Pub/Sub Metrics**
- Undelivered messages (should be 0)
- Oldest unacknowledged message age (should be < 1 min)
- Delivery attempts (high = worker issues)

**2. Worker Metrics**
- HTTP 500 rate (should be < 1%)
- Processing latency (should be < 5s)
- Cloud Trace API errors (rate limits?)

**3. Portal26 Metrics**
- Export success rate (should be > 99%)
- HTTP 400 errors (invalid data?)
- Missing traces (processing gaps?)

### Health Checks
```bash
# Worker health
curl http://localhost:8082/health

# Pub/Sub status
gcloud pubsub subscriptions describe telemetry-processor

# Recent traces
cd gcp_traces_agent_client
python view_traces.py --hours 1 --limit 5
```

---

## Failure Modes & Recovery

### Scenario 1: Worker Down
**What happens:** Pub/Sub retries with exponential backoff  
**Recovery:** Messages queued, processed when worker returns  
**Max retention:** 7 days in Pub/Sub

### Scenario 2: Cloud Trace API Rate Limit
**What happens:** 429 errors, automatic retries  
**Recovery:** Exponential backoff in TraceFetcher  
**Prevention:** Batch fetching (future improvement)

### Scenario 3: Portal26 Down
**What happens:** Export fails, worker returns 500  
**Recovery:** Pub/Sub retries message  
**Max attempts:** Configurable (default: infinite with backoff)

### Scenario 4: Invalid Span IDs
**What happens:** Warning logged, span skipped  
**Recovery:** Other spans still processed  
**Fixed:** Decimal to hex conversion

---

## Testing Strategy

### Unit Tests (Future)
```python
test_trace_fetcher.py    # Mock Cloud Trace API
test_otel_transformer.py # Test span conversions
test_portal26_exporter.py # Mock Portal26 endpoint
```

### Integration Tests
```bash
# Test with real trace ID
python test_console_trace.py

# Test with mock Pub/Sub message
python test_local.py <project> <trace_id> <tenant> <endpoint>
```

### End-to-End Test
```
1. Send query to Vertex AI Console
2. Monitor Flask logs
3. Verify in Portal26 UI
4. Check resource attributes match
```

---

## Future Improvements

### Phase 1: Production Hardening
- [ ] Copy fixes to telemetry_worker/
- [ ] Deploy to Cloud Run
- [ ] Get IAM permissions
- [ ] Switch Pub/Sub to Cloud Run endpoint
- [ ] Monitor for 24 hours

### Phase 2: Optimization
- [ ] Add Redis for dedup cache
- [ ] Batch multiple traces in one export
- [ ] Add metrics/monitoring (Prometheus)
- [ ] Cache frequently accessed metadata
- [ ] Compress exports (gzip)

### Phase 3: Features
- [ ] Support multiple Portal26 tenants
- [ ] Add trace sampling (if volume high)
- [ ] Support other OTEL backends (Jaeger, Tempo)
- [ ] Add trace enrichment (custom attributes)
- [ ] Dead letter queue for failed exports

---

## Quick Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| No traces in Portal26 | Flask logs | Check if messages arriving |
| 400 from Portal26 | Span ID conversion | Verify hex format |
| 500 from Cloud Trace | IAM permissions | Add cloudtrace.user role |
| Duplicates in Portal26 | Dedup cache | Enable Redis |
| High latency | Cloud Trace API | Add batching |

---

## One-Line Summary

**"Captures Vertex AI traces from client projects, fetches complete data via Cloud Trace API, transforms to OpenTelemetry format, and exports to Portal26 for centralized multi-tenant observability."**

---

For detailed technical explanation, see: **ARCHITECTURE_EXPLAINED.md**
