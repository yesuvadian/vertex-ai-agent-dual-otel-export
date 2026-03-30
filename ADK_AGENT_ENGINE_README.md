# ADK Agent Engine Deployment with Portal26 OTEL

Deploy Google ADK agents to Vertex AI Agent Engine with custom OTEL traces sent to Portal26.

**Based on:** Working solution from `adk-agent-engine-otel-custom-collector.md`

---

## 🎯 What This Does

Deploys your AI agent to **Vertex AI Agent Engine** (managed service) with:
- ✅ Google ADK framework
- ✅ Custom OTEL traces → Portal26
- ✅ Automatic scaling
- ✅ Built-in monitoring

**Architecture:**
```
Vertex AI Agent Engine (GCP)
    ↓ OTLP/HTTP
Portal26 OTEL Endpoint (https://otel-tenant1.portal26.in:4318)
    ↓
Portal26 Dashboard (https://portal26.in)
```

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install ADK CLI

```bash
pip install google-adk
```

### Step 2: Enable Vertex AI API

```bash
gcloud services enable aiplatform.googleapis.com
```

### Step 3: Deploy Agent

```bash
python deploy_adk_agent_engine.py
```

This will:
1. Create agent directory structure
2. Set up OTEL integration for Portal26
3. Deploy to Vertex AI Agent Engine
4. Configure traces → Portal26

### Step 4: Test Deployed Agent

```bash
python test_agent_engine.py
```

### Step 5: View Traces in Portal26

1. Go to: https://portal26.in
2. Login: titaniam / helloworld
3. Filter by:
   - Service: `ai-agent-engine`
   - Tenant: `tenant1`
   - User: `relusys`

---

## 📦 What Gets Created

```
adk_agent/
├── __init__.py           # OTEL bootstrap (registers custom exporter)
├── agent.py              # ADK agent with tools
├── .env                  # Environment variables (Portal26 config)
└── requirements.txt      # Python dependencies
```

---

## 🔧 How It Works

### The OTEL Bootstrap Pattern

**Key Insight from Working Example:**

Agent Engine initializes its own `TracerProvider`. Setting `OTEL_EXPORTER_OTLP_ENDPOINT` env var alone doesn't work. You must **programmatically append** a custom exporter.

**Solution:** `__init__.py` bootstrap

```python
# adk_agent/__init__.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def _add_custom_exporter():
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint.endswith("/v1/traces"):
        endpoint = endpoint.rstrip("/") + "/v1/traces"

    provider = trace.get_tracer_provider()

    if hasattr(provider, "add_span_processor"):
        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
        provider.add_span_processor(BatchSpanProcessor(exporter))

_add_custom_exporter()
```

This runs when the module is imported and **appends** the Portal26 exporter to Agent Engine's existing TracerProvider.

---

## 📋 Deployment Command

The deployment uses `adk deploy agent_engine`:

```bash
adk deploy agent_engine \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --display_name="ai-agent-portal26" \
  --otel_to_cloud \
  adk_agent
```

**Flags:**
- `--otel_to_cloud`: Enables Agent Engine telemetry
- `--display_name`: Human-readable name
- Agent directory (`adk_agent`) contains all files

**Note:** Don't use `--adk_app` flag - it has a CLI bug (double `.py` extension).

---

## 🔐 Environment Variables (.env)

```bash
# Vertex AI configuration
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716
GOOGLE_CLOUD_LOCATION=us-central1

# Portal26 OTEL configuration
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==

# OTEL settings
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
OTEL_SERVICE_NAME=ai-agent-engine
OTEL_PROPAGATORS=tracecontext,baggage
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=agent-engine

# Enable telemetry
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
```

---

## 🧪 Testing

### Python SDK Test

```python
import vertexai
from vertexai import agent_engines

vertexai.init(project="agentic-ai-integration-490716", location="us-central1")

# Get deployed agent
agents = agent_engines.list()
agent = agents[0]

# Query
response = agent.query(input="What is the weather in Tokyo?")
print(response)
```

### REST API Test

```bash
# Get resource ID
RESOURCE_ID=$(gcloud ai reasoning-engines list --location=us-central1 --format="value(name)" | head -1 | cut -d'/' -f6)

# Get token
TOKEN=$(gcloud auth print-access-token)

# Query
curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/$RESOURCE_ID:query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "What is the weather in Tokyo?"}'
```

### Automated Test Script

```bash
python test_agent_engine.py
```

---

## 📊 Monitoring & Debugging

### Check Agent Engine Logs

```bash
# Get resource ID
RESOURCE_ID=$(gcloud ai reasoning-engines list --location=us-central1 --format="value(name)" | head -1 | cut -d'/' -f6)

# View logs
gcloud logging read \
  "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND resource.labels.reasoning_engine_id=\"$RESOURCE_ID\"" \
  --project=agentic-ai-integration-490716 \
  --limit=100 \
  --format="value(textPayload)"
```

**Look for:**
- `[otel] Adding custom OTLP exporter` - Confirms bootstrap ran
- `[otel] Custom OTLP exporter registered successfully` - Exporter working
- Any error messages

### Check Deployed Environment Variables

