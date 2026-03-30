# Deployment Guide - Google Cloud Run

This guide will help you deploy your AI Agent to Google Cloud Run for production use.

## 📋 Prerequisites

- [x] Google Cloud Project: `agentic-ai-integration-490716`
- [x] gcloud CLI installed
- [x] Docker Desktop (optional, Cloud Build will handle this)
- [x] API key configured in `.env`

## 🚀 Quick Deploy

### Option 1: Automated Script (Recommended)

**Windows:**
```bash
deploy.bat
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Deployment

Follow the steps below for manual deployment.

---

## 📖 Manual Deployment Steps

### Step 1: Verify Prerequisites

```bash
# Check gcloud is installed
gcloud --version

# Authenticate if needed
gcloud auth login

# Set project
gcloud config set project agentic-ai-integration-490716
```

### Step 2: Enable Required APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    generativelanguage.googleapis.com
```

### Step 3: Build Container Image

```bash
# Build using Cloud Build (no local Docker needed)
gcloud builds submit --tag gcr.io/agentic-ai-integration-490716/ai-agent

# OR build locally with Docker (if you have Docker Desktop)
docker build -t gcr.io/agentic-ai-integration-490716/ai-agent .
docker push gcr.io/agentic-ai-integration-490716/ai-agent
```

### Step 4: Deploy to Cloud Run

```bash
gcloud run deploy ai-agent \
    --image gcr.io/agentic-ai-integration-490716/ai-agent \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716" \
    --set-env-vars="GOOGLE_CLOUD_LOCATION=us-central1" \
    --set-env-vars="GOOGLE_CLOUD_API_KEY=YOUR_API_KEY_HERE" \
    --set-env-vars="OTEL_SERVICE_NAME=ai-agent" \
    --set-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318" \
    --set-env-vars="OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf" \
    --set-env-vars="OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
    --set-env-vars="OTEL_TRACES_EXPORTER=otlp" \
    --set-env-vars="OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=production" \
    --set-env-vars="AGENT_MODE=manual" \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 300
```

### Step 5: Get Service URL

```bash
gcloud run services describe ai-agent \
    --region us-central1 \
    --format='value(status.url)'
```

---

## 🧪 Test Your Deployment

Once deployed, you'll get a URL like: `https://ai-agent-xxxxx-uc.a.run.app`

### Test Status Endpoint

```bash
curl https://ai-agent-xxxxx-uc.a.run.app/status
```

**Expected response:**
```json
{
  "agent_mode": "manual",
  "manual_agent_enabled": true,
  "adk_agent_enabled": false
}
```

### Test Weather Query

```bash
curl -X POST https://ai-agent-xxxxx-uc.a.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Paris?"}'
```

**Expected response:**
```json
{
  "final_answer": "The weather in Paris is 28°C and sunny."
}
```

### Test Order Status

```bash
curl -X POST https://ai-agent-xxxxx-uc.a.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order XYZ123?"}'
```

---

## 📊 Monitor Your Deployment

### Cloud Run Console

View your service:
https://console.cloud.google.com/run?project=agentic-ai-integration-490716

### Logs

```bash
# View logs
gcloud run services logs read ai-agent --region us-central1

# Follow logs (real-time)
gcloud run services logs tail ai-agent --region us-central1
```

### Portal26 Telemetry

Your traces will appear in Portal26 with:
- Service: `ai-agent`
- Environment: `production`
- User: `relusys`
- Tenant: `tenant1`

---

## ⚙️ Configuration

### Environment Variables

The deployment includes these environment variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| `GOOGLE_CLOUD_PROJECT` | agentic-ai-integration-490716 | GCP project |
| `GOOGLE_CLOUD_API_KEY` | From .env | Gemini API authentication |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Portal26 URL | Telemetry endpoint |
| `OTEL_RESOURCE_ATTRIBUTES` | portal26.user.id=relusys | Telemetry tags |
| `AGENT_MODE` | manual | Which agent to use |

### Update Environment Variables

```bash
gcloud run services update ai-agent \
    --region us-central1 \
    --set-env-vars="AGENT_MODE=both"
```

---

## 🔄 Update/Redeploy

To deploy a new version after code changes:

```bash
# Rebuild and deploy in one command
gcloud builds submit --tag gcr.io/agentic-ai-integration-490716/ai-agent && \
gcloud run deploy ai-agent \
    --image gcr.io/agentic-ai-integration-490716/ai-agent \
    --region us-central1
```

