# ✅ Dual OTEL Export - Successfully Configured!

**Date:** 2026-03-27 20:15
**Status:** 🟢 **FULLY OPERATIONAL**

---

## 📊 Deployment Summary

### New Agent Deployed
- **Name:** ai-agent-dual-export
- **Resource ID:** 3691509684943978496
- **Created:** 2026-03-27 14:34:40
- **Console URL:** https://console.cloud.google.com/vertex-ai/reasoning-engines/3691509684943978496?project=agentic-ai-integration-490716

### Total Agents: 7

| # | Name | Resource ID | Status |
|---|------|-------------|--------|
| 1 | ai-agent-dual-export | 3691509684943978496 | ✅ Dual Export |
| 2 | ai-agent-portal26 | 6317108267700977664 | ✅ Portal26 Direct |
| 3 | ai-agent-portal26-otel | 8818294910751866880 | ✅ Portal26 Direct |
| 4 | ai-agent-portal26-otel | 8206368311382900736 | ✅ Portal26 Direct |
| 5 | ai-agent-portal26-otel | 5441158140177416192 | ✅ Portal26 Direct |
| 6 | ai-agent-portal26-otel | 4812905992159232000 | ✅ Portal26 Direct |
| 7 | city-info-agent | 281862554559447040 | ✅ Portal26 Direct |

**View All Agents:**
https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716

---

## 🔄 Dual Export Architecture

```
Vertex AI Agent Engine (ai-agent-dual-export)
        ↓
        ↓ HTTPS POST (OTEL/HTTP)
        ↓
ngrok (https://tabetha-unelemental-bibulously.ngrok-free.dev)
        ↓
        ↓ Forward to localhost:4318
        ↓
Local OTEL Collector (Docker)
        ↓
        ├─→ Local Files (otel-data/)
        │   ├─ otel-traces.json (5.1 KB)
        │   ├─ otel-logs.json (28 KB)
        │   └─ otel-metrics.json (3.4 MB)
        │
        ├─→ Portal26 (https://otel-tenant1.portal26.in:4318)
        │   └─ Forwarding all signals
        │
        └─→ Console (debug output)
```

---

## 📁 Local Data Files

**Location:** `C:\Yesu\ai_agent_projectgcp\otel-data\`

| File | Size | Last Updated |
|------|------|--------------|
| otel-traces.json | 5.1 KB | Mar 27 19:48 |
| otel-logs.json | 28 KB | Mar 27 20:03 |
| otel-metrics.json | 3.4 MB | Mar 27 20:03 |

---

## 🛠️ Configuration

### Agent Environment Variables (.env)

```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716
GOOGLE_CLOUD_LOCATION=us-central1
OTEL_EXPORTER_OTLP_ENDPOINT=https://tabetha-unelemental-bibulously.ngrok-free.dev
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
OTEL_SERVICE_NAME=ai-agent-engine
OTEL_PROPAGATORS=tracecontext,baggage
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=agent-engine
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
```

### Deployment Command

```bash
python -m google.adk.cli deploy agent_engine \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --display_name="ai-agent-dual-export" \
  --otel_to_cloud \
  adk_agent
```

---

## 🌐 Access Points

### Google Cloud Console
**Agent List:**
https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716

**Specific Agent:**
https://console.cloud.google.com/vertex-ai/reasoning-engines/3691509684943978496?project=agentic-ai-integration-490716

### ngrok Web Interface
**URL:** http://localhost:4040
- Real-time request monitoring
- Request/response inspection
- Connection metrics: 49 active connections

### Docker Collector Logs
```bash
docker logs local-otel-collector -f
```

### Local Files
```bash
# View traces
cat otel-data/otel-traces.json | python -m json.tool

# View logs
cat otel-data/otel-logs.json | python -m json.tool

# View metrics
cat otel-data/otel-metrics.json | python -m json.tool
```

### Portal26 Dashboard
**URL:** https://portal26.in
**Filter:**
- service.name: ai-agent-engine
- tenant_id: tenant1
- user_id: relusys

---

## ✅ Testing the Agent

### Method 1: Google Cloud Console

1. Go to: https://console.cloud.google.com/vertex-ai/reasoning-engines/3691509684943978496?project=agentic-ai-integration-490716
2. Click on **Test** tab
3. Enter query: "What is the weather in Tokyo?"
4. Click **Send**
5. Watch telemetry at:
   - ngrok: http://localhost:4040
   - Local files: otel-data/
   - Portal26: https://portal26.in

### Method 2: REST API

```bash
TOKEN=$(gcloud auth print-access-token)

curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/3691509684943978496:streamQuery" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What is the weather in Tokyo?",
      "user_id": "test-user"
    }
  }'
