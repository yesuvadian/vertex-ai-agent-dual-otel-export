# AI Agent with Dual Implementation

This project supports **two different agent implementations** that can be configured via `.env`:

## 🤖 Agent Types

### 1. **Manual Agent** (`agent_manual.py`)
- DIY implementation with manual tool orchestration
- Uses `google.generative_models.GenerativeModel`
- Tools: `get_weather()`, `get_order_status()`
- Full control over LLM calls and tool execution

### 2. **ADK Agent** (`agent.py`)
- Google Agent Development Kit (ADK) framework
- Uses `google.adk.agents.Agent` (if available)
- Tools: `get_weather()`, `get_current_time()`
- Framework handles orchestration automatically

## ⚙️ Configuration

Edit `.env` to choose which agent(s) to run:

```bash
# Option 1: Use AGENT_MODE (simple)
AGENT_MODE=manual    # Use only manual agent (default)
AGENT_MODE=adk       # Use only ADK agent
AGENT_MODE=both      # Run both agents in parallel

# Option 2: Individual toggles (advanced)
ENABLE_MANUAL_AGENT=true
ENABLE_ADK_AGENT=false
```

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Google Cloud
Update `.env` with your actual project ID:
```bash
GOOGLE_CLOUD_PROJECT=your-actual-project-id
```

### 3. Enable Required GCP APIs
- [Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)
- [Cloud Trace API](https://console.cloud.google.com/apis/library/cloudtrace.googleapis.com)
- [Cloud Resource Manager API](https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com)

### 4. Authenticate
```bash
gcloud auth application-default login
```

## 🏃 Running

### Start the API server:
```bash
uvicorn app:app --reload
```

### Endpoints:
- `GET /` - Service info and agent status
- `GET /status` - Current agent configuration
- `POST /chat` - Send messages to agent(s)

### Test it:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in New York?"}'
```

## 📊 Response Formats

### Single Agent Mode
```json
{
  "final_answer": "The weather in New York is sunny, 22°C..."
}
```

### Both Agents Mode
```json
{
  "mode": "both",
  "results": {
    "manual_agent": {
      "final_answer": "..."
    },
    "adk_agent": {
      "response": "..."
    }
  }
}
```

## 📁 File Structure
```
├── agent.py              # ADK agent (framework-based)
├── agent_manual.py       # Manual agent (DIY)
├── agent_router.py       # Router that switches between agents
├── app.py                # FastAPI application
├── telemetry.py          # OpenTelemetry setup
├── requirements.txt      # Python dependencies
└── .env                  # Configuration
```

## 🔍 Telemetry

Both agents include OpenTelemetry tracing:
- **Manual agent**: Custom spans for each LLM call and tool execution
- **ADK agent**: Framework-managed tracing + custom OTLP exporter

### Telemetry Backends

Configure via `.env` using `OTEL_TRACES_EXPORTER`:

**Option 1: OTLP (Portal26 or custom)**
```bash
OTEL_TRACES_EXPORTER=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64-credentials>
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1
```

**Option 2: GCP Cloud Trace**
```bash
OTEL_TRACES_EXPORTER=gcp_trace
GOOGLE_CLOUD_PROJECT=your-project-id
```

The system automatically configures the appropriate exporter based on the setting.

## 🛠️ Troubleshooting

**"No module named 'google.adk'"**
- The ADK is not yet publicly available
- Use `AGENT_MODE=manual` in `.env`

**"Vertex AI API not enabled"**
- Update `GOOGLE_CLOUD_PROJECT` in `.env` with real project ID
- Enable required APIs in GCP Console
- Run `gcloud auth application-default login`

**"Permission Denied"**
- Ensure your GCP account has Vertex AI User role
- Check that APIs are enabled for your project
