# ✅ Deployment Success!

**Date:** 2026-03-30 13:52
**Status:** 🟢 BOTH AGENTS DEPLOYED

---

## 📊 Deployed Agents

### 1. portal26GCPLocal

**Details:**
- **Name:** portal26GCPLocal
- **Resource ID:** 1402185738425991168
- **Package:** adk_agent_ngrok/
- **Service Name:** portal26GCPLocal
- **Model:** Gemini 2.0 Flash Exp

**OTEL Export:**
```
Agent → ngrok → Local OTEL Collector
                     ↓
         ┌───────────┼───────────┐
         ↓           ↓           ↓
    Portal26    Local Files   Console
```

**Endpoint:** `https://tabetha-unelemental-bibulously.ngrok-free.dev`

**Console URL:**
```
https://console.cloud.google.com/vertex-ai/reasoning-engines/1402185738425991168?project=agentic-ai-integration-490716
```

---

### 2. portal26GCPTel

**Details:**
- **Name:** portal26GCPTel
- **Resource ID:** 9130362698993762304
- **Package:** adk_agent_portal26/
- **Service Name:** portal26GCPTel
- **Model:** Gemini 2.0 Flash Exp

**OTEL Export:**
```
Agent → Portal26 Cloud (direct)
```

**Endpoint:** `https://otel-tenant1.portal26.in:4318`

**Console URL:**
```
https://console.cloud.google.com/vertex-ai/reasoning-engines/9130362698993762304?project=agentic-ai-integration-490716
```

---

## 🧪 Testing

### Test portal26GCPLocal

```bash
TOKEN=$(gcloud auth print-access-token)

curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/1402185738425991168:query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What is the weather in Tokyo?"
    }
  }'
```

**Monitor telemetry:**
- ngrok UI: http://localhost:4040
- Local files: `cat otel-data/otel-traces.json | jq .`
- Portal26: https://portal26.in (filter: `service.name=portal26GCPLocal`)

---

### Test portal26GCPTel

```bash
TOKEN=$(gcloud auth print-access-token)

curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/9130362698993762304:query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What is the weather in London?"
    }
  }'
```

**Monitor telemetry:**
- Portal26: https://portal26.in (filter: `service.name=portal26GCPTel`)

---

### Quick Test Script

Run the provided test script:

```bash
bash test_deployed_agents.sh
```

---

## 📊 Telemetry Architecture

### portal26GCPLocal (Dual Export)

```
Vertex AI Agent (portal26GCPLocal)
        ↓
        ↓ HTTPS POST (OTLP/HTTP)
        ↓
ngrok (https://tabetha-unelemental-bibulously.ngrok-free.dev)
        ↓
        ↓ Forward to localhost:4318
        ↓
Local OTEL Collector (Docker)
        ↓
        ├─→ Portal26 Cloud
        ├─→ Local Files (otel-data/)
        └─→ Console (debug)
```

**Benefits:**
- ✅ Local debugging with JSON files
- ✅ Offline access to telemetry
- ✅ Real-time monitoring via ngrok UI
- ✅ Multiple export destinations
- ✅ Data backup and persistence

---

### portal26GCPTel (Direct Export)

```
Vertex AI Agent (portal26GCPTel)
        ↓
        ↓ HTTPS POST (OTLP/HTTP)
        ↓
Portal26 Cloud (https://otel-tenant1.portal26.in:4318)
```

**Benefits:**
- ✅ Simple architecture
- ✅ No local infrastructure needed
- ✅ Lower latency (fewer hops)
- ✅ Direct cloud integration

---

## 📈 Resource Attributes

Both agents include these attributes:

```yaml
portal26.user.id: relusys
portal26.tenant_id: tenant1
service.version: 1.0
```

**portal26GCPLocal specific:**
```yaml
service.name: portal26GCPLocal
agent.type: ngrok-export
deployment.environment: agent-ngrok
```

**portal26GCPTel specific:**
```yaml
service.name: portal26GCPTel
agent.type: portal26-direct
deployment.environment: agent-portal26
```

---

## 🔍 Monitoring

### Google Cloud Console

**All agents:**
```
https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716
```

**Logs for portal26GCPLocal:**
```
https://console.cloud.google.com/logs/query?project=agentic-ai-integration-490716&query=resource.type%3D%22vertex_ai_reasoning_engine%22%20resource.labels.reasoning_engine_id%3D%221402185738425991168%22
```

**Logs for portal26GCPTel:**
```
https://console.cloud.google.com/logs/query?project=agentic-ai-integration-490716&query=resource.type%3D%22vertex_ai_reasoning_engine%22%20resource.labels.reasoning_engine_id%3D%229130362698993762304%22
```

### Portal26 Dashboard

**Access:** https://portal26.in

**Filter by agent:**
- portal26GCPLocal: `service.name="portal26GCPLocal"`
- portal26GCPTel: `service.name="portal26GCPTel"`

**Filter by tenant:**
- `portal26.tenant_id="tenant1"`

**Filter by user:**
- `portal26.user.id="relusys"`

### Local Monitoring (portal26GCPLocal only)

**ngrok Web UI:**
```
http://localhost:4040
```

**View requests in real-time:**
- Request count
- Response times
- Request/response payloads

**Local telemetry files:**
```bash
# Traces
cat otel-data/otel-traces.json | jq .

# Logs
cat otel-data/otel-logs.json | jq .

# Metrics
cat otel-data/otel-metrics.json | jq .
```

**Collector logs:**
```bash
docker logs local-otel-collector -f
```

---

## 🎯 Agent Tools

Both agents provide:

**get_weather(city: str)**
- Returns weather for: Bengaluru, New York, London, Tokyo
- Example: "What is the weather in Tokyo?"

**get_current_time(city: str)**
- Returns current time with timezone
- Example: "What time is it in London?"

---

## ✅ Verification Checklist

- [x] portal26GCPLocal deployed (Resource ID: 1402185738425991168)
- [x] portal26GCPTel deployed (Resource ID: 9130362698993762304)
- [ ] Test portal26GCPLocal with query
- [ ] Verify telemetry in ngrok UI (http://localhost:4040)
- [ ] Verify telemetry in local files (otel-data/)
- [ ] Verify telemetry in Portal26 (service.name=portal26GCPLocal)
- [ ] Test portal26GCPTel with query
- [ ] Verify telemetry in Portal26 (service.name=portal26GCPTel)

---

## 🔄 Update/Redeploy

To update agents, run the deployment scripts again:

```bash
# Update portal26GCPLocal
export PYTHONIOENCODING=utf-8
python -m google.adk.cli deploy agent_engine \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --display_name="portal26GCPLocal" \
  --otel_to_cloud \
  adk_agent_ngrok

# Update portal26GCPTel
export PYTHONIOENCODING=utf-8
python -m google.adk.cli deploy agent_engine \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --display_name="portal26GCPTel" \
  --otel_to_cloud \
  adk_agent_portal26
```

---

## 🎉 Success!

Both agents are now live and ready to use!

**Project:** agentic-ai-integration-490716
**Region:** us-central1
**Framework:** Google Agent Development Kit (ADK)
**Model:** Gemini 2.0 Flash Exp
**Deployment Date:** 2026-03-30
