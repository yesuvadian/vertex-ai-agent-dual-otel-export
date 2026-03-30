# Vertex AI Agent Engine Deployment Guide

Complete guide for deploying your AI Agent to Vertex AI Agent Engine using the official Google Cloud method.

**Reference:** https://cloud.google.com/agent-builder/agent-engine/deploy

---

## 🎯 What is Vertex AI Agent Engine?

Vertex AI Agent Engine is a **managed service** that:
- Deploys AI agents as scalable API endpoints
- Handles infrastructure automatically
- Integrates with Vertex AI ecosystem
- Supports multiple frameworks (ADK, LangChain, LangGraph, Custom)
- Provides built-in monitoring and logging

---

## 📊 Comparison: Cloud Run vs Agent Engine

| Feature | Cloud Run (Current) | Agent Engine (New) |
|---------|---------------------|-------------------|
| **Type** | Container-based API | Managed Agent Service |
| **Control** | Full control | Managed by Google |
| **Setup** | Custom Dockerfile | Python source only |
| **OTEL** | Full integration ✅ | Partial support ⚠️ |
| **API Type** | REST (custom) | REST (generated) |
| **Scaling** | Container scaling | Agent scaling |
| **Best For** | Production APIs | Agent-specific workloads |

---

## 🚀 Quick Start

### Prerequisites

1. **Enable Vertex AI API:**
```bash
gcloud services enable aiplatform.googleapis.com
```

2. **Install SDK:**
```bash
pip install google-cloud-aiplatform[agent_engines] google-genai
```

3. **Authenticate:**
```bash
gcloud auth application-default login
```

### Deploy in 3 Steps

**Step 1: Test agent locally**
```bash
python agent_vertexai.py "What is the weather in Tokyo?"
```

**Step 2: Run deployment script**
```bash
python deploy_agent_engine.py
```

**Step 3: Query the deployed agent**
```python
from google import genai

client = genai.Client(vertexai=True, project="agentic-ai-integration-490716", location="us-central1")
remote_agent = client.agent_engines.get("RESOURCE_ID")

response = remote_agent.query(input="What is the weather in Tokyo?")
print(response)
```

---

## 📋 Deployment Methods

Vertex AI Agent Engine supports three deployment methods:

### Method 1: From Agent Object (Development)

**Best for:** Interactive development in notebooks

```python
from google import genai

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Deploy in-memory agent
remote_agent = client.agent_engines.create(
    agent=local_agent,  # Your agent object
    config={
        "requirements": ["google-genai", "requests"],
        "display_name": "My Agent",
        "env_vars": {"KEY": "VALUE"},
        "min_instances": 1,
        "max_instances": 10
    }
)
```

### Method 2: From Source Files (Recommended) ⭐

**Best for:** Production deployments, CI/CD

```python
remote_agent = client.agent_engines.create(
    config={
        "source_packages": ["."],  # Current directory
        "entrypoint_module": "agent_vertexai",
        "entrypoint_object": "query",
        "requirements": ["google-genai", "requests"],
        "display_name": "AI Agent",
        "env_vars": {
            "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
            "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel-tenant1.portal26.in:4318"
        },
        "min_instances": 0,
        "max_instances": 10,
        "resource_limits": {
            "cpu": "1",
            "memory": "2Gi"
        }
    }
)
```

### Method 3: From Developer Connect (Git Integration)

**Best for:** Team collaboration, version control

```python
remote_agent = client.agent_engines.create(
    config={
        "developer_connect_source": {
            "git_repository_link": "projects/PROJECT/locations/LOCATION/connections/CONN/gitRepositoryLinks/REPO",
            "revision": "main",
            "dir": "path/to/agent"
        },
        "entrypoint_module": "agent",
        "entrypoint_object": "root_agent",
        "requirements_file": "requirements.txt"
    }
)
```

---

## 🔧 Configuration Options

### Package Requirements

```python
requirements = [
    "google-cloud-aiplatform[agent_engines]>=1.70.0",
    "google-genai>=1.0.0",
    "requests>=2.31.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp-proto-http>=1.20.0",
]
```

### Environment Variables

