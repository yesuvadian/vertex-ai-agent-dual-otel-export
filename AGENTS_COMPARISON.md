# Agent Comparison - Telemetry Destinations

This project has **3 agents** demonstrating different telemetry export patterns:

---

## Agent 1: portal26_ngrok_agent

**Telemetry Flow:** Agent → Ngrok → Local Receiver → Portal26 + JSON files

**Key Features:**
- Custom OTEL tracer provider
- Exports to ngrok endpoint (local receiver)
- Local receiver forwards to Portal26 with authentication
- Saves JSON files locally for debugging

**Configuration:**
```env
OTEL_EXPORTER_OTLP_ENDPOINT=https://tabetha-unelemental-bibulously.ngrok-free.dev
OTEL_SERVICE_NAME=portal26_ngrok_agent
```

**Use Case:** Development/testing with local visibility and Portal26 export

**Files:**
- `portal26_ngrok_agent/agent.py` - Custom OTEL setup
- `portal26_ngrok_agent/.env` - Ngrok endpoint
- `local_otel_receiver.py` - Receiver that forwards to Portal26

---

## Agent 2: portal26_otel_agent

**Telemetry Flow:** Agent → Portal26 (direct)

**Key Features:**
- Custom OTEL tracer provider
- Direct export to Portal26 endpoint
- Includes Portal26 authentication headers
- No intermediate receiver needed

**Configuration:**
```env
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_SERVICE_NAME=portal26_otel_agent
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1
```

**Use Case:** Production deployment with direct Portal26 integration

**Files:**
- `portal26_otel_agent/agent.py` - Custom OTEL setup
- `portal26_otel_agent/.env` - Portal26 endpoint + auth

---

## Agent 3: gcp_traces_agent

**Telemetry Flow:** Agent → Google Cloud Trace (default)

**Key Features:**
- NO custom OTEL setup
- Uses GCP's built-in Cloud Trace automatically
- Traces visible in GCP Console
- No additional configuration needed

**Configuration:**
```env
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
OTEL_SERVICE_NAME=gcp_traces_agent
# NO OTEL_EXPORTER_OTLP_ENDPOINT - uses GCP default
```

**Use Case:** Standard GCP deployment using native Cloud Trace

**View Traces:**
- Go to: https://console.cloud.google.com/traces
- Project: agentic-ai-integration-490716
- Filter by service: gcp_traces_agent

**Files:**
- `gcp_traces_agent/agent.py` - No OTEL customization
- `gcp_traces_agent/.env` - Basic GCP settings only

---

## Comparison Matrix

| Feature | portal26_ngrok_agent | portal26_otel_agent | gcp_traces_agent |
|---------|---------------------|---------------------|------------------|
| **Destination** | Local + Portal26 | Portal26 | GCP Cloud Trace |
| **Custom OTEL** | ✓ Yes | ✓ Yes | ✗ No (GCP default) |
| **Authentication** | Via receiver | In .env | N/A (GCP handles) |
| **JSON Files** | ✓ Yes | ✗ No | ✗ No |
| **Development** | ✓ Best | Good | Good |
| **Production** | Limited | ✓ Best | ✓ Best (GCP) |
| **Complexity** | High | Medium | Low |

---

## How to Test Each Agent

### Testing portal26_ngrok_agent

1. Start local receiver: `python local_otel_receiver.py`
2. Start ngrok: `ngrok http 4318`
3. Query agent via GCP Console
4. Check `otel-data/*.json` for traces
5. Check Portal26 dashboard

### Testing portal26_otel_agent

1. Query agent via GCP Console
2. Check Portal26 dashboard:
   - Filter: tenant1, relusys
   - Service: portal26_otel_agent

### Testing gcp_traces_agent

1. Query agent via GCP Console
2. Go to: https://console.cloud.google.com/traces?project=agentic-ai-integration-490716
3. Filter by service: gcp_traces_agent
4. View traces in Cloud Trace UI

---

## Deployment Status

Run this to check deployment:
```bash
gcloud ai agent-engines list --region=us-central1 --project=agentic-ai-integration-490716
```

---

## When to Use Which Agent

**Use portal26_ngrok_agent when:**
- Developing locally
- Need to inspect JSON trace data
- Testing Portal26 integration
- Want local debugging

**Use portal26_otel_agent when:**
- Deploying to production
- Need direct Portal26 export
- Want simplest Portal26 integration
- Don't need local trace files

**Use gcp_traces_agent when:**
- Want standard GCP telemetry
- Using GCP Cloud Trace for monitoring
- Don't need external telemetry system
- Want simplest configuration

---

**Current Project:** All 3 agents are deployed to demonstrate different telemetry patterns.
