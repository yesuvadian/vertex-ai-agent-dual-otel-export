# Portal26 Integration - Ready for Deployment

**Status:** ✅ **Authentication FIXED - Ready to Deploy Agents**

**Date:** 2026-03-31 11:22  
**Portal26 Response:** 200 OK (Accepting data!)

---

## Problem Solved

**Issue:** Portal26 dashboard showed no logs  
**Root Cause:** Missing Basic Authentication header  
**Solution:** Added auth credentials to all components  
**Result:** Portal26 now returns **200 OK** ✅

---

## What Was Fixed

### Authentication Added ✅

**Authorization Header:**
```
Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==
Credentials: titaniam:helloworld
```

### Components Updated ✅

1. **local_otel_receiver.py** - Forwards with auth
2. **portal26_ngrok_agent/.env** - Full OTEL config
3. **portal26_otel_agent/.env** - Auth headers + OTEL config
4. **Test scripts** - Updated with auth

---

## Test Results

### Direct Portal26 Test ✅

```bash
$ python check_portal26_response.py

POST https://otel-tenant1.portal26.in:4318/v1/traces
Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==

Response Status: 200
Response Body: 

[SUCCESS] Portal26 accepted the trace data!
```

### Local Receiver Test ✅

```bash
$ python send_test_trace.py

[OK] Test trace sent!
JSON file created: traces_20260331_112200.json (3.3 KB)
```

**Portal26 forwarding:** Working with 200 OK ✅

---

## Updated Configuration

### portal26_otel_agent/.env

```env
GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true

# Portal26 Endpoint
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318

# Service Configuration
OTEL_SERVICE_NAME=portal26_otel_agent

# Resource Attributes (Portal26 Custom)
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1

# Authentication (REQUIRED!)
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==

# Enhanced Logging
OTEL_LOG_USER_PROMPTS=1
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_METRIC_EXPORT_INTERVAL=1000
OTEL_LOGS_EXPORT_INTERVAL=500
```

### portal26_ngrok_agent/.env

```env
GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true

# Ngrok Endpoint (forwards to local receiver)
OTEL_EXPORTER_OTLP_ENDPOINT=https://tabetha-unelemental-bibulously.ngrok-free.dev

# Service Configuration
OTEL_SERVICE_NAME=portal26_ngrok_agent

# Resource Attributes (Portal26 Custom)
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1

# Enhanced Logging
OTEL_LOG_USER_PROMPTS=1
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_METRIC_EXPORT_INTERVAL=1000
OTEL_LOGS_EXPORT_INTERVAL=500

# Note: Auth handled by local receiver when forwarding to Portal26
```

---

## NEXT STEP: Redeploy Agents

**IMPORTANT:** Agents must be redeployed to pick up new `.env` configuration!

### Option 1: Using Terraform (Recommended)

```bash
cd terraform

# Edit terraform.tfvars
notepad terraform.tfvars
# Change: trigger_redeploy = true

# Apply changes
terraform apply

# Agents will be redeployed with new .env files
# Wait 5-7 minutes for deployment to complete
```

### Option 2: Manual Deployment

```bash
# Deploy portal26_ngrok_agent
cd portal26_ngrok_agent
python -m google.adk.cli deploy agent_engine portal26_ngrok_agent \
  --project agentic-ai-integration-490716 \
  --region us-central1 \
  --agent_engine_id 2658127084508938240

# Wait for completion (~2-3 minutes)

# Deploy portal26_otel_agent
cd ../portal26_otel_agent
python -m google.adk.cli deploy agent_engine portal26_otel_agent \
  --project agentic-ai-integration-490716 \
  --region us-central1 \
  --agent_engine_id 7483734085236424704

# Wait for completion (~2-3 minutes)
```

---

## After Redeployment: Verification Steps

### Step 1: Query Agents

**Via Google Cloud Console:**
1. Go to: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716
2. Click on **portal26_ngrok_agent**
3. Send query: "What is the weather in Bengaluru?"
4. Wait for response

### Step 2: Check Local JSON (for ngrok agent)

```bash
ls -lht otel-data/*.json | head -3
cat otel-data/traces_*.json | tail -100
```

**Expected:** New JSON file with your query/response

### Step 3: Check Portal26 Dashboard

1. **Log in to Portal26:** https://portal26.in (or your Portal26 URL)

2. **Navigate to Traces/Telemetry section**

3. **Filter by:**
   - Tenant ID: `tenant1`
   - User ID: `relusys`
   - Time: Last 15 minutes

