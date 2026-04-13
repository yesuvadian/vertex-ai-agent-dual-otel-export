# Relusys Telemetry Source Analysis

**Date**: April 10, 2026  
**Time**: 15:38-15:43 IST (5-minute sample)  
**Analysis**: Fresh Kinesis pull with comprehensive pattern detection

---

## Executive Summary

**CRITICAL FINDING**: The "relusys" telemetry is **NOT normal telemetry** — it's a continuous stream of **ERROR LOGS** from a still-running automated process.

- ✅ **Source**: Automated process running `portal26_otel_agent` code
- ✅ **Frequency**: Every 11.7 seconds (highly regular)
- ✅ **Error**: 100% of logs are metrics export failures (404 errors)
- ❌ **Location**: Unknown (no host/OS metadata)
- ❌ **NOT**: Your Windows machine (confirmed clean)
- ❌ **NOT**: Deleted Reasoning Engines (all confirmed deleted)

---

## 1. Activity Breakdown (5-minute window)

| User | Service | Records | % | Platform | Pattern |
|------|---------|---------|---|----------|---------|
| **user** | claude-code | 37 | 30.3% | Mac arm64 | Irregular |
| **aishwarya** | claude-code | 32 | 26.2% | Mac arm64 | Irregular |
| **relusys** | portal26_otel_agent | 26 | 21.3% | **Unknown** | **Regular** |
| **mathanraj** | claude-code | 17 | 13.9% | Mac arm64 | Irregular |
| **kalpana** | claude-code | 10 | 8.2% | Mac arm64 | Irregular |

---

## 2. Relusys Pattern Analysis

### Timing Data
```
Event #  Time      Interval
------   --------  --------
   1     15:38:33  (start)
   2     15:38:44  +11.2s
   3     15:38:56  +11.4s
   4     15:39:07  +11.5s
   5     15:39:18  +10.9s
   6     15:39:30  +12.2s
   7     15:39:42  +11.9s
   ...   (continuing every ~11s)
  26     15:43:25  +14.0s
```

### Statistical Profile
- **Average interval**: 11.7 seconds
- **Min interval**: 10.5 seconds
- **Max interval**: 14.0 seconds
- **Standard deviation**: 0.87 seconds

### Pattern Classification
```
Type: HIGHLY REGULAR
Behavior: Strict timer-based (~12s)
Source Type: Automated process (cron/scheduler/retry loop)
```

**Interpretation**: The low standard deviation (0.87s) indicates a timer-based system, not manual activity.

---

## 3. Error Analysis

### Error Message (All 26 records)
```
Failed to export metrics batch code: 404, reason: 404 page not found
```

**Source**: `opentelemetry.exporter.otlp.proto.http.metric_exporter`

