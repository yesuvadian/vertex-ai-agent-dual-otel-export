# Vertex AI Agent with Dual OpenTelemetry Export

A Google ADK (Agent Development Kit) agent package with dual OpenTelemetry export capability - sends telemetry to both local files and Portal26 cloud simultaneously.

## 🏗️ Architecture

```
Vertex AI Agent → ngrok Tunnel → Local OTEL Collector
                                        ↓
                        ┌───────────────┼───────────────┐
                        ↓               ↓               ↓
                  Local Files      Portal26        Console
                  (JSON files)     (Cloud)         (Debug)
```

## 📁 Package Structure

```
adk_agent/
├── __init__.py         # OTEL bootstrap - adds custom OTLP exporter
├── agent.py            # Agent definition with tools and CustomAdkApp
├── requirements.txt    # Dependencies for deployment
└── .env               # Environment configuration (OTEL endpoints, credentials)
```

## 🚀 Quick Start

### 1. Configure Environment

Edit `adk_agent/.env`:

```bash
# Google Cloud
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# OTEL Export (Dual: Local Collector + Portal26)
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-ngrok-url.ngrok-free.dev
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64-credentials>
OTEL_SERVICE_NAME=ai-agent-engine

# Resource Attributes
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=your-user,portal26.tenant_id=your-tenant,service.version=1.0
```

### 2. Deploy to Vertex AI

```bash
python -m google.adk.cli deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --display_name="my-dual-export-agent" \
  --otel_to_cloud \
  adk_agent
```

### 3. Set Up Local Collector (Optional)

For local telemetry collection, you need:
- Docker with OTEL Collector
- ngrok tunnel pointing to collector
- Collector configured to export to Portal26 + local files

## 🔍 Key Features

### Custom OTLP Exporter (`__init__.py`)

Automatically adds OTLP exporter when agent package initializes:
- Reads `OTEL_EXPORTER_OTLP_ENDPOINT` from environment
- Parses authorization headers
- Creates `OTLPSpanExporter` with `BatchSpanProcessor`
- Adds to existing trace provider (doesn't replace ADK's default)

### Agent Tools (`agent.py`)

**get_weather(city: str)**
- Returns mock weather data for cities
- Supports: Bengaluru, New York, London

**get_current_time(city: str)**
- Returns current time in city's timezone
- Supports: Bengaluru, New York, London, Tokyo

### Custom App Hook

`CustomAdkApp` extends `AdkApp` with:
- `set_up()` method that adds custom exporter after ADK initialization
- Ensures dual export: ADK's cloud trace + custom OTLP endpoint

## 📊 Telemetry Signals

All three OTEL signals are exported:

- **Traces**: Span timing, parent-child relationships, attributes
- **Logs**: Structured logs with trace correlation
- **Metrics**: Request counters, response time histograms

## 🔧 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | `https://example.ngrok-free.dev` |
| `OTEL_EXPORTER_OTLP_HEADERS` | Auth headers (comma-separated) | `Authorization=Basic xxx` |
| `OTEL_SERVICE_NAME` | Service identifier | `ai-agent-engine` |
| `OTEL_RESOURCE_ATTRIBUTES` | Resource metadata | `user.id=x,tenant_id=y` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `my-project-123` |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |

## 📖 How It Works

1. **Bootstrap**: `__init__.py` runs on import, adds OTLP exporter
2. **Setup**: `CustomAdkApp.set_up()` ensures exporter added after ADK init
3. **Execution**: Agent processes requests, OTEL auto-instruments
4. **Export**: Telemetry sent to configured OTLP endpoint
5. **Collection**: Local collector receives, routes to multiple destinations

## 🎯 Use Cases

- **Development**: Debug telemetry locally before sending to cloud
- **Compliance**: Keep local copy of all telemetry data
- **Reliability**: Continue collecting if cloud backend is down
- **Analysis**: Query local JSON files with standard tools

## 📝 License

MIT

## 🤝 Contributing

This is a reference implementation for dual OTEL export with Google ADK agents.

---

**Project:** Vertex AI Agent with Dual OpenTelemetry Export
**Framework:** Google Agent Development Kit (ADK)
**Model:** Gemini 2.5 Flash
**Telemetry:** OpenTelemetry (OTLP/HTTP)
