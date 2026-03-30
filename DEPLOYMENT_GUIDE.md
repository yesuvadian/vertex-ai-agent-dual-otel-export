# Deployment Guide

This guide explains how to deploy the two agents with different OTEL export destinations.

## 📦 Available Agents

| Agent Name | Deployment Script | Package | OTEL Endpoint |
|------------|------------------|---------|---------------|
| **portal26GCPLocal** | `deploy_portal26GCPLocal.py` | `adk_agent_ngrok/` | ngrok tunnel |
| **portal26GCPTel** | `deploy_portal26GCPTel.py` | `adk_agent_portal26/` | Portal26 direct |

---

## 🚀 Quick Start

### Option 1: Deploy Both Agents (Sequential)

```bash
python deploy_both_agents.py
```

This will deploy both agents one after the other with a 15-second delay between deployments.

### Option 2: Deploy Individual Agents

**Deploy portal26GCPLocal (ngrok export):**
```bash
python deploy_portal26GCPLocal.py
```

**Deploy portal26GCPTel (direct Portal26 export):**
```bash
python deploy_portal26GCPTel.py
```

---

## 📋 Prerequisites

### 1. Google Cloud Setup

```bash
# Authenticate
gcloud auth application-default login

# Set project
gcloud config set project agentic-ai-integration-490716

# Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudtrace.googleapis.com
```

### 2. Install Google ADK

```bash
pip install google-genai[adk]
```

### 3. Configure Environment Files

**For portal26GCPLocal (adk_agent_ngrok/.env):**
```bash
cd adk_agent_ngrok
cp .env.example .env
# Edit .env and set:
# - GOOGLE_CLOUD_PROJECT
# - OTEL_EXPORTER_OTLP_ENDPOINT (ngrok URL)
# - OTEL_EXPORTER_OTLP_HEADERS (auth credentials)
```

**For portal26GCPTel (adk_agent_portal26/.env):**
```bash
cd adk_agent_portal26
cp .env.example .env
# Edit .env and set:
# - GOOGLE_CLOUD_PROJECT
# - OTEL_EXPORTER_OTLP_HEADERS (auth credentials)
```

### 4. Additional Setup for portal26GCPLocal

This agent requires local infrastructure:

**Start OTEL Collector:**
```bash
docker-compose -f docker-compose-otel-collector.yml up -d
```

**Start ngrok tunnel:**
```bash
ngrok http 4318
```

**Update .env with ngrok URL:**
```bash
# Get ngrok URL (e.g., https://abc123.ngrok-free.dev)
# Update adk_agent_ngrok/.env:
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-ngrok-url.ngrok-free.dev
```

---

## 🔍 Deployment Details

### portal26GCPLocal Deployment

**Command:**
```bash
python deploy_portal26GCPLocal.py
```

**What it does:**
1. Packages `adk_agent_ngrok/` directory
2. Uploads to Google Cloud Storage
3. Creates Vertex AI Agent Engine instance
4. Configures environment variables from `.env`
5. Agent starts sending telemetry to ngrok URL

**Telemetry Flow:**
```
Agent → ngrok → Local Collector → Portal26 + Local Files + Console
```

**Verify deployment:**
```bash
# Check ngrok traffic
open http://localhost:4040

# Check local files
ls -lh otel-data/

# Check collector logs
docker logs local-otel-collector -f
```

---

### portal26GCPTel Deployment

**Command:**
```bash
python deploy_portal26GCPTel.py
```

**What it does:**
1. Packages `adk_agent_portal26/` directory
2. Uploads to Google Cloud Storage
3. Creates Vertex AI Agent Engine instance
4. Configures environment variables from `.env`
5. Agent starts sending telemetry directly to Portal26

**Telemetry Flow:**
```
Agent → Portal26 Cloud
```

**Verify deployment:**
```bash
# Check Portal26 dashboard
open https://portal26.in
# Filter by: service.name = "portal26GCPTel"
```

---

## 🧪 Testing Deployed Agents

### Get Agent Resource ID

After deployment, note the Resource ID from the output or list all agents:

```bash
gcloud ai agent-engines list \
  --project=agentic-ai-integration-490716 \
  --region=us-central1
```

### Test portal26GCPLocal

