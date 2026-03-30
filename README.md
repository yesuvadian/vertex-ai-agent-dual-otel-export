# Portal26 Dual OTEL Agents

Two independent Vertex AI agents that send OpenTelemetry data to different endpoints.

## Agents

### 1. portal26_otel_agent
Sends telemetry to Portal26 OTEL endpoint
- Endpoint: https://otel-tenant1.portal26.in:4318
- Resource ID: `6507015916050448384`

### 2. portal26_ngrok_agent
Sends telemetry to ngrok local endpoint
- Endpoint: https://tabetha-unelemental-bibulously.ngrok-free.dev
- Resource ID: `6065663152568139776`

## Project Structure

```
.
├── portal26_otel_agent/       # Agent for Portal26 direct endpoint
├── portal26_ngrok_agent/      # Agent for ngrok local endpoint
├── test_portal26_otel_agent.py    # Test script for OTEL agent
├── test_portal26_ngrok_agent.py   # Test script for ngrok agent
└── DEPLOYMENT_STATUS.md       # Full deployment documentation
```

## Deploy

```bash
# Deploy OTEL agent
export PYTHONIOENCODING=utf-8
python -m google.adk.cli deploy agent_engine portal26_otel_agent \
  --project agentic-ai-integration-490716 \
  --region us-central1 \
  --otel_to_cloud

# Deploy ngrok agent
export PYTHONIOENCODING=utf-8
python -m google.adk.cli deploy agent_engine portal26_ngrok_agent \
  --project agentic-ai-integration-490716 \
  --region us-central1 \
  --otel_to_cloud
```

## Test

```bash
python test_portal26_otel_agent.py
python test_portal26_ngrok_agent.py
```

Check ngrok dashboard at http://localhost:4040 to see incoming telemetry.
