# Migrate to Agent Builder with Playground

## What We're Doing

Convert Reasoning Engine → Agent Builder Agent
- ✅ Get Playground UI access  
- ✅ Keep all functionality
- ✅ Logs automatically captured to AWS Lambda

---

## Step 1: Create New Agent in Console

**URL:** https://console.cloud.google.com/vertex-ai/agent-builder/agents?project=agentic-ai-integration-490716

### Click "CREATE AGENT"

**Agent Configuration:**
- **Name**: `pubsub-lambda-monitoring-agent`
- **Model**: `Gemini 2.0 Flash`  
- **Instructions**:
```
You are a GCP monitoring agent that processes Pub/Sub messages and forwards them to AWS Lambda with AI analysis.

When you receive a message:
1. Decode the base64 data if provided
2. Analyze the message for:
   - Severity level (HIGH, MEDIUM, LOW, INFO)
   - Category (error, warning, metric, performance)
   - Anomaly detection (true/false)
   - Insights and recommendations
3. Forward the enriched message to AWS Lambda
4. Report the results

Analysis Rules:
- ERROR/EXCEPTION/FAILED/CRITICAL → HIGH severity, anomaly detected
- WARNING/WARN → MEDIUM severity  
- SLOW/TIMEOUT/LATENCY → MEDIUM severity, performance category
- CPU/MEMORY/DISK/METRIC → INFO severity, metric category
```

### Add Function/Tool (Optional - for reference)

**Tool Name**: `analyze_and_forward`
**Description**: Analyzes message and forwards to AWS Lambda
**Parameters**:
```json
{
  "message_data": "Base64 encoded message",
  "message_id": "Message identifier",
  "publish_time": "ISO timestamp"
}
```

Click **CREATE**

---

## Step 2: Test in Playground

Once created, click on your agent → **Playground** tab

**Test Message 1: Normal Log**
```
Analyze this message: {"data": "VGVzdCBtZXNzYWdl", "messageId": "test-001"}
```

**Test Message 2: Error Detection**
```
Analyze: ERROR in database connection timeout
```

**Test Message 3: Performance Issue**
```
Analyze: API latency increased to 5 seconds
```

You should see:
- ✅ Agent responds with analysis
- ✅ Severity classification
- ✅ Recommendations

---

## Step 3: Verify Logs Flow to AWS

Wait 1-2 minutes after testing, then check:

```bash
MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test \
  --since 5m \
  --region us-east-1
```

You should see Agent Builder logs forwarded to Lambda!

---

## Step 4: Delete Old Reasoning Engine

Once new agent is working:

```bash
# List Reasoning Engines
gcloud ai reasoning-engines list \
  --location=us-central1 \
  --project=agentic-ai-integration-490716

# Delete old Reasoning Engine
gcloud ai reasoning-engines delete 3783824681212051456 \
  --location=us-central1 \
  --project=agentic-ai-integration-490716 \
  --quiet
```

Or via Python:
```python
import vertexai
from vertexai.preview import reasoning_engines

vertexai.init(
    project="agentic-ai-integration-490716",
    location="us-central1",
    staging_bucket="gs://agentic-ai-integration-490716-reasoning-engine"
)

# Delete Reasoning Engine
engine = reasoning_engines.ReasoningEngine(
    "projects/961756870884/locations/us-central1/reasoningEngines/3783824681212051456"
)
engine.delete()

print("Reasoning Engine deleted")
```

---

## Architecture After Migration

```
┌──────────────────────────────────────────┐
│         GCP Agent Builder                │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  Monitoring Agent              │     │
│  │  (Playground Enabled)          │     │
│  └──────────┬─────────────────────┘     │
│             │                            │
│             │ Logs (automatic)           │
│             ↓                            │
│  ┌────────────────────────────────┐     │
│  │  Cloud Logging                 │     │
│  └──────────┬─────────────────────┘     │
│             │                            │
│             │ Log Sink                   │
│             ↓                            │
│  ┌────────────────────────────────┐     │
│  │  Pub/Sub: agent-builder-logs   │     │
│  └──────────┬─────────────────────┘     │
└─────────────┼──────────────────────────┘
              │
              │ Push Subscription
              ↓
┌──────────────────────────────────────────┐
│            AWS Lambda                     │
│  (gcp-pubsub-test)                       │
│             ↓                            │
│     Portal26 OTEL Endpoint               │
└──────────────────────────────────────────┘
```

---

## Benefits of Agent Builder

✅ **Playground UI** - Test directly in console  
✅ **Same functionality** - All analysis preserved  
✅ **Automatic logging** - Logs flow to AWS Lambda  
✅ **Tool support** - Can add custom functions  
✅ **Production-ready** - Fully managed service  

---

## Comparison

| Feature | Reasoning Engine (Old) | Agent Builder (New) |
|---------|------------------------|---------------------|
| **Playground UI** | ❌ Not available | ✅ Available |
| **Logs to Cloud Logging** | ✅ Yes | ✅ Yes |
| **Logs to AWS Lambda** | ✅ Yes | ✅ Yes |
| **Tool/Function Calling** | ⚠️ Limited | ✅ Full support |
| **Console Testing** | ❌ CLI only | ✅ UI + CLI |
| **AI Model** | Gemini | Gemini 2.0 Flash |

---

## Summary

1. ✅ Log capture configured (agent-builder-logs → AWS Lambda)
2. ⏳ Create agent in console using instructions above
3. ⏳ Test in Playground
4. ⏳ Verify logs reach Lambda
5. ⏳ Delete old Reasoning Engine

**Estimated time:** 10 minutes

Once complete, you'll have full Playground access with all logs captured!
