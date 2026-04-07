# Vertex AI Reasoning Engine - Known Limitations

## Vertex AI Reasoning Engine Platform Limitations

### Overview
Vertex AI Reasoning Engine provides a **managed runtime** with built-in observability, but this comes with several constraints that limit customization and visibility.

### 1. Managed Runtime Environment
- **No SSH access** to Cloud Run container
- **No console access** to inspect running processes
- **Limited logging** - only structured logs visible
- **No file system access** after deployment
- **Cannot inspect OTEL configuration** at runtime

### 2. Environment Variable Constraints
- **.env files NOT deployed** - only packaged code
- **Cannot set custom environment variables** via deployment API
- **Environment variables must be hardcoded** in agent.py
- **No runtime configuration changes** without redeployment
- **Cloud Run env vars not accessible** during container init

### 3. Container Lifecycle Restrictions
- **Auto-scaling controlled by platform** - cannot configure
- **Cold start time varies** (typically 2-3 seconds)
- **No persistent storage** between invocations
- **Container recycling unpredictable** - may restart anytime
- **Cannot install system packages** outside requirements.txt

### 4. OpenTelemetry Integration Constraints
- **Platform-provided OTEL instrumentation** - cannot replace
- **Cannot modify OTEL config** after module import
- **Instrumentation auto-injected** - no control over hooks
- **Cannot disable auto-instrumentation** for specific spans
- **Limited visibility** into OTEL internal operations

### 5. Deployment Package Limitations
- **Max package size**: Limited by Cloud Run constraints
- **Python version**: Platform-managed (currently 3.11)
- **Dependencies**: Must be in requirements.txt or extra_packages
- **Binary dependencies**: Limited support
- **Build time**: 2-5 minutes on average

### 6. Network and Security
- **Outbound HTTPS only** - no arbitrary ports
- **Cannot configure VPC** directly
- **IP address not static** - changes with scaling
- **TLS/SSL certificates** managed by platform
- **Cannot use custom CA certificates** easily

### 7. Monitoring and Debugging
- **No direct Cloud Run metrics** access
- **Cannot attach debugger** to running container
- **Log sampling** may occur under load
- **Trace sampling** controlled by platform
- **Cannot capture heap dumps** or profiles

### 8. Query Interface Requirements
- **Must implement query() method** - strict requirement
- **Must return synchronous result** - no async streaming
- **Query method signature fixed** - `query(*, user_input: str)`
- **Cannot customize API schema** for reasoning engine
- **Error handling opaque** - platform catches exceptions

---

## 1. Content Capture Limitation (CRITICAL)

### Issue
**Prompts and responses are NOT captured in traces** - only metadata, timing, and structure.

### Root Cause
Vertex AI Reasoning Engine uses a **managed runtime** where:
- OpenTelemetry instrumentation is provided by the platform
- Environment variable `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` is **not accessible**
- No control over Cloud Run container environment variables

### What IS Captured
```json
{
  "traceId": "0000000000000000cefd10716a1122d1",
  "spanId": "9af226ff09117061",
  "name": "generate_content gemini-2.5-flash",
  "duration_ms": 973.19,
  "gen_ai.usage.input_tokens": 106,
  "gen_ai.usage.output_tokens": 6
}
```

### What is NOT Captured
```json
{
  "gcp.vertex.agent.llm_request": "{}",    // Empty
  "gcp.vertex.agent.llm_response": "{}",   // Empty
  "gcp.vertex.agent.tool_call_args": "{}"  // Empty
}
```

### Impact
- ✓ Can observe **WHAT** happened (structure, timing, tool calls)
- ✓ Can measure **HOW LONG** (performance monitoring)
- ✓ Can track **WHO** (tenant_id, user_id)
- ✗ Cannot see **CONTENT** (actual user queries, LLM responses, tool arguments)

### Workarounds Evaluated
1. **Setting env var in agent.py** ❌ Module loads before env vars take effect in Cloud Run
2. **Custom wrapper class** ❌ Still inherits platform's OTEL instrumentation
3. **Deploying to Cloud Run directly** ⚠️ Possible but loses Vertex AI managed features

### Decision
**Accept limitation** - Focus on observability use case (timing, structure, metadata) rather than full content logging.

### When This Matters
- **Debugging**: Cannot replay exact prompts/responses
- **Content Analysis**: Cannot analyze what users are asking
- **Quality Assurance**: Cannot verify response correctness from traces alone
- **Security Auditing**: Limited visibility into actual data processed

### When This Doesn't Matter
- **Performance Monitoring**: Trace timing is fully captured ✓
- **Availability Monitoring**: Request success/failure tracked ✓
- **Usage Tracking**: Token counts and tool usage captured ✓
- **Multi-tenant Observability**: Tenant/user tags present ✓

---

## 2. Metrics Endpoint 404 Error

### Issue
Metrics export fails with **HTTP 404** on every attempt.

