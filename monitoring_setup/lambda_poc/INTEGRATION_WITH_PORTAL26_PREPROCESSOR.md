## Integration Plan: Reasoning Engines + Portal26 Preprocessor

### Current Setup (What We Have)
```
3 Reasoning Engines → Cloud Logging → Pub/Sub → AWS Lambda
```

### Target Setup (Using Portal26 Preprocessor)
```
3 Reasoning Engines → Cloud Logging → Pub/Sub → Portal26 FastAPI Preprocessor → Customer OTEL
```

---

## Integration Steps

### Step 1: Deploy Portal26 Preprocessor

**Location:** `C:\Yesu\portal26-agentengine-otel-preprocessor`

```bash
cd C:\Yesu\portal26-agentengine-otel-preprocessor

# Install dependencies
pip install -r requirements.txt

# Build Docker container
docker-compose build

# Start the preprocessor
docker-compose up -d
```

**This gives you:**
- FastAPI endpoint at `http://localhost:8080/webhook/{customer_id}`
- GCP to OTEL conversion
- Multi-tenant message processing

### Step 2: Update Pub/Sub Push Subscriptions

**Replace AWS Lambda URL with FastAPI endpoint:**

```bash
PROJECT_ID="agentic-ai-integration-490716"

# Delete old AWS Lambda subscription
gcloud pubsub subscriptions delete reasoning-engine-logs-to-aws \
  --project $PROJECT_ID

# Create new subscription to FastAPI preprocessor
gcloud pubsub subscriptions create reasoning-engine-to-preprocessor \
  --topic reasoning-engine-logs-topic \
  --push-endpoint http://YOUR_FASTAPI_HOST:8080/webhook/customer-001 \
  --project $PROJECT_ID
```

**Note:** You'll need to expose FastAPI publicly (use ngrok, Cloud Run, or App Runner)

### Step 3: Configure Customer in Preprocessor

The preprocessor already has customer configuration support:

**File:** `implementation/message-processor/api/main.py`

Add your customer configuration:
```python
CUSTOMERS = {
    "customer-001": {
        "name": "agentic-ai-integration",
        "project_id": "agentic-ai-integration-490716",
        "otel_endpoint": "https://your-customer-otel-endpoint.com/v1/traces",
        "otel_headers": {
            "X-API-Key": "customer-api-key"
        }
    }
}
```

### Step 4: Test the Flow

```bash
# Trigger a reasoning engine query
python test_reasoning_engine_new.py

# Check preprocessor logs
docker-compose logs -f message-processor

# Verify OTEL data reaches customer endpoint
curl http://localhost:8080/health
```

---

## Architecture Comparison

### What We Built (AWS Lambda)

**Pros:**
- ✅ Quick POC
- ✅ Serverless (no container management)
- ✅ Working end-to-end

**Cons:**
- ❌ Not OTEL format
- ❌ No GCP trace pulling
- ❌ No multi-tenant routing
- ❌ Limited preprocessing

### Portal26 Preprocessor (Better)

**Pros:**
- ✅ OTEL format conversion
- ✅ Multi-tenant (one container for all customers)
- ✅ GCP trace pulling
- ✅ Customer-specific routing
- ✅ Checkpoint management
- ✅ Production-ready

**Cons:**
- ⚠️ Requires container deployment
- ⚠️ Need public endpoint

---

## Complete Integration Architecture

```
┌─────────────────────────────────────────────────┐
│           GCP Environment                        │
│                                                  │
│  Reasoning Engines (3)                          │
│  - basic-gcp-agent-working                      │
│  - monitoring-agent-with-logs                   │
│  - adk-style-monitoring-agent                   │
│          ↓                                       │
│  Cloud Logging (automatic)                      │
│          ↓                                       │
│  Log Sink (reasoning-engine-to-pubsub)         │
│          ↓                                       │
│  Pub/Sub (reasoning-engine-logs-topic)         │
│          ↓ (push subscription)                  │
└──────────┼──────────────────────────────────────┘
           │
           │ HTTPS Push
           ↓
┌─────────────────────────────────────────────────┐
│   Portal26 Preprocessor Container               │
│                                                  │
│  FastAPI Webhook                                │
│    ↓                                            │
│  GCP to OTLP Converter                          │
│    ↓                                            │
│  Customer Router                                │
│    ↓                                            │
│  OTEL Forwarder                                 │
│          ↓                                       │
└──────────┼──────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────────┐
│   Customer OTEL Collectors                      │
│   - Traces, Logs, Metrics                      │
│   - Portal26 Backend                            │
└─────────────────────────────────────────────────┘
```

---

## Migration Path

### Phase 1: Keep AWS Lambda (Current)
- ✅ Everything working
- Use for immediate needs

### Phase 2: Deploy Preprocessor Alongside
- Deploy Portal26 preprocessor
- Test with sample messages
- Verify OTEL conversion

### Phase 3: Switch Pub/Sub Subscriptions
- Update subscriptions to point to preprocessor
- Keep Lambda as backup
- Monitor for issues

### Phase 4: Decommission Lambda
- Remove AWS Lambda
- Remove Lambda-related Pub/Sub subscriptions
- Full production on preprocessor

---

## Key Differences

| Feature | AWS Lambda (Current) | Portal26 Preprocessor |
|---------|---------------------|----------------------|
| **Format** | GCP native | OTEL (standard) |
| **Multi-tenant** | No | Yes (1 container) |
| **Trace Pulling** | No | Yes (GCP API) |
| **Cost** | $0.20/10K | $40/month (unlimited) |
| **Deployment** | Serverless | Container |
| **Customer Routing** | Single endpoint | Per-customer config |
| **Schema Conversion** | None | GCP → OTLP |

---

## Recommended Next Steps

1. **Review Portal26 Preprocessor Code**
   ```bash
   cd C:\Yesu\portal26-agentengine-otel-preprocessor
   code implementation/message-processor/
   ```

2. **Test Locally**
   ```bash
   docker-compose up -d
   curl http://localhost:8080/health
   ```

3. **Deploy to Production**
   - Use Cloud Run, App Runner, or ECS
   - Get public HTTPS endpoint
   - Update Pub/Sub subscriptions

4. **Configure Customers**
   - Add customer configs
   - Set OTEL endpoints
   - Test end-to-end

---

## Summary

**You have a better solution ready!** The Portal26 preprocessor project provides:

✅ Multi-tenant architecture (shared container)  
✅ OTEL format conversion (standard)  
✅ GCP trace pulling (complete data)  
✅ Customer-specific routing  
✅ Production-ready code  

**Your Reasoning Engines fit perfectly** - just point Pub/Sub to the preprocessor instead of Lambda!
