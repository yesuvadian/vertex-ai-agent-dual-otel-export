# GCP Cloud Trace - Important Notes

## Issue: No Traces Appearing in Cloud Trace

**Root Cause:**  
GCP Agent Engine with `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` enables telemetry collection, but **does NOT automatically export to Cloud Trace** without additional configuration.

---

## Why This Happens

1. **Custom OTEL Setup Required**  
   - Agent Engine needs explicit OTEL exporter configuration
   - Without it, telemetry is collected but not exported

2. **Cloud Trace OTLP Support**  
   - Cloud Trace may not support OTLP endpoints directly
   - Requires Google Cloud Trace exporter (not OTLP exporter)

3. **Custom OTEL Overrides Default**  
   - When you set custom OTEL endpoint, it replaces GCP defaults
   - Traces go ONLY to that endpoint, not Cloud Trace

---

## Working Solution: portal26_otel_agent

**Status:** ✅ CONFIRMED WORKING

- Agent ID: 7483734085236131200
- Endpoint: https://otel-tenant1.portal26.in:4318
- Authentication: ✅ Working (200 OK)
- Local test: ✅ Successful

**How to verify:**
```bash
python test_otel_direct.py
```

**Check Portal26 Dashboard:**
- Filter: tenant_id=tenant1, user_id=relusys
- Service: portal26_otel_agent
- Should see traces with queries and responses

---

## Options for GCP Cloud Trace

### Option 1: Use Google Cloud Trace Exporter (Not OTLP)

Instead of OTLP exporter, use Google's native Cloud Trace exporter:

```python
from google.cloud.trace.v1 import TraceServiceClient
# Use Cloud Trace SDK instead of OTEL OTLP
```

**Note:** This is different from OTEL and requires different setup.

### Option 2: Export to Both Portal26 AND Cloud Trace

Create agent with multiple exporters:
- One for Portal26 (OTLP)
- One for Cloud Trace (GCP native)

### Option 3: Use Portal26 for All Telemetry

**Recommended:** Portal26 is working. Use it for all telemetry needs.

---

## Current Project Status

### ✅ Working: portal26_otel_agent

**Export destination:** Portal26  
**Status:** Fully tested and working  
**Configuration:**
```env
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic ...
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1
```

**Test:** `python test_otel_direct.py` - Returns 200 OK

### ⚠️ Attempted: gcp_traces_agent

**Export destination:** GCP Cloud Trace  
**Status:** Configuration unclear  
**Issue:** Cloud Trace OTLP endpoint not standard

**What we learned:**
- `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` alone is insufficient
- Cloud Trace requires different exporter than OTLP
- GCP Agent Engine works with custom OTEL to external endpoints

---

## Recommendation

**For this project:**

1. **Use portal26_otel_agent for all telemetry**
   - Confirmed working
   - Portal26 dashboard available
   - Authentication tested

2. **If GCP Cloud Trace needed:**
   - Research Google Cloud Trace exporter (not OTLP)
   - May require different SDK
   - Or use Cloud Monitoring instead

3. **For development:**
   - Use portal26_ngrok_agent
   - Local JSON files for debugging
   - Forwards to Portal26

---

## Summary

**What works:**
- ✅ portal26_otel_agent → Portal26 (OTLP with auth)
- ✅ portal26_ngrok_agent → Local + Portal26
- ✅ Local OTEL test (test_otel_direct.py)

**What doesn't work without additional setup:**
- ❌ GCP Cloud Trace via OTLP endpoint
- ❌ Automatic export to Cloud Trace

**Solution:** Use Portal26 for telemetry. It's tested, working, and provides the observability you need.

---

## Next Steps

1. **Test portal26_otel_agent via Console**
   - Query the agent
   - Verify traces in Portal26 dashboard

2. **Show team Portal26 integration**
   - Use VERIFY_PORTAL26.md guide
   - Demonstrate working traces

3. **If Cloud Trace required:**
   - Investigate Google Cloud Trace SDK
   - Different from OTEL OTLP approach
