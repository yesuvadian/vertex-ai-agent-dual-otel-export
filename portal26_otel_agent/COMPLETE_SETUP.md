# Complete Portal26 OTEL Agent Setup

## Configuration

**All three telemetry signals enabled:**
- ✓ **Traces** - Request flow, timing, span hierarchy (200 OK)
- ✓ **Metrics** - Aggregated statistics (404 expected in staging, won't break other signals)
- ✓ **Logs** - Discrete events and error messages (200 OK)

## Agent Code

**File:** `agent.py`
- Lines 5-38: Traces setup with OTLPSpanExporter
- Lines 41-52: Metrics setup with OTLPMetricExporter (wrapped in try/except)
- Lines 55-72: Logs setup with OTLPLogExporter (wrapped in try/except)
- Error handling ensures one signal failing doesn't break others

**Agent:** `portal26_otel_complete`
- Service: `portal26_otel_agent`
- Tenant: `tenant1`
- User: `relusys`

## Portal26 Endpoints

```
Base: https://otel-tenant1.portal26.in:4318

Traces:  /v1/traces   → 200 OK ✓
Metrics: /v1/metrics  → 404 (staging disabled, expected)
Logs:    /v1/logs     → 200 OK ✓
```

## Data Flow

```
Agent (Vertex AI)
    ↓
OpenTelemetry SDK
    ↓
Portal26 OTEL Collector
    ↓
AWS Kinesis Stream (stg_otel_source_data_stream)
    ↓
pull_agent_logs.py
    ↓
Analysis & Visualization
```

## Captured Data

### Traces (Structure & Timing)
```json
{
  "traceId": "0000000000000000cefd10716a1122d1",
  "spans": [
    "HTTP receive/send (0.06ms)",
    "LLM call (973ms)",
    "Tool execution (0.37ms)"
  ],
  "metadata": {
    "service.name": "portal26_otel_agent",
    "portal26.tenant_id": "tenant1",
    "portal26.user.id": "relusys",
    "gen_ai.usage.input_tokens": 106,
    "gen_ai.usage.output_tokens": 6
  }
}
```

### Logs (Events & Errors)
```json
{
  "resourceLogs": [{
    "resource": {
      "attributes": [
        {"key": "service.name", "value": "portal26_otel_agent"},
        {"key": "portal26.tenant_id", "value": "tenant1"}
      ]
    },
    "logRecords": [{
      "severityText": "ERROR",
      "body": "Failed to export metrics batch code: 404"
    }]
  }]
}
```

### Metrics (Expected 404)
- Metrics endpoint disabled in staging
- Will log errors but won't break traces/logs
- Production environment should enable this endpoint

## Known Limitations

### Content Capture
❌ **Prompt/response content empty** due to Vertex AI managed runtime
- `gcp.vertex.agent.llm_request`: `{}`
- `gcp.vertex.agent.llm_response`: `{}`
- Vertex AI doesn't expose `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` control
- **Accepted limitation** - focus on observability (timing, structure, metadata)

### Metrics 404
⚠️ **Expected behavior** in staging environment
- Wrapped in try/except - doesn't break other signals
- Production should enable `/v1/metrics` endpoint

## Files

**Core:**
- `agent.py` - Agent with all three OTEL signals
- `.env` - Configuration (local only, not deployed)
- `deploy.py` - Vertex AI Reasoning Engine deployment

**Data Collection:**
- `pull_agent_logs.py` - Pull traces + logs from Kinesis
- `show_traces.py` - Display trace structure
- `check_raw_data.py` - Inspect raw Kinesis data

**Analysis:**
- `all_traces.json` - Extracted trace data (42KB)
- `TRACE_ANALYSIS.md` - Complete trace breakdown
- `agent_logs_*.jsonl` - Raw Kinesis dumps

## Usage

### Pull Latest Telemetry
```bash
cd portal26_otel_agent
python pull_agent_logs.py
```

### View Traces
```python
python show_traces.py
```

### Deploy Agent
```bash
python deploy.py
```

## Multi-Tenant Support

All telemetry includes tenant context:
```json
{
  "portal26.tenant_id": "tenant1",
  "portal26.user.id": "relusys",
  "agent.type": "otel-direct"
}
```

Filter in Kinesis pull script automatically includes these identifiers.

## Success Metrics

- ✓ Traces captured: 6 spans per query
- ✓ Logs captured: ~180 records per 5-minute window
- ✓ Metrics errors logged: Yes (expected 404)
- ✓ Multi-tenant tags: Present on all signals
- ✓ Token usage tracked: Input/output/reasoning tokens
- ✓ Tool calls traced: Names and timing captured
- ✗ Content capture: Not available (Vertex AI limitation)