```bash
RESOURCE_ID="<your-resource-id>"
TOKEN=$(gcloud auth print-access-token)

curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/${RESOURCE_ID}:query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What is the weather in Tokyo?"
    }
  }'
```

**Check telemetry:**
- ngrok UI: http://localhost:4040
- Local files: `cat otel-data/otel-traces.json | jq .`
- Portal26: https://portal26.in (filter: `service.name=portal26GCPLocal`)

### Test portal26GCPTel

```bash
RESOURCE_ID="<your-resource-id>"
TOKEN=$(gcloud auth print-access-token)

curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/${RESOURCE_ID}:query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What is the weather in London?"
    }
  }'
```

**Check telemetry:**
- Portal26: https://portal26.in (filter: `service.name=portal26GCPTel`)

---

## 🐛 Troubleshooting

### portal26GCPLocal Issues

**"Connection refused to ngrok"**
```bash
# Check ngrok is running
ps aux | grep ngrok

# Restart ngrok
ngrok http 4318

# Update .env with new URL
```

**"Collector not receiving data"**
```bash
# Check collector is running
docker ps | grep otel-collector

# Check collector logs
docker logs local-otel-collector -f

# Restart collector
docker-compose -f docker-compose-otel-collector.yml restart
```

**"No data in local files"**
```bash
# Check volume mount
docker inspect local-otel-collector | grep Mounts -A 10

# Check file permissions
ls -la otel-data/

# Check collector config
cat otel-collector-config.yaml
```

### portal26GCPTel Issues

**"Connection timeout to Portal26"**
```bash
# Test connectivity
curl -v https://otel-tenant1.portal26.in:4318/v1/traces

# Check firewall rules
gcloud compute firewall-rules list

# Verify credentials in .env
echo $OTEL_EXPORTER_OTLP_HEADERS
```

### General Issues

**"Permission denied"**
```bash
# Check GCP permissions
gcloud projects get-iam-policy agentic-ai-integration-490716 \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"
```

**"API not enabled"**
```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudtrace.googleapis.com
```

**"Deployment timeout"**
- Check network connectivity
- Verify GCP project is valid
- Try deploying from Cloud Shell

---

## 📊 Monitoring

### Google Cloud Console

**View all agents:**
```
https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716
```

**View specific agent:**
```
https://console.cloud.google.com/vertex-ai/reasoning-engines/{RESOURCE_ID}?project=agentic-ai-integration-490716
```

### Portal26 Dashboard

**Access:**
```
https://portal26.in
```

**Filter by agent:**
- portal26GCPLocal: `service.name = "portal26GCPLocal"`
- portal26GCPTel: `service.name = "portal26GCPTel"`

### Local Monitoring (portal26GCPLocal only)

**ngrok Web UI:**
```
http://localhost:4040
```

**Collector logs:**
```bash
docker logs local-otel-collector -f
```

**Local telemetry files:**
```bash
# Traces
cat otel-data/otel-traces.json | jq .

# Logs
cat otel-data/otel-logs.json | jq .

# Metrics
cat otel-data/otel-metrics.json | jq .
```

---

## 🔄 Update/Redeploy

To update an agent, simply run the deployment script again:

```bash
# Update portal26GCPLocal
python deploy_portal26GCPLocal.py

# Update portal26GCPTel
python deploy_portal26GCPTel.py
```

The deployment will create a new version of the agent.

---

## 🗑️ Cleanup

### Delete Agents

```bash
# List agents
gcloud ai agent-engines list \
  --project=agentic-ai-integration-490716 \
  --region=us-central1

# Delete specific agent
gcloud ai agent-engines delete {RESOURCE_ID} \
  --project=agentic-ai-integration-490716 \
  --region=us-central1
```

### Stop Local Infrastructure (portal26GCPLocal)

```bash
# Stop collector
docker-compose -f docker-compose-otel-collector.yml down

# Stop ngrok
# Press Ctrl+C in ngrok terminal
```

---

## 📚 Additional Resources

- **TWO_AGENTS_README.md** - Detailed agent documentation
- **README.md** - Project overview
- **Google ADK Docs** - https://cloud.google.com/vertex-ai/docs/adk
- **OpenTelemetry** - https://opentelemetry.io/docs/

---

**Project:** agentic-ai-integration-490716
**Region:** us-central1
**Framework:** Google Agent Development Kit (ADK)
**Model:** Gemini 2.0 Flash Exp
