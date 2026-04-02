# Full Content Logging - Final Configuration

**Date:** 2026-04-02  
**Status:** Deploying new agent with official Google environment variable

---

## ✅ Correct Configuration Added

### Official Google Environment Variable

**From Vertex AI documentation:**
```env
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
```

**What this captures:**
- ✅ Full user prompts (complete text)
- ✅ Full LLM responses (complete text)
- ✅ Tool call parameters
- ✅ Tool outputs
- ✅ All message content

**Source:** Google Cloud Console → Service Configuration → Observability

---

## Complete Configuration

### gcp_traces_agent/.env

```env
# Enable telemetry
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true

# Service name
OTEL_SERVICE_NAME=gcp_traces_agent

# FULL CONTENT LOGGING - Official Google variable
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true

# Log user prompts
OTEL_LOG_USER_PROMPTS=1

# Large attribute limits (10KB per attribute)
OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT=10000
OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT=10000

# Allow many attributes and events
OTEL_ATTRIBUTE_COUNT_LIMIT=128
OTEL_SPAN_EVENT_COUNT_LIMIT=128

# Debug logging
OTEL_LOG_LEVEL=debug
```

---

## Deployment Strategy

### Why New Agent vs Update

**Update attempts failed:**
- ❌ Attempt 1: Reserved variable error
- ❌ Attempt 2: "Failed to update Agent Engine"
- ❌ Attempt 3: "Failed to update Agent Engine"

**Solution:** Deploy as NEW agent
- ✅ Avoids update conflicts
- ✅ Fresh deployment state
- ✅ Clean configuration
- ✅ Can compare old vs new

---

## After Deployment

### 1. Get New Agent ID

The deployment will output a new agent ID. Update the client configuration:

**Edit:** `gcp_traces_agent_client/.env`
```env
SERVICE_NAME=gcp_traces_agent_new  # Or use the new agent ID
```

### 2. Test Full Content Logging

**Query the new agent:**
```
Send: "What is the weather in Tokyo? Please provide detailed information."
```

**Check traces in Cloud Trace:**
1. Go to: https://console.cloud.google.com/traces?project=agentic-ai-integration-490716
2. Filter by new service name
3. Click on a trace
4. **Check labels for:**
   - Full prompt text (should not be truncated)
   - Full response text (should not be truncated)
   - Tool parameters (complete JSON)
   - Tool outputs (complete results)

### 3. Compare with Old Agent

**Old agent (8517380568462131200):**
- May have truncated content
- Basic telemetry only

**New agent (TBD):**
- Full content capture
- No truncation
- Complete message content

---

## Environment Variables Explained

### OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT
**Purpose:** Captures full message content in GenAI instrumentation  
**Values:** true/false  
**Effect:** When true, captures complete prompts and responses  
**Official:** ✅ Google-recommended variable

### OTEL_LOG_USER_PROMPTS
**Purpose:** Log user prompts in traces  
**Values:** 0/1  
**Effect:** Includes user query text in traces

### OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT
**Purpose:** Maximum length of span attribute values  
**Values:** Number of characters (10000 = 10KB)  
**Effect:** Prevents truncation of long text

### OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT
**Purpose:** Maximum length of any attribute value  
**Values:** Number of characters  
**Effect:** Global attribute length limit

### OTEL_ATTRIBUTE_COUNT_LIMIT
**Purpose:** Maximum number of attributes per span  
**Values:** Number (128 = many attributes)  
**Effect:** Allows capturing many data points per span

---

## Verification Checklist

After deployment completes:

- [ ] New agent appears in GCP Console
- [ ] New agent ID obtained
- [ ] Test query sent to new agent
- [ ] Traces visible in Cloud Trace
- [ ] Click on trace to see details
- [ ] Labels contain full prompt text (not "...")
- [ ] Labels contain full response text (not "...")
- [ ] Tool parameters are complete
- [ ] No truncation anywhere
- [ ] Export trace to JSON for verification

---

## Troubleshooting

### If Content Still Truncated

**Check these values:**
```env
OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT=10000  # Increase if needed
OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT=10000       # Increase if needed
```

Can increase to 50000 (50KB) or even 100000 (100KB) if needed.

### If Traces Not Appearing

**Verify:**
1. Agent deployed successfully
2. `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`
3. Query sent to agent recently
4. Filter in Cloud Trace set correctly
5. Time range includes recent queries

### If Deployment Fails

**Fallback:** Use existing agent
- Agent ID: 8517380568462131200
- Already deployed and working
- Captures basic telemetry
- May have some truncation but still useful

---

## Client Configuration Update

### After New Agent Deployed

**Update:** `gcp_traces_agent_client/.env`

**Option 1:** Filter by new service name
```env
SERVICE_NAME=gcp_traces_agent  # Should still work if name unchanged
```

**Option 2:** Filter by agent ID
If needed, we can modify the client to filter by agent ID instead of service name.

---

## Documentation References

**Google Cloud Vertex AI:**
- Observability: Agent Engine Telemetry
- Environment Variable: `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`
- Documentation: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine

**OpenTelemetry:**
- Attribute Limits: OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT
- Span Configuration: OTEL_SPAN_EVENT_COUNT_LIMIT
- Documentation: https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/

---

## Summary

**Problem:** Minimal skeleton logging (no content)  
**Solution:** Official Google environment variable  
**Variable:** `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`  
**Deployment:** New agent (avoids update failures)  
**Result:** Full prompt/response content captured  

**Status:** 🟡 Deploying now...
