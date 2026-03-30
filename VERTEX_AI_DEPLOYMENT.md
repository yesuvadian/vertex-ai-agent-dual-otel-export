# Deploying AI Agent to Vertex AI

Complete guide for deploying to Vertex AI instead of Cloud Run.

---

## 🔄 Deployment Options Comparison

| Feature | Cloud Run (Current) | Vertex AI Reasoning Engine |
|---------|---------------------|----------------------------|
| **Type** | REST API Service | Managed Agent Service |
| **Control** | Full control | Managed by Google |
| **Scaling** | Auto-scaling HTTP | Managed execution |
| **Endpoints** | Custom FastAPI endpoints | Query API |
| **OTEL Integration** | Full control | Limited |
| **Cost** | Pay per request | Pay per query |
| **Setup Complexity** | Medium | Low |
| **Best For** | Production APIs | Prototyping, managed agents |

---

## 📊 Current Architecture (Cloud Run)

```
User Request (HTTP)
    ↓
FastAPI Application (Cloud Run)
    ↓
Agent Router
    ↓
Manual Agent / ADK Agent
    ↓
Gemini API
    ↓
OTEL → Portal26
```

**Pros:**
- ✅ Full control over API endpoints
- ✅ Complete OTEL integration
- ✅ Custom middleware and authentication
- ✅ Can combine multiple agents
- ✅ Works with existing monitoring

**Cons:**
- ⚠️ Need to manage infrastructure
- ⚠️ More code to maintain

---

## 🚀 Vertex AI Architecture (Reasoning Engine)

```
User Request (SDK/API)
    ↓
Vertex AI Reasoning Engine
    ↓
Agent Code
    ↓
Gemini API
    ↓
Response
```

**Pros:**
- ✅ Managed service (less infrastructure)
- ✅ Built-in versioning
- ✅ Integrated with Vertex AI ecosystem
- ✅ Simple deployment

**Cons:**
- ⚠️ Less control over execution
- ⚠️ Limited OTEL integration
- ⚠️ Not a REST API (SDK-based)
- ⚠️ Preview API (less stable)

---

## 🎯 Recommendation

### Use Cloud Run (Current) if you need:
- Production-ready REST API
- Full observability with Portal26
- Custom endpoints and middleware
- Integration with existing systems
- High control over infrastructure

### Use Vertex AI if you need:
- Rapid prototyping
- Managed agent service
- Integration with Vertex AI tools
- Less infrastructure management
- SDK-based access only

---

## 📦 Option 1: Keep Cloud Run (Recommended)

Your current Cloud Run deployment is **production-ready** and has:

✅ Full OTEL integration with Portal26
✅ REST API endpoints
✅ Automated deployment
✅ Proven working architecture

**No changes needed!**

---

## 📦 Option 2: Deploy to Vertex AI Reasoning Engine

### Prerequisites

```bash
# Install Vertex AI SDK
pip install google-cloud-aiplatform

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Create staging bucket
gsutil mb -p agentic-ai-integration-490716 \
  -c STANDARD -l us-central1 \
  gs://agentic-ai-integration-490716-reasoning-engine
```

### Step 1: Test Agent Locally

```bash
# Test the Vertex AI agent locally
python agent_vertexai.py "What is the weather in Tokyo?"
```

Expected output:
```
Query: What is the weather in Tokyo?

Response: The weather in Tokyo is sunny, 28°C with clear skies.
```

### Step 2: Deploy to Reasoning Engine

**Note:** Vertex AI Reasoning Engine is currently in Preview and has limitations.

**Option A: Use Cloud Function with Vertex AI Agent**

This gives you the benefits of both - managed infrastructure + your agent code:

```bash
# Deploy as Cloud Function
gcloud functions deploy ai-agent-vertexai \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=query \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716" \
  --set-env-vars="GOOGLE_CLOUD_LOCATION=us-central1" \
  --set-env-vars="GOOGLE_CLOUD_API_KEY=AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8"
```

**Option B: Deploy to Cloud Run with Vertex AI Agent**

Keep Cloud Run but use the Vertex AI agent code:

```bash
# Update app.py to use agent_vertexai instead of agent_manual
# Then redeploy
bash deploy.sh
```

### Step 3: Add OTEL to Vertex AI Deployment

Create `agent_vertexai_otel.py`:

```python
from agent_vertexai import CityInfoAgent
from telemetry import tracer, meter
import logging

logger = logging.getLogger(__name__)

class CityInfoAgentWithOTEL(CityInfoAgent):
    def query(self, user_input: str):
        with tracer.start_as_current_span("vertex_ai_agent_query") as span:
            span.set_attribute("user.input", user_input)
            logger.info(f"Processing query: {user_input[:100]}")

            try:
                result = super().query(user_input)
                span.set_attribute("agent.success", True)
                logger.info("Query completed successfully")
                return result
            except Exception as e:
                span.set_attribute("agent.success", False)
                span.set_attribute("error", str(e))
                logger.error(f"Query failed: {e}")
                raise

def query(user_input: str):
    agent = CityInfoAgentWithOTEL()
    return agent.query(user_input)
```

---

