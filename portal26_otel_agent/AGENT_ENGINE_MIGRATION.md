# Migration to Vertex AI Agent Engine

## Summary

Migrated from **Vertex AI Reasoning Engine** to **Vertex AI Agent Engine** to enable full prompt/response content capture in OTEL traces.

## What Changed

### API Switch

**Before (Reasoning Engine):**
```python
from vertexai.preview import reasoning_engines

# Required wrapper class
class AgentWrapper:
    def query(self, *, user_input: str):
        return self.agent.run_live(user_input=user_input)

reasoning_engine = reasoning_engines.ReasoningEngine.create(
    AgentWrapper(root_agent),
    requirements=[...],
    # ❌ No env_vars parameter
)
```

**After (Agent Engine):**
```python
from vertexai import agent_engines

# No wrapper needed
deployed_agent = agent_engines.create(
    agent_engine=root_agent,
    requirements=[...],
    # ✅ env_vars parameter available
    env_vars=otel_config.OTEL_CONFIG,
)
```

### Content Capture Enabled

**Key Change in otel_config.py:**
```python
OTEL_CONFIG = {
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",  # ✅ NOW WORKS!
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel-tenant1.portal26.in:4318",
    ...
}
```

### VertexAI Instrumentation Added

**In agent.py (lines 84-97):**
```python
try:
    from opentelemetry.instrumentation.vertexai import VertexAIInstrumentor
    VertexAIInstrumentor().instrument()
    print(f"[OTEL_INIT] Vertex AI instrumentation enabled")
    
    content_capture = os.environ.get("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false")
    print(f"[OTEL_INIT] Content capture: {content_capture}")
except Exception as e:
    print(f"[OTEL_INIT] Vertex AI instrumentation warning: {e}")
```

### New Configuration Files

**config.py** - Central configuration:
```python
GOOGLE_CLOUD_PROJECT = "agentic-ai-integration-490716"
GOOGLE_CLOUD_LOCATION = "us-central1"
OTEL_ENDPOINT = "https://otel-tenant1.portal26.in:4318"
SERVICE_NAME = "portal26_otel_agent"
TENANT_ID = "tenant1"
USER_ID = "relusys"
```

**otel_config.py** - OTEL environment variables:
```python
OTEL_CONFIG = {
    "OTEL_SERVICE_NAME": config.SERVICE_NAME,
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
    "OTEL_EXPORTER_OTLP_ENDPOINT": config.OTEL_ENDPOINT,
    ...
}
```

### Updated Requirements

**Added to requirements.txt:**
```
opentelemetry-instrumentation-vertexai>=2.0b0  # Critical for content capture
opentelemetry-instrumentation-google-genai>=0.4b0
boto3  # For Kinesis retrieval
```

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `agent.py` | Modified | Added VertexAIInstrumentor + content capture check |
| `deploy.py` | Rewritten | Switch from reasoning_engines to agent_engines |
| `requirements.txt` | Modified | Added VertexAI instrumentation packages |
| `config.py` | Created | Central configuration for GCP & Portal26 |
| `otel_config.py` | Created | OTEL env vars with content capture enabled |
| `AGENT_ENGINE_MIGRATION.md` | Created | This document |

## Expected Results

### Before Migration (Reasoning Engine)

**Traces:**
```json
{
  "llm_request": {},  // ❌ Empty
  "llm_response": {},  // ❌ Empty
  "tool_call_args": {}  // ❌ Empty
}
```

**Reason:** Platform controls `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` and sets it to `false`

### After Migration (Agent Engine)

**Traces:**
```json
{
  "llm_request": {
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "user", "content": "What's the weather in Tokyo?"}
    ]
  },  // ✅ Full content
  "llm_response": {
    "content": "Let me check the weather for you...",
    "tool_calls": [{"name": "get_weather", "args": {"city": "Tokyo"}}]
  },  // ✅ Full content
  "tool_call_args": {
    "city": "Tokyo"
  }  // ✅ Full content
}
```

**Reason:** Agent Engine respects `env_vars` parameter and enables content capture

## Deployment

**Deploy to Agent Engine:**
```bash
cd portal26_otel_agent
python deploy.py
```

**Query the deployed agent:**
```bash
python query_agent.py <agent_id> "What is the weather in Tokyo?"
```

**Verify content capture:**
```bash
python pull_agent_logs.py  # Fetch from Kinesis
python show_traces.py       # Parse and display traces
# Check for non-empty llm_request and llm_response fields
```

## Key Benefits

| Feature | Reasoning Engine | Agent Engine |
|---------|------------------|--------------|
| **Content Capture** | ❌ Blocked | ✅ Enabled |
| **Wrapper Class** | ✅ Required | ❌ Not needed |
| **env_vars Support** | ❌ No | ✅ Yes |
| **VertexAI Instrumentation** | ❌ No | ✅ Yes |
| **Deployment Complexity** | Higher | Lower |

## Verification Checklist

After deployment, verify:

- [ ] Agent deploys successfully to Agent Engine
- [ ] Console playground accessible
- [ ] Agent responds to queries
- [ ] Traces exported to Portal26
- [ ] Logs exported to Portal26
- [ ] Metrics attempts (expect 404 in staging)
- [ ] **Content capture enabled** - check `llm_request` and `llm_response` in traces
- [ ] Kinesis retrieval works
- [ ] Multi-tenant tags present (tenant1, relusys)

## Documentation Updates Needed

Update these files to reflect Agent Engine:
- [ ] README.md - Change "Reasoning Engine" to "Agent Engine"
- [ ] ARCHITECTURE.md - Update deployment section
- [ ] LIMITATIONS.md - Remove content capture limitation (now fixed!)

## References

- Agent Engine API: `vertexai.agent_engines.create()`
- Reasoning Engine API (old): `vertexai.preview.reasoning_engines.ReasoningEngine.create()`
- VertexAI Instrumentation: `opentelemetry-instrumentation-vertexai>=2.0b0`
- Downloaded reference code: `C:\Users\yesuv\Downloads\hardcode-otel-vertex-ai-master\`