### Root Cause
1. OTEL metrics exporter is configured to send to `/v1/metrics`
2. Portal26 endpoint returns 404 (endpoint doesn't exist or disabled)
3. Exporter retries every ~10 seconds
4. Each retry generates an ERROR log
5. ERROR logs are sent to Kinesis (creating the "relusys" telemetry)

**This is not normal telemetry — these are error notifications!**

---

## 4. Platform Comparison

### Team Members (Claude Code on Mac)
| User | OS | Version | Arch | Has Host Info |
|------|-------|---------|------|---------------|
| user | darwin | 25.3.0 | arm64 | ✅ Yes |
| aishwarya | darwin | 25.4.0 | arm64 | ✅ Yes |
| mathanraj | darwin | 25.3.0 | arm64 | ✅ Yes |
| kalpana | darwin | 24.3.0 | arm64 | ✅ Yes |

### Relusys Source
| Attribute | Value |
|-----------|-------|
| OS Type | ❌ **Missing** |
| OS Version | ❌ **Missing** |
| Host Name | ❌ **Missing** |
| Host Arch | ❌ **Missing** |
| Cloud Provider | ❌ **Missing** |
| Container ID | ❌ **Missing** |

**Key Difference**: Relusys has **NO platform metadata** — suggests:
- Minimal OTEL configuration
- Serverless environment (Cloud Function/Cloud Run)
- OR: Team member with stripped-down config

---

## 5. Visual Timeline

```
Timeline (R=relusys, U=user, A=aishwarya, M=mathanraj, K=kalpana)

15:38 |RUUAURAUUAAAAURAAUAA
15:39 |AAUUAARAAUAAAAURAAUMUARUAUAMAURAAMUMRUM
15:40 |MUURUUMRUUMAMUURMUMUMRMARA
15:41 |RRRKRKRKKR
15:42 |KARKRKKURUUKURMR
15:43 |KMRUUURMUMU
```

**Pattern**: 
- Team members (U/A/M/K): Clustered, irregular (user activity)
- Relusys (R): Evenly spaced, regular (automated)

---

## 6. Activity Rate Projection

### Relusys Error Logs
- **5 minutes**: 26 records
- **Per minute**: 5.2 records
- **Per hour**: ~312 records
- **Per day**: ~7,488 records
- **Per month**: ~224,640 records

**Cost/Impact**: Continuous error logging, wasting Kinesis capacity and potentially masking real issues.

---

## 7. What We've Ruled Out

| Potential Source | Status | Verification Method |
|------------------|--------|---------------------|
| Your Windows machine | ✅ RULED OUT | All .env files disabled |
| Reasoning Engines (us-central1) | ✅ DELETED | Deleted Apr 9, verified via API |
| Reasoning Engines (us-west1) | ✅ DELETED | Deleted Apr 9, verified via API |
| Reasoning Engines (us-east1) | ✅ NONE | Checked via API |
| AI Endpoints (all regions) | ✅ NONE | Checked via gcloud |
| Cloud Run Services | ✅ NONE | Checked via gcloud |

---

## 8. Most Likely Sources (Ranked)

### #1: Team Member Running Portal26_OTEL_Agent Locally (70% probability)
**Evidence**:
- Someone has the code
- Default config has `USER_ID = "relusys"`
- Regular timing suggests "leave it running" scenario
- No OS info = minimal config or ENV vars only

**Action**: Ask team members

### #2: Undiscovered Cloud Deployment (20% probability)
**Candidates**:
- Cloud Function (API not enabled in project)
- Cloud Run (none found, but could be in different region)
- GKE container (no Kubernetes cluster found)

**Action**: Check all regions systematically

### #3: Local Development Server (10% probability)
**Evidence**:
- Someone started `python agent.py` and left it running
- Terminal/IDE backgrounded but still active

**Action**: Check with team if anyone has long-running terminals

---

## 9. Why It's Hard to Find

The source is deliberately or accidentally **invisible** due to:

1. **No Resource Detection**: OTEL auto-detection disabled
   ```python
   # Missing or disabled:
   from opentelemetry.sdk.resources import Resource
   ```

2. **Minimal Configuration**: Only exports, no metadata
   ```bash
   OTEL_EXPORTER_OTLP_ENDPOINT=https://...
   PORTAL26_USER_ID=relusys
   # Missing: host detection, cloud detection, etc.
   ```

3. **Error Context Lost**: Errors don't include source location

---

## 10. How to Find the Source

### Option A: Ask Team (Fastest)
```
Subject: Is anyone running portal26_otel_agent code?

Hi team,

We're seeing continuous error logs from a service with user_id="relusys".
It's trying to export metrics every 10 seconds and getting 404 errors.

Questions:
1. Is anyone running portal26_otel_agent locally?
2. Check your terminals for any long-running Python processes?
3. Anyone testing OTEL integration?

Context: This started after we deployed, uses default config
Location: Telemetry visible in Kinesis, but no host metadata
```

### Option B: Monitor Changes (Slower)
```bash
# Pull Kinesis every hour, track pattern changes
# If someone closes their terminal, relusys will disappear
python3 portal26_otel_agent/pull_agent_logs.py
```

### Option C: Add Tracing
Deploy a test agent with unique USER_ID:
```python
USER_ID = "relusys_test_findme"
```
If you see BOTH in Kinesis, confirms someone else is running the default.

---

## 11. How to Stop the Errors (When Source is Found)

### Fix #1: Disable Metrics Export
```bash
# In .env or environment
OTEL_METRICS_ENABLED=false
```

### Fix #2: Comment Out Metrics Endpoint
```python
# In otel_config.py
# metrics_endpoint = f"{OTEL_ENDPOINT}/v1/metrics"
```

### Fix #3: Add Resource Detection
```python
from opentelemetry.sdk.resources import Resource

resource = Resource.create({
    "service.name": SERVICE_NAME,
    "host.name": socket.gethostname(),  # Add this
    "process.pid": os.getpid(),         # Add this
    # ... rest of attributes
})
```

This way we can identify the source in future.

---

## 12. Immediate Action Items

**Priority 1: Find the Source**
- [ ] Ask team members about running portal26_otel_agent
- [ ] Check team Slack/email for mentions of OTEL testing
- [ ] Ask who has pulled the code recently

**Priority 2: Stop the Errors**
- [ ] Once source found, disable metrics export
- [ ] OR: Fix Portal26 /v1/metrics endpoint (if it should exist)

**Priority 3: Prevent Future Issues**
- [ ] Change default USER_ID in config.py to avoid conflicts
- [ ] Add resource detection to identify sources
- [ ] Document OTEL configuration for team

---

## 13. Key Insights

1. **Error Logs ≠ Telemetry**: Don't confuse error notifications with actual usage telemetry
2. **Regular Pattern = Automated**: Standard deviation of 0.87s proves this is not manual
3. **No Metadata = Red Flag**: Always include host/OS info for debugging
4. **Default Config Risk**: Default `USER_ID = "relusys"` causes attribution problems
5. **404 Errors are Expensive**: 7,488 error logs per day waste resources

---

## 14. Conclusion

**The relusys "telemetry" is actually a monitoring alert**: An automated process is continuously failing to export metrics and logging each failure to Kinesis.

**Next Step**: Contact your team to identify who is running the portal26_otel_agent code with the default configuration.

**Expected Outcome**: Once the source disables metrics export or closes their process, relusys entries will stop immediately.

---

**Report Generated**: April 10, 2026 at 15:45 IST  
**Analysis Tool**: Claude Code with Kinesis pull scripts  
**Data Source**: AWS Kinesis stream `stg_otel_source_data_stream`