```

### Method 3: Python SDK

```python
import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/3691509684943978496"
agent = reasoning_engines.ReasoningEngine(resource_name)

# Create session
session = agent.create_session(user_id="test-user")

# Query agent
response = agent.stream_query(
    message="What is the weather in Tokyo?",
    user_id="test-user"
)

for event in response:
    print(event)
```

---

## 📊 Telemetry Data Types

### Traces
- Span timing and duration
- Parent-child relationships
- Resource attributes
- Custom attributes (user.message, agent.success)

### Logs
- Structured log entries
- Trace context correlation
- Log levels and timestamps
- Application events

### Metrics
- Request counters (agent_requests_total)
- Response time histograms (agent_response_time_seconds)
- HTTP server metrics
- SDK metrics

---

## 🔧 Maintenance Commands

### Monitor Real-time Activity

```bash
# Watch collector logs
docker logs local-otel-collector -f

# Watch ngrok traffic
# Open: http://localhost:4040

# Monitor file sizes
watch -n 2 'ls -lh otel-data/'
```

### Restart Services

```bash
# Restart collector
docker-compose -f docker-compose-otel-collector.yml restart

# Restart ngrok (if needed)
# Press Ctrl+C in ngrok window, then:
ngrok http 4318
```

### Clean Data

```bash
# Backup first
cp -r otel-data otel-data-backup-$(date +%Y%m%d)

# Clear files
rm otel-data/*.json
```

---

## 🎯 Benefits Achieved

✅ **Local Visibility**
- All telemetry data available locally
- Debug in real-time without Portal26 login
- Offline access to historical data

✅ **Data Persistence**
- All data saved to local files
- No data loss if Portal26 is down
- Can analyze historical patterns

✅ **Multiple Backends**
- Data sent to both local files AND Portal26
- Can add more exporters (Jaeger, Prometheus, etc.)
- Flexible routing and filtering

✅ **Easy Debugging**
- Console output for immediate feedback
- File storage for detailed analysis
- ngrok UI for HTTP-level inspection

✅ **Data Processing**
- Can filter, transform, and sample data
- Add custom attributes
- Control what goes where

---

## 📝 File Structure

```
C:\Yesu\ai_agent_projectgcp\
├── adk_agent/                          # Agent source code
│   ├── __init__.py                     # OTEL bootstrap
│   ├── agent.py                        # Agent logic
│   ├── requirements.txt                # Dependencies
│   └── .env                            # Environment variables
├── otel-data/                          # Local telemetry data
│   ├── otel-traces.json                # Trace spans
│   ├── otel-logs.json                  # Log entries
│   └── otel-metrics.json               # Metrics data
├── otel-collector-config.yaml          # Collector configuration
├── docker-compose-otel-collector.yml   # Docker setup
├── deploy_adk_agent_engine.py          # Original deployment script
├── list_all_agents.py                  # List all agents
├── test_dual_export_agent.py           # Test script
└── DUAL_EXPORT_SUCCESS.md              # This document
```

---

## 🚀 Next Steps (Optional)

### Add More Agents

```bash
# Update .env with ngrok URL (already done)
# Deploy another agent
python -m google.adk.cli deploy agent_engine \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --display_name="agent-name" \
  --otel_to_cloud \
  adk_agent
```

### Add More Exporters

Edit `otel-collector-config.yaml`:

```yaml
exporters:
  jaeger:
    endpoint: localhost:14250
  prometheus:
    endpoint: "0.0.0.0:8889"
```

### Add Filtering/Sampling

```yaml
processors:
  filter/sample:
    traces:
      probabilistic_sampler:
        sampling_percentage: 50
```

---

## ✅ Success Verification

- ✅ Agent deployed successfully
- ✅ ngrok tunnel active (49 connections)
- ✅ Local collector running
- ✅ Local files updating (28KB logs, 3.4MB metrics)
- ✅ Portal26 forwarding active
- ✅ Console accessible
- ✅ Test queries working

---

## 🎉 Summary

**Status:** ✅ **FULLY OPERATIONAL**

You now have **7 Vertex AI Agent Engines** deployed, with **ai-agent-dual-export** configured for dual OTEL export:
- Local files for offline access and debugging
- Portal26 for centralized observability

All telemetry data from the agent is being captured in both locations simultaneously!

---

**Project:** agentic-ai-integration-490716
**Region:** us-central1
**ngrok URL:** https://tabetha-unelemental-bibulously.ngrok-free.dev
**Collector:** local-otel-collector (Docker)
**Data Location:** C:\Yesu\ai_agent_projectgcp\otel-data\
**Setup Date:** 2026-03-27
