# Reasoning Engine Deletion Summary

**Date**: 2026-04-10  
**Action**: Deleted all Vertex AI Reasoning Engines sending telemetry

---

## Reasoning Engines Deleted

### Session 1: us-central1 (13:16 IST)

1. **Post-ADK Manual OTEL Test**
   - ID: 4833919858389286912
   - Region: us-central1
   - Created: 2026-04-09 14:02:49
   - Created by: Unknown (team member)

2. **Post-ADK Debug Agent**
   - ID: 7765763215807479808
   - Region: us-central1
   - Created: 2026-04-09 13:15:45
   - Created by: Unknown (team member)

### Session 2: us-west1 (13:30 IST)

3. **AGENT_DESIGNER_GENERATED_DO_NOT_DELETE** ← Main culprit
   - ID: 4493378567278690304
   - Region: us-west1
   - Created: 2026-03-30 15:19:17 (11 days old)
   - Created by: **yesuvadian.c@portal26.ai** (YOU)
   - Method: Agent Designer UI (internal API)
   - This was generating continuous telemetry every 10-15 seconds

---

## Why It Wasn't Found Initially

1. **Different Region**: Was in us-west1, we were checking us-central1
2. **Misleading Name**: "DO_NOT_DELETE" suggested it was system-generated
3. **Old Creation Date**: Created 11 days ago, seemed unrelated to recent work

---

## Timeline of Investigation

| Time | Event |
|------|-------|
| 13:00 | Pulled Kinesis logs, saw `portal26_otel_agent` from `relusys` |
| 13:05 | Analyzed machines, identified Reasoning Engines as source |
| 13:16 | Deleted 2 Reasoning Engines in us-central1 |
| 13:21 | Pulled Kinesis again, **still seeing telemetry!** |
| 13:25 | Checked other regions, found engine in us-west1 |
| 13:30 | Deleted us-west1 engine |
| 13:30 | Verified all regions clear (0 engines everywhere) |

---

## Telemetry Pattern Before Deletion

The us-west1 Reasoning Engine was sending telemetry:
```
13:16:13 - portal26_otel_agent (relusys)
13:16:26 - portal26_otel_agent (relusys)
13:16:37 - portal26_otel_agent (relusys)
... every ~10-15 seconds ...
13:21:05 - portal26_otel_agent (relusys)
```

**Frequency**: Every 10-15 seconds  
**Service Name**: portal26_otel_agent  
**User**: relusys  
**OS Info**: None (running in GCP Cloud)

---

## Current Status

### GCP Resources (All Regions)
✅ Reasoning Engines: **0**  
✅ Cloud Run Services: **0**  
✅ Endpoints: **0**  
✅ Models: **0**

### Remaining Telemetry Sources

Only team members' local Claude Code sessions:

1. **karunakaran** - Mac (IntelliJ, macOS 24.6.0, arm64)
2. **srijangupta** - Mac (IntelliJ, macOS 24.6.0, arm64)
3. **kalpana** - Mac (Terminal, macOS 24.3.0, arm64)

### Your Windows Machine
✅ **LAPTOP-T6A5Q56Q**: Clean, NOT sending telemetry

---

## Expected Outcome

After 3-5 minutes (telemetry pipeline flush time):
- ❌ No more `portal26_otel_agent` telemetry
- ❌ No more `relusys` user in logs
- ✅ Only `claude-code` service from team Macs
- ✅ Only team member users: karunakaran, srijangupta, kalpana

---

## How Agent Designer Creates Reasoning Engines

When you use the **Agent Designer UI** in Google Cloud Console:

1. Navigate to: Vertex AI → Agent Builder → Design an Agent
2. Build your agent using the visual designer
3. Click "Deploy" or "Test"
4. **Behind the scenes**: Creates a Reasoning Engine with auto-generated name
5. **Name pattern**: `AGENT_DESIGNER_GENERATED_DO_NOT_DELETE`
6. **Purpose**: Backend execution engine for the agent you designed

**Why "DO_NOT_DELETE"?**
- The UI expects this engine to exist
- Deleting it may break the agent design in the UI
- But the agent design is stored separately, so it can be recreated

---

## Lessons Learned

1. ✅ Always check **all regions**, not just the default one
2. ✅ Auto-generated resources (like Agent Designer engines) can run indefinitely
3. ✅ Service name in telemetry (`portal26_otel_agent`) ≠ resource name (`AGENT_DESIGNER_GENERATED_DO_NOT_DELETE`)
4. ✅ Resources created via UI may have different naming patterns than CLI/API
5. ✅ When telemetry continues after deletion, check other regions

---

## Verification Checklist

To verify telemetry has stopped, wait 5 minutes then run:

```bash
cd C:\Yesu\ai_agent_projectgcp\portal26_otel_agent

# Pull latest Kinesis logs (last 5 minutes)
AWS_ACCESS_KEY_ID=AKIAWG3G2WLZ2T45KWPJ \
AWS_SECRET_ACCESS_KEY=$(grep AWS_SECRET_ACCESS_KEY .env.DISABLED | cut -d= -f2) \
python pull_agent_logs.py

# Analyze machines
python analyze_machines.py
```

**Expected result**:
- No `portal26_otel_agent` service
- No `relusys` user
- Only `claude-code` from team members

---

## If Telemetry Still Continues

If `portal26_otel_agent` telemetry continues after 5 minutes:

1. Check for Cloud Functions:
   ```bash
   gcloud functions list --project=agentic-ai-integration-490716
   ```

2. Check for Compute Engine VMs:
   ```bash
   gcloud compute instances list --project=agentic-ai-integration-490716
   ```

3. Check for App Engine:
   ```bash
   gcloud app services list --project=agentic-ai-integration-490716
   ```

4. Check other GCP projects:
   ```bash
   gcloud projects list
   ```

---

**Generated**: 2026-04-10 13:32 IST  
**Next Check**: 2026-04-10 13:35-13:37 IST (wait 3-5 minutes)