```python
env_vars = {
    # Project configuration
    "GOOGLE_CLOUD_PROJECT": "agentic-ai-integration-490716",
    "GOOGLE_CLOUD_LOCATION": "us-central1",

    # OTEL configuration
    "OTEL_SERVICE_NAME": "ai-agent-engine",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel-tenant1.portal26.in:4318",
    "OTEL_TRACES_EXPORTER": "otlp",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_RESOURCE_ATTRIBUTES": "portal26.user.id=relusys,portal26.tenant_id=tenant1",

    # Secrets from Secret Manager
    "API_KEY": {
        "secret": "gemini-api-key",
        "version": "latest"
    }
}
```

### Resource Configuration

```python
config = {
    "min_instances": 0,  # Scale to zero when idle
    "max_instances": 10,  # Maximum scaling
    "resource_limits": {
        "cpu": "1",  # Options: 1, 2, 4, 6, 8
        "memory": "2Gi"  # Range: 1Gi to 32Gi
    },
    "container_concurrency": 3  # Recommended: 2*CPU + 1
}
```

---

## 📝 Complete Deployment Example

```python
#!/usr/bin/env python3
from google import genai

# Initialize client
client = genai.Client(
    vertexai=True,
    project="agentic-ai-integration-490716",
    location="us-central1"
)

# Define configuration
config = {
    # Metadata
    "display_name": "ai-agent-weather-time",
    "description": "AI Agent providing weather and time information",

    # Source code
    "source_packages": ["."],
    "entrypoint_module": "agent_vertexai",
    "entrypoint_object": "query",

    # Dependencies
    "requirements": [
        "google-cloud-aiplatform[agent_engines]>=1.70.0",
        "google-genai>=1.0.0",
        "requests>=2.31.0",
    ],

    # Environment
    "env_vars": {
        "GOOGLE_CLOUD_PROJECT": "agentic-ai-integration-490716",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel-tenant1.portal26.in:4318",
    },

    # Resources
    "min_instances": 0,
    "max_instances": 10,
    "resource_limits": {
        "cpu": "1",
        "memory": "2Gi"
    },
    "container_concurrency": 3
}

# Deploy
print("Deploying agent...")
remote_agent = client.agent_engines.create(config=config)

print(f"Deployed! Resource: {remote_agent.api_resource.name}")

# Test
response = remote_agent.query(input="What is the weather in Tokyo?")
print(f"Response: {response}")
```

---

## 🧪 Testing Deployed Agent

### Python SDK

```python
from google import genai

# Connect to deployed agent
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
remote_agent = client.agent_engines.get("RESOURCE_ID")

# Query
response = remote_agent.query(input="What is the weather in Tokyo?")
print(response)
```

### REST API

```bash
# Get access token
TOKEN=$(gcloud auth print-access-token)

# Query agent
curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/RESOURCE_ID:query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "What is the weather in Tokyo?"}'
```

### gcloud CLI

```bash
# List agents
gcloud ai reasoning-engines list --location=us-central1

# Describe agent
gcloud ai reasoning-engines describe RESOURCE_ID --location=us-central1

# Query agent (if supported)
gcloud ai reasoning-engines query RESOURCE_ID \
  --location=us-central1 \
  --input="What is the weather in Tokyo?"
```

---

## 📊 Monitoring & Observability

### Cloud Logging

```bash
# View agent logs
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.resource_id="RESOURCE_ID"' \
  --limit=50 \
  --format="table(timestamp,textPayload)"
```

### Portal26 Dashboard

1. Access: https://portal26.in
2. Login: titaniam / helloworld
3. Filter by:
   - Service: ai-agent-engine
   - Tenant: tenant1
   - User: relusys

### Cloud Console

View in Cloud Console:
```
https://console.cloud.google.com/vertex-ai/agent-engines/RESOURCE_ID?project=agentic-ai-integration-490716
```

---

## 🔐 Security & Secrets

### Using Secret Manager

```python
env_vars = {
    # Regular env var
    "PUBLIC_KEY": "value",

    # Secret from Secret Manager
    "API_KEY": {
        "secret": "gemini-api-key",  # Secret ID
        "version": "latest"  # or specific version number
    },

    "OTEL_HEADERS": {
        "secret": "otel-auth-header",
        "version": "1"
    }
}
```

### Create Secrets

```bash
# Create secret
echo -n "AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8" | \
  gcloud secrets create gemini-api-key --data-file=-

# Grant access to Agent Engine service account
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 🔄 Updating Deployed Agent

### Update Configuration

```python
# Get existing agent
remote_agent = client.agent_engines.get("RESOURCE_ID")