```
ERROR: Failed to export metrics batch code: 404, reason: 404 page not found
```

### Root Cause
Portal26 staging environment has `/v1/metrics` endpoint **disabled**.

### Impact
- ✗ Cannot capture custom metrics (counters, gauges, histograms)
- ✓ Traces and logs continue working (independent pipelines)
- ⚠️ Generates ~10 error log entries per minute

### Mitigation
Code wrapped in `try/except` to prevent crashes:
```python
try:
    metric_exporter = OTLPMetricExporter(endpoint=metrics_endpoint)
    # ...
except Exception as e:
    print(f"[OTEL_INIT] Metrics setup warning: {e}")
```

### Expected Behavior
- Staging: 404 errors logged but system continues
- Production: Should enable `/v1/metrics` endpoint

### Configuration
```python
# Metrics configured but expect 404
metrics_endpoint = "https://otel-tenant1.portal26.in:4318/v1/metrics"
export_interval_millis = 10000  # 10 seconds
```

---

## 3. Data Latency

### Issue
Telemetry data appears in Kinesis with **1-2 minute delay**.

### Contributing Factors
1. **BatchSpanProcessor**: Buffers spans for 30 seconds or 512 spans
2. **Portal26 Processing**: ~10-30 seconds
3. **Kinesis Propagation**: ~10-30 seconds

### Impact
- ✗ Real-time monitoring not possible
- ✓ Acceptable for observability and debugging
- ⚠️ Must wait 2+ minutes after query to see traces

### Timeline
```
User Query → Agent → OTEL Buffer (30s) → Portal26 (10-30s) → Kinesis (10-30s)
                                            ↓
                                   Total: 60-120 seconds
```

### Workarounds
None - this is by design for batch efficiency. Real-time monitoring would require:
- Reducing batch window (impacts network efficiency)
- Direct streaming (not supported by platform)

---

## 4. Environment Variable Deployment

### Issue
`.env` files are **NOT deployed** to Cloud Run container.

### Root Cause
Vertex AI Reasoning Engine packages code but not config files.

### What Works
```python
# Hardcoded in agent.py (works)
endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
```

### What Doesn't Work
```bash
# .env file (NOT deployed)
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
```

### Solution
Set environment variables via:
1. **Hardcode defaults** in agent.py (current approach)
2. **Vertex AI deployment config** (if supported)
3. **Cloud Run environment variables** (manual configuration)

---

## 5. Multi-Line JSON Parsing

### Issue
Kinesis records are **pretty-printed JSON** (indented), not single-line JSONL.

### Example
```json
{
  "resourceSpans": [
    {
      "resource": {
        ...
      }
    }
  ]
}
```

### Impact
- Standard JSONL parsers fail
- Requires custom regex splitting: `re.split(r'\}\n\{', content)`

### Solution
`show_traces.py` implements custom parser:
```python
records_raw = re.split(r'\}\n\{', content)
for record_str in records_raw:
    # Re-add braces stripped by split
    if not record_str.startswith('{'):
        record_str = '{' + record_str
    if not record_str.endswith('}'):
        record_str = record_str + '}'
    data = json.loads(record_str)
```

---

## 6. AgentWrapper Requirement

### Issue
Vertex AI Reasoning Engine requires agents to have a `query()` method.

### Error Without Wrapper
```
TypeError: reasoning_engine has neither a callable method named `query` 
nor a callable method named `register_operations`.
```

### Solution
Wrap agent in class with `query()` method:
```python
class AgentWrapper:
    def __init__(self, agent):
        self.agent = agent
    
    def query(self, *, user_input: str):
        return self.agent.run_live(user_input=user_input)
```

### Impact
- Adds layer of indirection
- Slightly increases code complexity
- Required for Vertex AI compatibility

---

## 7. No Metrics Visualization

### Issue
No built-in visualization for captured telemetry data.

### Current State
- Raw JSON files only
- Manual parsing required
- No dashboards or graphs

### What Would Help
- Grafana/Prometheus integration
- Portal26 UI (if available)
- Custom visualization scripts
- Integration with Cloud Trace UI

---

## Summary Table

| Limitation | Severity | Impact | Workaround Available |
|------------|----------|--------|---------------------|
| No Content Capture | **HIGH** | Cannot see prompts/responses | ❌ No (platform limitation) |
| Metrics 404 Error | **LOW** | No metrics data | ⚠️ Accept & ignore |
| 1-2 Min Latency | **MEDIUM** | Not real-time | ❌ No (by design) |
| .env Not Deployed | **LOW** | Manual config needed | ✓ Hardcode in agent.py |
| Multi-line JSON | **LOW** | Parsing complexity | ✓ Custom parser |
| Wrapper Required | **LOW** | Code complexity | ✓ AgentWrapper class |
| No Visualization | **LOW** | Raw data only | ⚠️ External tools |

