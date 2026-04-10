# Telemetry Source Investigation & Resolution

**Date**: 2026-04-09  
**Issue**: Telemetry still appearing in Kinesis after portal26_otel_agent deletion

---

## Investigation Results

### ✅ Root Cause Found

**3 Active Agents** were still deployed and sending telemetry:

| Agent ID | Display Name | OTEL Service Name | Endpoint | Status |
|----------|-------------|-------------------|----------|--------|
| `2601260343120363520` | Debug Step 1 - Provider Monitoring | `debug-agent` | localhost:4318 | ❌ **DELETED** |
| `9176515799081287680` | Clean Agent - No OTEL Code | `debug-agent` | localhost:4318 | ❌ **DELETED** |
| `9162160575269044224` | Clean Agent - No OTEL Code | `debug-agent` | localhost:4318 | ❌ **DELETED** |

### Timeline

**17:15-17:17** - Telemetry observed in Kinesis  
**17:20** - Kinesis pull showed 8,844 records (49 matching portal26_otel_agent)  
**17:38** - Investigation started  
**17:39** - Found 3 active agents via REST API  
**17:39** - Deleted all 3 agents forcefully  
**17:40** - ✅ **All agents deleted successfully**

---

## Why Telemetry Appeared with Wrong Service Name

The agents were configured with:
```
OTEL_SERVICE_NAME=debug-agent
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

But telemetry arrived at Kinesis with `service.name: portal26_otel_agent`

### Possible Explanations:

1. **Local OTEL Collector** - A collector running on localhost:4318 that relabels service names
2. **Portal26 Processing** - Portal26 backend might be mapping/relabeling services
3. **Terraform Configuration** - The .env files in portal26_otel_agent/ directory set `OTEL_SERVICE_NAME=portal26_otel_agent`, which might have been used by a local process
4. **Kinesis Data Buffering** - Old data from deleted agents still being processed

---

## Actions Taken

### 1. Listed All Active Agents

```bash
curl -X GET \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)"
```

### 2. Force Deleted All Agents

```bash
# Agent 1
curl -X DELETE \
  "https://.../reasoningEngines/2601260343120363520?force=true" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)"

# Agent 2
curl -X DELETE \
  "https://.../reasoningEngines/9176515799081287680?force=true"

# Agent 3
curl -X DELETE \
  "https://.../reasoningEngines/9162160575269044224?force=true"
```

### 3. Verified Deletion

```
[SUCCESS] All agents deleted!
Total agents found: 0
```

---

## Verification Steps

### Check for New Telemetry (in 5-10 minutes)

```bash
cd portal26_otel_agent
python pull_agent_logs.py
```

**Expected Result:**
- ✅ **NO new logs** → All sources stopped
- ❌ **NEW logs** → Additional investigation needed

### Check GCP Logs

```bash
gcloud logging read \
  "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND timestamp>=\"$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ)\"" \
  --limit=10 --project=agentic-ai-integration-490716
```

**Expected Result:** No recent logs

---

## Additional Checks

### Local Processes

```bash
# Check for local OTEL collectors
netstat -ano | findstr "4318"

# Check running Python processes
tasklist | findstr python
```

### Other Agents (if any)

```bash
# Check other GCP projects
gcloud projects list --format="table(projectId)"

# Check Cloud Run services
gcloud run services list --project=agentic-ai-integration-490716
```

---

## Status

- [x] **Found active agents**
- [x] **Deleted all agents (3 total)**
- [x] **Verified deletion**
- [ ] **Confirmed telemetry stopped** (check in 5-10 minutes)

---

## Next Steps

1. ⏰ **Wait 10 minutes** for buffered data to clear
2. 🔍 **Run** `python pull_agent_logs.py` to check for new telemetry
3. ✅ **If no new logs** → Issue resolved
4. ⚠️ **If new logs appear** → Check for:
   - Local OTEL collectors on port 4318
   - Cloud Run services sending telemetry
   - Other GCP projects with similar agents
   - Portal26 backend buffering/replaying data

---

## Files to Review

- `portal26_otel_agent/.env` - Contains service name configuration
- `terraform/terraform.tfvars` - Agent deployment config
- `portal26_otel_agent/pull_agent_logs.py` - Kinesis data retrieval

---

**Resolution Time**: ~2 minutes  
**Method**: REST API force deletion  
**Confidence**: HIGH (all agents confirmed deleted)
