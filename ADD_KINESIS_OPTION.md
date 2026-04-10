# Option: Add Kinesis for Log Retrieval

## Current Architecture (Simple)
```
portal26_agent_v3 → Portal26 OTEL (4318)
                      ├─ /v1/traces  ✓
                      └─ /v1/logs    ✓
```

**Pros:** Simple, direct  
**Cons:** No local copy for offline analysis

---

## Proposed Architecture (with Kinesis)

### Option A: Dual Export from Agent
```
portal26_agent_v3 → Portal26 OTEL (4318)
                  ↘
                    AWS Kinesis Stream
```

**Implementation:** Add second OTLP exporter in agent

### Option B: OTEL Collector in Middle
```
portal26_agent_v3 → OTEL Collector
                      ├─→ Portal26
                      └─→ Kinesis
```

**Implementation:** Deploy OTEL Collector, configure pipelines

---

## Option A: Dual Export (Simpler)

### 1. Create AWS Kinesis Stream
```bash
aws kinesis create-stream \
  --stream-name prod_otel_traces \
  --shard-count 1 \
  --region us-east-2
```

### 2. Install Kinesis Exporter
```bash
pip install opentelemetry-exporter-kinesis
```

### 3. Update agent.py
```python
from opentelemetry.exporter.kinesis import KinesisSpanExporter

# Existing Portal26 exporter
portal26_exporter = OTLPSpanExporter(endpoint="https://otel-tenant1.portal26.in:4318/v1/traces")
portal26_processor = BatchSpanProcessor(portal26_exporter)

# NEW: Add Kinesis exporter
kinesis_exporter = KinesisSpanExporter(
    stream_name="prod_otel_traces",
    region_name="us-east-2"
)
kinesis_processor = BatchSpanProcessor(kinesis_exporter)

# Add BOTH processors
provider.add_span_processor(portal26_processor)
provider.add_span_processor(kinesis_processor)
```

### 4. Use kenis_pull.sh
```bash
# Update script config
STREAM_ARN="arn:aws:kinesis:us-east-2:YOUR_ACCOUNT:stream/prod_otel_traces"

# Pull logs
./kenis_pull.sh
```

**Pros:**
- ✅ Keep Portal26 real-time view
- ✅ Get local copy for analysis
- ✅ Offline debugging

**Cons:**
- ❌ More complex agent code
- ❌ AWS costs for Kinesis
- ❌ Dual export overhead

---

## Option B: OTEL Collector (Production Grade)

### 1. Deploy OTEL Collector
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s

exporters:
  otlphttp/portal26:
    endpoint: https://otel-tenant1.portal26.in:4318
    headers:
      authorization: "Basic dGl0YW5pYW06aGVsbG93b3JsZA=="

  kinesis:
    region: us-east-2
    stream_name: prod_otel_traces

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlphttp/portal26, kinesis]
```

### 2. Update Agent to Send to Collector
```python
# Instead of Portal26 directly
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4318
```

### 3. Use kenis_pull.sh
```bash
./kenis_pull.sh
```

**Pros:**
- ✅ Agent code stays simple
- ✅ Centralized telemetry routing
- ✅ Easy to add more destinations
- ✅ Production-grade architecture

**Cons:**
- ❌ Additional infrastructure (OTEL Collector)
- ❌ More moving parts
- ❌ AWS costs

---

## Recommendation

**For your use case (debugging/testing):**

### Keep it Simple
```
1. Use Portal26 UI for real-time viewing
2. If Portal26 has export/API, use that
3. Only add Kinesis if you need:
   - Offline analysis
   - Long-term storage
   - Compliance/audit trail
```

### If you need local logs:
```
Option 1: Export from Portal26 UI (if available)
Option 2: Add file exporter to agent (simpler than Kinesis)
```

### File Exporter (Simplest for Local Copy)
```python
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.file import FileSpanExporter

# Portal26 (real-time)
portal26_exporter = OTLPSpanExporter(endpoint="...")
provider.add_span_processor(BatchSpanProcessor(portal26_exporter))

# Local file (backup)
file_exporter = FileSpanExporter("traces.jsonl")
provider.add_span_processor(SimpleSpanProcessor(file_exporter))
```

Then analyze with:
```bash
grep "portal26_agent_v3" traces.jsonl | jq .
```

**No AWS, no Kinesis, just local files!**

---

## Summary

| Method | Complexity | Cost | Use When |
|--------|-----------|------|----------|
| Portal26 UI only | Low | $0 | Default choice |
| + File exporter | Low | $0 | Need local backup |
| + Kinesis | Medium | $$ | Need replay/audit |
| + OTEL Collector | High | $$$ | Production scale |

**Your current setup is fine!** Only add complexity if you have specific needs.