## 📦 Option 3: Hybrid Approach (Best of Both)

Deploy **both** and use for different purposes:

### Cloud Run (Production)
- Production API
- Full OTEL integration
- REST endpoints for external systems
- Current deployment

### Cloud Function/Vertex AI (Internal)
- Internal testing
- Direct SDK access
- Rapid prototyping
- Development environment

**Deploy both:**

```bash
# Cloud Run (keep current)
bash deploy.sh

# Cloud Function (add new)
gcloud functions deploy ai-agent-vertexai \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=query \
  --trigger-http \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716"
```

---

## 🔧 Migration Guide: Cloud Run → Vertex AI

If you want to fully migrate:

### Step 1: Update Dependencies

```bash
# Update requirements.txt
echo "google-cloud-aiplatform" >> requirements.txt
```

### Step 2: Update Application

Replace `app.py` imports:

```python
# OLD:
from agent_manual import run_agent

# NEW:
from agent_vertexai import query as run_agent
```

### Step 3: Redeploy

```bash
# Build new image
gcloud builds submit --tag gcr.io/agentic-ai-integration-490716/ai-agent

# Deploy to Cloud Run
bash deploy.sh
```

### Step 4: Test

```bash
TOKEN=$(gcloud auth print-identity-token)

curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Tokyo?"}'
```

### Step 5: Verify OTEL

```bash
# Check Cloud Run logs
gcloud logging read \
  "resource.labels.service_name=ai-agent" \
  --limit=20

# Check Portal26 dashboard
```

---

## 🧪 Testing Vertex AI Deployment

### Test Agent Locally

```bash
# Set environment variables
export GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716
export GOOGLE_CLOUD_LOCATION=us-central1
export GOOGLE_CLOUD_API_KEY=AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8

# Run agent
python agent_vertexai.py "What is the weather in Tokyo?"
```

### Test Cloud Function

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe ai-agent-vertexai --region=us-central1 --gen2 --format='value(serviceConfig.uri)')

# Test query
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is the weather in Tokyo?"}'
```

### Compare with Cloud Run

```bash
# Cloud Run
TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Tokyo?"}'
```

---

## 💡 Recommendations

### For Your Use Case:

**Keep Cloud Run** because:
1. ✅ Already working in production
2. ✅ Full OTEL integration with Portal26
3. ✅ REST API for easy integration
4. ✅ Proven architecture
5. ✅ Complete documentation and testing

**Add Vertex AI** optionally for:
1. ⚡ Internal testing
2. 🔬 Experimentation
3. 📊 Comparison testing
4. 🛠️ Development environment

---

## 📋 Deployment Checklist

### If Keeping Cloud Run:
- [ ] No changes needed
- [ ] Continue using current deployment
- [ ] Keep OTEL integration working
- [ ] Use existing testing docs

### If Adding Vertex AI:
- [ ] Test `agent_vertexai.py` locally
- [ ] Choose deployment method (Cloud Function/Cloud Run)
- [ ] Add OTEL instrumentation
- [ ] Update deployment scripts
- [ ] Test end-to-end
- [ ] Verify Portal26 integration

### If Migrating Fully:
- [ ] Test Vertex AI agent locally
- [ ] Update application imports
- [ ] Redeploy to Cloud Run
- [ ] Verify OTEL still works
- [ ] Test all endpoints
- [ ] Update documentation

---

## 🔗 Resources

### Vertex AI
- **Reasoning Engine**: https://cloud.google.com/vertex-ai/docs/reasoning-engine/overview
- **Agent Builder**: https://cloud.google.com/vertex-ai/docs/agent-builder
- **SDK**: https://cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk

### Current Deployment
- **Cloud Run**: https://console.cloud.google.com/run/detail/us-central1/ai-agent
- **Service URL**: https://ai-agent-961756870884.us-central1.run.app

---

## ❓ FAQ

**Q: Should I migrate from Cloud Run to Vertex AI?**
A: No, your Cloud Run deployment is production-ready. Only add Vertex AI if you need specific Vertex AI features.

**Q: Can I use both?**
A: Yes! Deploy Cloud Run for production API and Cloud Function with Vertex AI agent for internal use.

**Q: Will OTEL work with Vertex AI?**
A: Yes, but you need to add instrumentation (see agent_vertexai_otel.py example above).

**Q: Which is cheaper?**
A: Cloud Run is typically more cost-effective for HTTP APIs. Vertex AI Reasoning Engine is preview and pricing may change.

**Q: Can I deploy the ADK agent.py?**
A: Not directly - the ADK package isn't available yet. Use agent_vertexai.py instead.

---

## ✅ Summary

**Current Status:**
- ✅ Cloud Run deployment working
- ✅ Full OTEL integration
- ✅ Production-ready
- ✅ Comprehensive testing

**Vertex AI Option:**
- 📝 `agent_vertexai.py` created
- 📝 Deployment scripts ready
- 📝 Testing instructions included
- ⚠️ Optional enhancement

**Recommendation:**
**Keep Cloud Run** for production, **optionally add Vertex AI** for experimentation.

---

**Last Updated**: 2026-03-27
**Version**: 1.0