```python
import vertexai
from vertexai import agent_engines

vertexai.init(project="agentic-ai-integration-490716", location="us-central1")
agents = agent_engines.list()
agent = agents[0]

# View configuration
print(agent.gca_resource)
```

### Verify OTEL Endpoint

```bash
# Test Portal26 endpoint directly
curl -s -X POST https://otel-tenant1.portal26.in:4318/v1/traces \
  -H "Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}'

# Should return: {"partialSuccess":{}}
```

---

## 🔄 Updating Deployed Agent

### Update Code

1. Modify `adk_agent/agent.py`
2. Redeploy:

```bash
adk deploy agent_engine \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --agent_engine_id=RESOURCE_ID \
  --display_name="ai-agent-portal26" \
  --otel_to_cloud \
  adk_agent
```

**Note:** Use `--agent_engine_id` to update existing agent, or omit to create new.

### Update OTEL Configuration

1. Edit `adk_agent/.env`
2. Redeploy (command above)

---

## 🆚 Comparison: Cloud Run vs Agent Engine

| Feature | Cloud Run (Current) | Agent Engine (ADK) |
|---------|---------------------|-------------------|
| **Framework** | FastAPI + Manual Agent | Google ADK |
| **Deployment** | Docker container | ADK CLI |
| **OTEL Setup** | Built into app | Custom exporter in `__init__.py` |
| **Control** | Full control | Managed by Google |
| **Best For** | Production REST API | ADK-based agents |
| **Portal26** | ✅ Full integration | ✅ Custom exporter |

---

## 💡 Key Learnings (from Working Example)

### 1. Env Vars Alone Don't Work

```bash
# ❌ This doesn't work
OTEL_EXPORTER_OTLP_ENDPOINT=https://portal26...
```

Agent Engine ignores this for custom exporters.

### 2. Programmatic Registration Required

```python
# ✅ This works
provider = trace.get_tracer_provider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(...)))
```

Must append exporter to Agent Engine's TracerProvider.

### 3. Timing Matters

Register exporter in `__init__.py` so it runs when module is imported.

### 4. Don't Use --adk_app Flag

Has a bug - double-appends `.py` extension. Use directory deployment instead.

### 5. --otel_to_cloud Flag

Overrides `.env` `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`. Use one or the other.

---

## 🎯 Use Cases

### Use Agent Engine When:
- ✅ Using Google ADK framework
- ✅ Want managed infrastructure
- ✅ Building conversational agents
- ✅ Need Vertex AI integration

### Use Cloud Run When:
- ✅ Custom REST API required
- ✅ Multiple frameworks
- ✅ Full control over deployment
- ✅ Already have working setup

### Use Both:
- ✅ Cloud Run for production API
- ✅ Agent Engine for ADK agents
- ✅ Best of both worlds!

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] ADK CLI installed (`pip install google-adk`)
- [ ] Vertex AI API enabled
- [ ] Authenticated (`gcloud auth application-default login`)
- [ ] Agent tested locally

### Deployment
- [ ] Run `python deploy_adk_agent_engine.py`
- [ ] Note Resource ID from output
- [ ] Verify deployment in Cloud Console

### Post-Deployment
- [ ] Run `python test_agent_engine.py`
- [ ] Check Agent Engine logs for `[otel]` messages
- [ ] Verify traces in Portal26 dashboard
- [ ] Test REST API endpoint

---

## 🔧 Troubleshooting

### Issue: "No spans received in Portal26"

**Check:**
1. Agent Engine logs show `[otel]` messages?
2. OTEL endpoint reachable?
3. Authentication headers correct?

**Debug:**
```bash
# Check logs for OTEL bootstrap
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --limit=100 | grep otel

# Test endpoint
curl -X POST https://otel-tenant1.portal26.in:4318/v1/traces \
  -H "Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}'
```

### Issue: "Deployment failed"

**Check:**
1. ADK CLI installed and updated
2. Vertex AI API enabled
3. Proper IAM permissions
4. Valid project ID

### Issue: "Agent not responding"

**Check:**
1. Query syntax correct
2. Agent deployed successfully
3. Check Agent Engine logs for errors

---

## 📚 Resources

- **ADK Documentation:** https://cloud.google.com/agent-builder/docs/adk
- **Agent Engine Docs:** https://cloud.google.com/agent-builder/agent-engine/deploy
- **Working Example:** See `adk-agent-engine-otel-custom-collector.md`
- **OTEL Documentation:** https://opentelemetry.io/docs/

---

## ✅ Summary

**You can now deploy ADK agents to Vertex AI Agent Engine with Portal26 OTEL!**

**Quick commands:**
```bash
# Deploy
python deploy_adk_agent_engine.py

# Test
python test_agent_engine.py

# View traces
# https://portal26.in (login: titaniam/helloworld)
```

**Key files created:**
- `deploy_adk_agent_engine.py` - Deployment script
- `test_agent_engine.py` - Testing script
- `adk_agent/` - Agent directory (created during deployment)

**The solution:** Custom OTEL exporter in `__init__.py` appends to Agent Engine's TracerProvider!

---

**Last Updated:** 2026-03-27
**Status:** ✅ Working (based on proven example)