---

## 💰 Cost Estimates

Cloud Run pricing (as of 2024):

**Free Tier:**
- 2 million requests/month
- 360,000 GB-seconds/month
- 180,000 vCPU-seconds/month

**Estimated Costs (beyond free tier):**
- Requests: $0.40 per million requests
- Memory: $0.0000025 per GB-second
- CPU: $0.00002400 per vCPU-second

**Your Configuration:**
- 512 MB memory
- 1 vCPU
- ~2-3 seconds per request

**Example:**
- 10,000 requests/month = **FREE** (within free tier)
- 100,000 requests/month = ~$5-10/month
- 1,000,000 requests/month = ~$50-100/month

---

## 🔒 Security

### Authentication

Currently deployed with `--allow-unauthenticated` for easy testing.

**To add authentication:**

```bash
# Require authentication
gcloud run services update ai-agent \
    --region us-central1 \
    --no-allow-unauthenticated

# Create service account for access
gcloud iam service-accounts create ai-agent-client

# Grant invoker role
gcloud run services add-iam-policy-binding ai-agent \
    --region us-central1 \
    --member="serviceAccount:ai-agent-client@agentic-ai-integration-490716.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### API Key Security

**⚠️ Important:** Never commit your API key to git!

- API keys are set as environment variables (not in code)
- Use Secret Manager for production (recommended)

**Using Secret Manager:**

```bash
# Create secret
echo -n "YOUR_API_KEY" | gcloud secrets create ai-agent-api-key --data-file=-

# Deploy with secret
gcloud run deploy ai-agent \
    --image gcr.io/agentic-ai-integration-490716/ai-agent \
    --region us-central1 \
    --set-secrets="GOOGLE_CLOUD_API_KEY=ai-agent-api-key:latest"
```

---

## 🐛 Troubleshooting

### Build Fails

**Error:** "permission denied"
```bash
# Ensure Cloud Build API is enabled
gcloud services enable cloudbuild.googleapis.com
```

### Deployment Fails

**Error:** "Service account does not have required permissions"
```bash
# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
    --member="user:YOUR_EMAIL@gmail.com" \
    --role="roles/run.admin"
```

### Service Returns 500 Error

```bash
# Check logs
gcloud run services logs read ai-agent --region us-central1 --limit 50

# Common issues:
# - API key not set or invalid
# - Missing environment variables
# - Generative Language API not enabled
```

### Cold Start Issues

First request after idle may be slow (2-5 seconds).

**Solution:** Set minimum instances:
```bash
gcloud run services update ai-agent \
    --region us-central1 \
    --min-instances 1
```

Note: This will increase costs (always running).

---

## 📈 Scaling

Cloud Run auto-scales based on traffic:

- **Default:** 0-1000 instances
- **Concurrency:** 80 requests per instance
- **Current setting:** Max 10 instances

**Adjust scaling:**

```bash
gcloud run services update ai-agent \
    --region us-central1 \
    --min-instances 1 \
    --max-instances 100 \
    --concurrency 50
```

---

## 🔗 Useful Links

- **Cloud Run Console**: https://console.cloud.google.com/run?project=agentic-ai-integration-490716
- **Cloud Build History**: https://console.cloud.google.com/cloud-build/builds?project=agentic-ai-integration-490716
- **Container Registry**: https://console.cloud.google.com/gcr/images/agentic-ai-integration-490716?project=agentic-ai-integration-490716
- **Logs**: https://console.cloud.google.com/logs?project=agentic-ai-integration-490716
- **Metrics**: https://console.cloud.google.com/monitoring?project=agentic-ai-integration-490716

---

## ✅ Deployment Checklist

- [ ] gcloud CLI installed and authenticated
- [ ] Required APIs enabled
- [ ] `.env` file configured with API key
- [ ] Container image built successfully
- [ ] Service deployed to Cloud Run
- [ ] Service URL obtained
- [ ] Status endpoint tested
- [ ] Chat endpoint tested with sample query
- [ ] Telemetry visible in Portal26
- [ ] Logs checked for errors
- [ ] Documentation updated with service URL

---

**Ready to deploy? Run `deploy.bat` (Windows) or `./deploy.sh` (Linux/Mac)!** 🚀