4. **Look for:**
   - Service: `portal26_ngrok_agent` or `portal26_otel_agent`
   - Spans with your query: "What is the weather in Bengaluru?"
   - Response: "Partly cloudy, 28C. Humidity 70%."
   - Tool calls: `get_weather(city="bengaluru")`

5. **Verify:**
   - ✅ Traces appear in Portal26 UI
   - ✅ Custom attributes visible (tenant1, relusys)
   - ✅ Agent queries and responses captured
   - ✅ Timing and performance data present

---

## Expected Data Flow After Deployment

### portal26_ngrok_agent

```
Query in Console
       ↓
Agent processes
       ↓
Generates OTEL traces
       ↓
Sends to: tabetha-unelemental-bibulously.ngrok-free.dev
       ↓
Ngrok forwards to: localhost:4318
       ↓
Local Receiver:
  - Decodes protobuf ✓
  - Saves JSON file ✓
  - Forwards to Portal26 with auth ✓
       ↓
POST https://otel-tenant1.portal26.in:4318/v1/traces
Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==
       ↓
Portal26 Response: 200 OK ✓
       ↓
LOGS APPEAR IN PORTAL26 DASHBOARD ✓
```

### portal26_otel_agent

```
Query in Console
       ↓
Agent processes
       ↓
Generates OTEL traces
       ↓
Sends directly to: otel-tenant1.portal26.in:4318
Headers: Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
       ↓
Portal26 Response: 200 OK ✓
       ↓
LOGS APPEAR IN PORTAL26 DASHBOARD ✓
```

---

## Troubleshooting

### If Portal26 Dashboard Still Empty After Deployment

**Check 1: Agent Environment Variables**

```bash
# In GCP Console → Agent Engine → Deployment details → Environment
# Verify these are set:
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1
```

**Check 2: Local Receiver Running (for ngrok agent)**

```bash
curl http://localhost:4318
# Should return: OK - Local OTEL Receiver Running
```

**Check 3: Test Direct Portal26**

```bash
python check_portal26_response.py
# Should return: [SUCCESS] Portal26 accepted the trace data!
```

**Check 4: Portal26 Dashboard Filters**

Make sure filters are correct:
- Tenant: `tenant1` (not empty, not default)
- User: `relusys` (not empty)
- Time range: Last 1 hour (not last 5 minutes)

---

## Configuration Summary

### What Portal26 Receives

**Resource Attributes:**
- `service.name`: portal26_ngrok_agent / portal26_otel_agent
- `portal26.tenant_id`: tenant1
- `portal26.user.id`: relusys
- `agent.type`: ngrok-local / otel-direct

**Authentication:**
- Header: `Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==`
- Username: titaniam
- Password: helloworld

**Protocol:**
- Format: OTLP/HTTP
- Encoding: Protobuf
- Content-Type: application/x-protobuf

**Enhanced Features:**
- User prompt logging enabled (`OTEL_LOG_USER_PROMPTS=1`)
- Fast log export (500ms interval)
- Metric export (1000ms interval)

---

## Deployment Checklist

Before deploying:
- [x] Authentication credentials added
- [x] .env files updated
- [x] Local receiver updated
- [x] Direct Portal26 test: PASSED (200 OK)
- [x] Local receiver test: PASSED
- [x] Changes committed to GitHub

After deploying:
- [ ] Agents redeployed (wait 5-7 min)
- [ ] Query agents via Console
- [ ] Check local JSON files (ngrok agent)
- [ ] **Check Portal26 dashboard for logs**
- [ ] Verify traces appear with correct attributes

---

## Success Criteria

✅ **Portal26 Dashboard shows:**
- Service names: portal26_ngrok_agent, portal26_otel_agent
- Tenant: tenant1
- User: relusys
- Recent traces (within last 15 minutes)
- Agent queries and responses
- Tool calls and LLM interactions
- Timing and performance data

✅ **Local Files show (ngrok agent only):**
- JSON files in otel-data/
- Recent timestamps
- Valid trace data

---

## Summary

**Status:** ✅ Ready for Deployment

**Authentication:** Fixed and tested (200 OK)  
**Configuration:** Updated in all components  
**Local Tests:** Passing  
**GitHub:** Committed and pushed  

**Next Action:** **Redeploy agents** to enable Portal26 logging!

After redeployment, Portal26 dashboard will show logs with:
- Tenant: tenant1
- User: relusys  
- Full agent telemetry and traces

---

**Ready to deploy!** 🚀
