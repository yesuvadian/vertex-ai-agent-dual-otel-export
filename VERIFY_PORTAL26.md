# Portal26 Telemetry Verification

**Quick guide for team members to verify Portal26 integration**

---

## Status

✅ Local OTEL test successful (test_otel_direct.py completed)  
✅ Portal26 authentication working (200 OK)  
✅ Agent deployed with correct configuration  

---

## How to Verify in Portal26 Dashboard

### Step 1: Log in to Portal26

Go to: https://portal26.in (or your Portal26 URL)

### Step 2: Navigate to Traces/Telemetry

Find the telemetry or traces section in the Portal26 UI

### Step 3: Set Filters

**Required filters:**
- **Tenant ID:** `tenant1`
- **User ID:** `relusys`
- **Time Range:** Last 15-30 minutes

### Step 4: Look for Test Traces

You should see traces from:

**Service Name:** `portal26_otel_agent`

**Recent spans:**
- `local_agent_test` (from local test)
- Agent query spans (if agent was queried via Console)

**Attributes to verify:**
- `portal26.tenant_id`: tenant1
- `portal26.user.id`: relusys
- `service.name`: portal26_otel_agent
- Custom test attributes (if present)

---

## Expected Results

✅ **SUCCESS:** Traces appear in Portal26 dashboard with correct tenant/user IDs

❌ **FAILED:** No traces appear
   - Check time range filter (try "Last 1 hour")
   - Verify filters are set correctly
   - Confirm agent was queried recently

---

## To Generate Fresh Telemetry

### Option 1: Query Deployed Agent (GCP Console)

1. Go to: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716
2. Click on `portal26_otel_agent`
3. Send query: "What is the weather in Bengaluru?"
4. Wait 30-60 seconds
5. Check Portal26 dashboard (refresh if needed)

### Option 2: Run Local Test

```bash
cd C:\Yesu\ai_agent_projectgcp
python test_otel_direct.py
```

This sends a test span to Portal26 immediately.

### Option 3: Test Portal26 Endpoint Directly

```bash
python check_portal26_response.py
```

This confirms Portal26 is accepting data (should return 200 OK).

---

## Configuration Details

**Portal26 Endpoint:**
```
https://otel-tenant1.portal26.in:4318
```

**Authentication:**
```
Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==
(Credentials: titaniam:helloworld)
```

**Resource Attributes:**
```
portal26.tenant_id=tenant1
portal26.user.id=relusys
service.name=portal26_otel_agent
```

---

## Troubleshooting

**Q: No traces in Portal26?**

A: 
1. Verify filters are correct (tenant1, relusys)
2. Expand time range to "Last 1 hour"
3. Generate fresh telemetry (run test_otel_direct.py)
4. Check Portal26 authentication is working (run check_portal26_response.py)

**Q: Traces appear but missing attributes?**

A: Agent may need redeployment to pick up latest .env configuration

**Q: Portal26 returns errors?**

A: Check authentication credentials are correct in .env files

---

## Files Reference

- **PORTAL26_READY_TO_DEPLOY.md** - Complete deployment guide
- **verify_telemetry.py** - Automated verification script
- **test_otel_direct.py** - Direct OTEL test to Portal26
- **check_portal26_response.py** - Test Portal26 endpoint
- **portal26_otel_agent/.env** - Agent configuration with auth

---

**For detailed instructions, see:** `PORTAL26_READY_TO_DEPLOY.md`
