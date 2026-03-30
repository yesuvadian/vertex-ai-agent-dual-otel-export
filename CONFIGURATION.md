# Configuration Guide

## ✅ Current Configuration

Your AI Agent system is now configured with:

### 🔧 GCP Project
```
Project ID: agentic-ai-integration-490716
```

### 📊 OpenTelemetry - Portal26
```
Endpoint: https://otel-tenant1.portal26.in:4318
Protocol: http/protobuf
Authentication: Basic Auth (configured)
User ID: relusys
Tenant ID: tenant1
```

### 🤖 Agent Mode
```
Mode: manual (using agent_manual.py)
Manual Agent: ✓ Enabled
ADK Agent: ✗ Disabled
```

## 📝 Environment Variables

All configuration is in `.env`:

```bash
# GCP Project
GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716

# OpenTelemetry - Portal26
OTEL_SERVICE_NAME=ai-agent
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==

# Exporters
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp

# Resource Attributes
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=dev

# Export Intervals
OTEL_METRIC_EXPORT_INTERVAL=1000
OTEL_LOGS_EXPORT_INTERVAL=500

# Sampling
OTEL_TRACES_SAMPLER=traceidratio
OTEL_TRACES_SAMPLER_ARG=1.0

# Additional Settings
OTEL_LOG_USER_PROMPTS=1

# Agent Configuration
AGENT_MODE=manual
ENABLE_MANUAL_AGENT=true
ENABLE_ADK_AGENT=false
```

## 🔄 Switching Telemetry Backends

### To use Portal26 (Current):
```bash
OTEL_TRACES_EXPORTER=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
```

### To use GCP Cloud Trace:
```bash
OTEL_TRACES_EXPORTER=gcp_trace
# No need for OTEL_EXPORTER_OTLP_ENDPOINT
```

### To disable telemetry:
```bash
OTEL_TRACES_EXPORTER=none
```

## 🔄 Switching Agent Modes

### Manual Agent Only (Current):
```bash
AGENT_MODE=manual
```

### ADK Agent Only:
```bash
AGENT_MODE=adk
```

### Both Agents (Parallel Execution):
```bash
AGENT_MODE=both
```

## 📊 Telemetry Data Flow

```
AI Agent
   ↓
OpenTelemetry SDK
   ↓
OTLP Exporter (http/protobuf)
   ↓
Portal26 Endpoint (https://otel-tenant1.portal26.in:4318)
   ↓
[Basic Auth: dGl0YW5pYW06aGVsbG93b3JsZA==]
   ↓
Traces stored with attributes:
  - portal26.user.id=relusys
  - portal26.tenant_id=tenant1
  - service.name=ai-agent
  - service.version=1.0
  - deployment.environment=dev
```

## 🚀 Next Steps

1. **Enable Vertex AI API** in GCP project `agentic-ai-integration-490716`:
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=agentic-ai-integration-490716
   ```

2. **Authenticate with GCP**:
   ```bash
   gcloud auth application-default login
   ```

3. **Start the server**:
   ```bash
   python -m uvicorn app:app --reload
   ```

4. **Verify telemetry** in Portal26 dashboard at:
   - https://otel-tenant1.portal26.in (check for traces from `ai-agent` service)

5. **Test the API**:
   ```bash
   python test_api.py
   ```

## 🔍 Monitoring

### Check Telemetry Status
```bash
curl http://localhost:8000/status
```

### View Traces in Portal26
- Login to Portal26 dashboard
- Navigate to tenant: `tenant1`
- Filter by user: `relusys`
- Service name: `ai-agent`

### Expected Trace Spans
- `agent_run` - Overall agent execution
- `llm_call` - Gemini API calls
- `tool:get_weather` - Weather tool execution
- `tool:get_order_status` - Order status tool execution
- `llm_final` - Final response generation

## ⚠️ Troubleshooting

### Telemetry not appearing in Portal26?
1. Verify endpoint is reachable: `curl -I https://otel-tenant1.portal26.in:4318`
2. Check Basic Auth credentials are correct
3. Verify tenant_id and user_id match Portal26 configuration
4. Check server logs for `[telemetry]` messages

### Vertex AI API errors?
1. Enable the API: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=agentic-ai-integration-490716
2. Authenticate: `gcloud auth application-default login`
3. Verify project ID in `.env` matches your GCP project

### Agent not responding?
1. Check agent mode: `AGENT_MODE=manual` should work immediately
2. For ADK mode, ensure `google-genai-adk` is installed
3. Check logs for import errors
