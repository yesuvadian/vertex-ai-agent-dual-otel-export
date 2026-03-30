# Two Agents with Different OTEL Export Destinations

This project contains **two separate ADK agent packages** that export telemetry to different destinations.

## 🤖 Agents

### 1. **portal26GCPLocal** (`adk_agent_ngrok/`)

Exports telemetry via **ngrok** to a **local OTEL collector**, which then forwards to multiple destinations.

```
Agent → ngrok → Local Collector → Portal26 + Local Files + Console
```

**Configuration:**
- **OTEL Endpoint:** `https://tabetha-unelemental-bibulously.ngrok-free.dev`
- **Service Name:** `portal26GCPLocal`
- **Agent Name:** `portal26GCPLocal`

**Benefits:**
- Local data persistence in JSON files
- Debug in real-time without cloud login
- Offline access to telemetry
- Can add more exporters (Jaeger, Prometheus, etc.)

---

### 2. **portal26GCPTel** (`adk_agent_portal26/`)

Exports telemetry **directly to Portal26 cloud** (no local collector).

```
Agent → Portal26 Cloud
```

**Configuration:**
- **OTEL Endpoint:** `https://otel-tenant1.portal26.in:4318`
- **Service Name:** `portal26GCPTel`
- **Agent Name:** `portal26GCPTel`

**Benefits:**
- Simpler architecture (no ngrok, no local collector)
- Direct cloud integration
- Lower latency (one less hop)
- Works without local infrastructure

---

## 📁 Project Structure

```
.
├── adk_agent_ngrok/           # Agent with ngrok export
│   ├── __init__.py            # OTEL bootstrap
│   ├── agent.py               # Agent: portal26GCPLocal
│   ├── requirements.txt       # Dependencies
│   └── .env                   # Config: ngrok endpoint
│
├── adk_agent_portal26/        # Agent with direct Portal26 export
│   ├── __init__.py            # OTEL bootstrap
│   ├── agent.py               # Agent: portal26GCPTel
│   ├── requirements.txt       # Dependencies
│   └── .env                   # Config: Portal26 endpoint
│
├── adk_agent/                 # Original reference agent
├── deploy_both_agents.py      # Deploy both agents
└── README.md                  # Main documentation
```

---

## 🚀 Deployment

### Deploy Both Agents

```bash
python deploy_both_agents.py
```

This will deploy:
1. `portal26GCPLocal` from `adk_agent_ngrok/`
2. `portal26GCPTel` from `adk_agent_portal26/`

### Deploy Individual Agents

**Deploy portal26GCPLocal (ngrok):**
```bash
python -m google.adk.cli deploy agent_engine \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --display_name="portal26GCPLocal" \
  --otel_to_cloud \
  adk_agent_ngrok
```

**Deploy portal26GCPTel (direct):**
```bash
python -m google.adk.cli deploy agent_engine \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --display_name="portal26GCPTel" \
  --otel_to_cloud \
  adk_agent_portal26
```

---

## ⚙️ Configuration Differences

| Aspect | portal26GCPLocal | portal26GCPTel |
|--------|------------------|----------------|
| **Package** | `adk_agent_ngrok/` | `adk_agent_portal26/` |
| **OTEL Endpoint** | ngrok URL | Portal26 URL |
| **Service Name** | `portal26GCPLocal` | `portal26GCPTel` |
| **Agent Type** | `ngrok-export` | `portal26-direct` |
| **Data Flow** | Agent → ngrok → Collector → Multiple destinations | Agent → Portal26 |
| **Local Files** | ✅ Yes (via collector) | ❌ No |
| **Requires ngrok** | ✅ Yes | ❌ No |
| **Requires Collector** | ✅ Yes | ❌ No |

---

## 🔍 Environment Variables

### portal26GCPLocal (`.env` in `adk_agent_ngrok/`)

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://tabetha-unelemental-bibulously.ngrok-free.dev
OTEL_SERVICE_NAME=portal26GCPLocal
OTEL_RESOURCE_ATTRIBUTES=agent.type=ngrok-export,...
```

### portal26GCPTel (`.env` in `adk_agent_portal26/`)

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_SERVICE_NAME=portal26GCPTel
OTEL_RESOURCE_ATTRIBUTES=agent.type=portal26-direct,...
```

---

## 🧪 Testing

After deployment, query both agents and observe telemetry:

### Query portal26GCPLocal
```bash
# This agent's telemetry goes through ngrok to local collector
curl -X POST "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/{RESOURCE_ID}:query" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -d '{"input": {"message": "What is the weather in Tokyo?"}}'
```

**Telemetry visible at:**
- ngrok UI: http://localhost:4040
- Local files: `otel-data/*.json`
- Portal26: https://portal26.in (filter: `service.name=portal26GCPLocal`)

### Query portal26GCPTel
```bash
# This agent's telemetry goes directly to Portal26
curl -X POST "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/{RESOURCE_ID}:query" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -d '{"input": {"message": "What is the weather in London?"}}'
```

**Telemetry visible at:**
- Portal26: https://portal26.in (filter: `service.name=portal26GCPTel`)

---

## 📊 Observability

### In Portal26 Dashboard

Filter by service name to see each agent separately:
- `service.name = "portal26GCPLocal"` → Shows ngrok-routed telemetry
- `service.name = "portal26GCPTel"` → Shows direct telemetry

### Resource Attributes

Both agents include:
```
portal26.user.id: relusys
portal26.tenant_id: tenant1
service.version: 1.0
```

**portal26GCPLocal** adds:
```
agent.type: ngrok-export
deployment.environment: agent-ngrok
```

**portal26GCPTel** adds:
```
agent.type: portal26-direct
deployment.environment: agent-portal26
```

---

## 🎯 Use Cases

### Use portal26GCPLocal when:
- You need local debugging and offline access
- You want to export to multiple backends
- You need data persistence and backup
- You're developing/testing locally

### Use portal26GCPTel when:
- You want simplest deployment
- You don't need local telemetry files
- You have reliable internet connection
- You prefer direct cloud integration

---

## 🔧 Troubleshooting

### portal26GCPLocal issues

**"Connection refused to ngrok"**
- Start ngrok: `ngrok http 4318`
- Update `.env` with new ngrok URL
- Restart local collector: `docker-compose -f docker-compose-otel-collector.yml restart`

**"No data in local files"**
- Check collector is running: `docker ps`
- Check collector logs: `docker logs local-otel-collector -f`

### portal26GCPTel issues

**"Connection timeout to Portal26"**
- Verify Portal26 endpoint is reachable
- Check authorization credentials in `.env`
- Verify firewall allows HTTPS to Portal26

---

## 📝 Summary

This project demonstrates **two different telemetry export patterns**:

1. **Local-first with cloud backup** (portal26GCPLocal) - Maximum observability
2. **Cloud-direct** (portal26GCPTel) - Minimum complexity

Both agents have identical functionality (weather and time tools) but differ only in how they export telemetry.

**Project:** agentic-ai-integration-490716
**Region:** us-central1
**Framework:** Google Agent Development Kit (ADK)
**Model:** Gemini 2.0 Flash Exp