# Update configuration
updated_config = {
    "max_instances": 20,  # Increase scaling
    "env_vars": {
        "NEW_VAR": "value"
    }
}

# Apply update
remote_agent.update(config=updated_config)
```

### Redeploy New Version

```python
# Delete old version
client.agent_engines.delete("RESOURCE_ID")

# Deploy new version
new_agent = client.agent_engines.create(config=new_config)
```

---

## 💰 Cost Estimation

### Agent Engine Pricing

- **Compute:** Pay per vCPU-hour and GB-hour
- **Requests:** Pay per request processed
- **Storage:** Minimal costs for agent artifacts

**Estimated Monthly Cost:**
- Low traffic (< 1K requests/day): ~$10-30
- Medium traffic (1K-10K requests/day): ~$30-100
- High traffic (> 10K requests/day): ~$100-500

### Cost Optimization

```python
config = {
    "min_instances": 0,  # Scale to zero (saves cost)
    "max_instances": 10,  # Limit max scaling
    "resource_limits": {
        "cpu": "1",  # Start with minimal resources
        "memory": "2Gi"
    }
}
```

---

## 🆚 When to Use Agent Engine vs Cloud Run

### Use Agent Engine if:
- ✅ Building AI agent applications
- ✅ Want managed infrastructure
- ✅ Using Vertex AI ecosystem
- ✅ Need built-in versioning
- ✅ Prefer Python-only deployment

### Use Cloud Run if:
- ✅ Need full control over API
- ✅ Custom Docker containers
- ✅ Multiple languages/frameworks
- ✅ **Full OTEL integration required** (Current setup)
- ✅ Already have working REST API

### Use Both (Hybrid):
- ✅ Cloud Run for production REST API
- ✅ Agent Engine for internal agent workflows
- ✅ Best of both worlds

---

## 🚀 Deployment Workflow

```
┌──────────────────┐
│ Develop Locally  │
│ agent_vertexai.py│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Test Locally     │
│ python agent...  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Deploy to Agent  │
│ Engine           │
│ deploy_agent_... │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Test Deployed    │
│ Agent            │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Monitor & Scale  │
│ Cloud Console    │
└──────────────────┘
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Vertex AI API enabled
- [ ] Agent tested locally
- [ ] Requirements defined
- [ ] Environment variables configured
- [ ] Secrets created in Secret Manager

### Deployment
- [ ] Run `python deploy_agent_engine.py`
- [ ] Verify deployment successful
- [ ] Note Resource ID
- [ ] Test with sample query

### Post-Deployment
- [ ] Verify logs in Cloud Logging
- [ ] Check Portal26 dashboard
- [ ] Test REST API endpoint
- [ ] Set up monitoring alerts
- [ ] Document Resource ID

---

## 🔧 Troubleshooting

### Error: "API not enabled"
```bash
gcloud services enable aiplatform.googleapis.com
```

### Error: "Permission denied"
```bash
# Add Vertex AI User role
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="user:YOUR_EMAIL" \
  --role="roles/aiplatform.user"
```

### Error: "Module not found"
- Check `entrypoint_module` matches your file name
- Verify all dependencies in `requirements`
- Test locally first

### Error: "Deployment timeout"
- Large packages take longer
- Consider reducing dependencies
- Check quota limits

---

## 📚 Additional Resources

- **Official Docs:** https://cloud.google.com/agent-builder/agent-engine/deploy
- **Python SDK:** https://cloud.google.com/python/docs/reference/aiplatform/latest
- **Examples:** https://github.com/GoogleCloudPlatform/vertex-ai-samples
- **Support:** https://cloud.google.com/support

---

## ✅ Summary

**Vertex AI Agent Engine provides:**
- ✅ Managed agent deployment
- ✅ Automatic scaling
- ✅ Built-in monitoring
- ✅ Integration with Vertex AI

**Your Options:**
1. **Keep Cloud Run** - Full control + complete OTEL ✅
2. **Add Agent Engine** - Managed agent service 🆕
3. **Use Both** - Hybrid approach (recommended)

**Recommendation:** Deploy to **both** for different use cases!

---

**Last Updated:** 2026-03-27
**Version:** 1.0 (Based on official Google Cloud documentation)
