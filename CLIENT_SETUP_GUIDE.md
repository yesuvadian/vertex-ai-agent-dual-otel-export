# Client Project Setup Guide

## 📋 Overview

This guide explains what needs to be configured in **CLIENT PROJECT** to send telemetry to the central Portal26 system.

**Client Project:** `agentic-ai-integration-490716` (your Vertex AI project)  
**Telemetry Project:** `agentic-ai-integration-490716` (same project for now, can be separate)  
**Portal26 Endpoint:** `https://otel-tenant1.portal26.in:4318/v1/traces`

---

## ✅ Prerequisites

Before starting, ensure you have:
- [ ] Admin access to client project
- [ ] Vertex AI Reasoning Engine deployed and working
- [ ] Project number and ID noted down
- [ ] Service account email for telemetry worker

---

## 🔐 Required Permissions Summary

### **1. In CLIENT Project**
Grant `roles/cloudtrace.user` to telemetry worker service account:
- **Who:** `telemetry-worker@<TELEMETRY_PROJECT>.iam.gserviceaccount.com`
- **Where:** Client project IAM
- **Why:** Allow worker to read traces from your project

### **2. In TELEMETRY Project**
Grant `roles/pubsub.publisher` to Cloud Logging service account:
- **Who:** `service-<CLIENT_PROJECT_NUMBER>@gcp-sa-logging.iam.gserviceaccount.com`
- **Where:** Pub/Sub topic IAM
- **Why:** Allow your logs to be exported to central Pub/Sub

---

## 📝 Step-by-Step Setup

### Step 1: Get Your Project Information

```bash
# Get project ID (already known)
PROJECT_ID="agentic-ai-integration-490716"

# Get project NUMBER (needed for service account)
gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
# Example output: 961756870884

# Set variables
PROJECT_NUMBER="961756870884"
TELEMETRY_PROJECT="agentic-ai-integration-490716"  # Can be different
```

---

### Step 2: Enable Required APIs

```bash
# Enable Cloud Trace API (for reading traces)
gcloud services enable cloudtrace.googleapis.com \
  --project=$PROJECT_ID

# Enable Cloud Logging API (already enabled with Vertex AI)
gcloud services enable logging.googleapis.com \
  --project=$PROJECT_ID
```

**Expected output:**
```
Operation "operations/..." finished successfully.
```

---

### Step 3: Create Log Sink

**Purpose:** Export Vertex AI logs to central Pub/Sub

```bash
# Create log sink
gcloud logging sinks create telemetry-sink \
  pubsub.googleapis.com/projects/$TELEMETRY_PROJECT/topics/telemetry-logs \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="8081657304514035712"' \
  --project=$PROJECT_ID
```

**What this does:**
- Filters logs from your specific Reasoning Engine
- Routes them to Pub/Sub topic in telemetry project
- Creates a service account for the sink automatically

**Expected output:**
```
Created [https://logging.googleapis.com/v2/projects/agentic-ai-integration-490716/sinks/telemetry-sink].
```

**Note the service account created:**
```
serviceAccount:service-961756870884@gcp-sa-logging.iam.gserviceaccount.com
```

---

### Step 4: Grant Pub/Sub Publisher Permission

**Purpose:** Allow log sink to publish to Pub/Sub topic

**Run in TELEMETRY PROJECT:**

```bash
# Grant roles/pubsub.publisher to log sink service account
gcloud pubsub topics add-iam-policy-binding telemetry-logs \
  --project=$TELEMETRY_PROJECT \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-logging.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

**Expected output:**
```
Updated IAM policy for topic [telemetry-logs].
bindings:
- members:
  - serviceAccount:service-961756870884@gcp-sa-logging.iam.gserviceaccount.com
  role: roles/pubsub.publisher
```

---

### Step 5: Grant Cloud Trace Read Permission

**Purpose:** Allow telemetry worker to read traces from your project

**Run in CLIENT PROJECT:**

```bash
# Get telemetry worker service account email
WORKER_SA="telemetry-worker@${TELEMETRY_PROJECT}.iam.gserviceaccount.com"

# Grant roles/cloudtrace.user to telemetry worker
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${WORKER_SA}" \
  --role="roles/cloudtrace.user" \
  --condition=None
```

**Expected output:**
```
Updated IAM policy for project [agentic-ai-integration-490716].
bindings:
- members:
  - serviceAccount:telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com
  role: roles/cloudtrace.user
```

**Permissions granted:**
- `cloudtrace.traces.get` - Read individual traces
- `cloudtrace.traces.list` - List traces (optional)
- `cloudtrace.tasks.list` - List trace tasks (optional)

---

### Step 6: Add Tenant ID Label (Optional but Recommended)

**Purpose:** Tag logs with tenant identifier for multi-tenant isolation

**Option A: Add to Log Sink (Automatic)**

```bash
# Update log sink with tenant label
gcloud logging sinks update telemetry-sink \
  --add-exclusion='name=exclude-non-agent,filter="NOT resource.type=\"aiplatform.googleapis.com/ReasoningEngine\""' \
  --project=$PROJECT_ID
```

**Option B: Add in Agent Configuration**

Add to your agent's environment variables or code:
```python
# In agent code
import os
os.environ['TENANT_ID'] = 'tenant1'

# Or in agent deployment
labels = {
    'tenant_id': 'tenant1'
}
```

**Option C: Add via Log Entry Labels**

Logs will automatically include tenant_id if present in agent metadata.

---

### Step 7: Verify Log Sink

**Check if log sink is working:**

```bash
# Describe log sink
gcloud logging sinks describe telemetry-sink \
  --project=$PROJECT_ID

# Check for errors
gcloud logging sinks describe telemetry-sink \
  --project=$PROJECT_ID \
  --format="value(errors)"
```

**Expected output:**
```
createTime: '2026-04-03T10:00:00.000Z'
destination: pubsub.googleapis.com/projects/agentic-ai-integration-490716/topics/telemetry-logs
filter: resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="8081657304514035712"
name: telemetry-sink
writerIdentity: serviceAccount:service-961756870884@gcp-sa-logging.iam.gserviceaccount.com
```

---

### Step 8: Test End-to-End

**1. Trigger agent execution:**
```bash
# Via Vertex AI Console
https://console.cloud.google.com/vertex-ai/agents/agent-engines/8081657304514035712

# Or via API/SDK
```

**2. Check Cloud Logging:**
```bash
# View recent logs
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --project=$PROJECT_ID \
  --limit=5 \
  --format=json
```

**3. Check Pub/Sub:**
```bash
# Check if messages are being published
gcloud pubsub topics describe telemetry-logs \
  --project=$TELEMETRY_PROJECT

# Check subscription metrics
gcloud pubsub subscriptions describe telemetry-processor \
  --project=$TELEMETRY_PROJECT
```

**4. Check Telemetry Worker Logs:**
```bash
# If using Cloud Run
gcloud run logs read telemetry-worker \
  --project=$TELEMETRY_PROJECT \
  --limit=50

# If using local ngrok
tail -f flask_fixed_8082.log
```

**5. Check Portal26:**
- Login to Portal26 UI
- Search for traces from your tenant
- Verify resource attributes match

---

## 📊 IAM Permissions Table

| Permission | Resource | Principal | Purpose | Required |
|------------|----------|-----------|---------|----------|
| **roles/pubsub.publisher** | Pub/Sub topic | Log Sink SA | Export logs to Pub/Sub | ✅ Yes |
| **roles/cloudtrace.user** | Client project | Worker SA | Read traces from client | ✅ Yes |
| **roles/pubsub.subscriber** | Pub/Sub sub | Worker SA | Pull messages | ✅ Yes (internal) |
| **roles/run.invoker** | Cloud Run | Pub/Sub | Push to Cloud Run | ⚠️ Prod only |

---

## 🔍 Verification Commands

### Check Log Sink Permissions
```bash
gcloud pubsub topics get-iam-policy telemetry-logs \
  --project=$TELEMETRY_PROJECT \
  --format=json
```

**Expected:**
```json
{
  "bindings": [
    {
      "members": [
        "serviceAccount:service-961756870884@gcp-sa-logging.iam.gserviceaccount.com"
      ],
      "role": "roles/pubsub.publisher"
    }
  ]
}
```

### Check Cloud Trace Permissions
```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:telemetry-worker@"
```

**Expected:**
```
ROLE
roles/cloudtrace.user
```

### Test Log Export
```bash
# Generate a test log
gcloud logging write test-log "Test message" \
  --resource=aiplatform.googleapis.com/ReasoningEngine \
  --severity=INFO \
  --project=$PROJECT_ID

# Wait a few seconds, then check Pub/Sub
gcloud pubsub subscriptions pull telemetry-processor \
  --project=$TELEMETRY_PROJECT \
  --limit=1 \
  --auto-ack
```

---

## 🐛 Troubleshooting

### Issue 1: Logs not appearing in Pub/Sub

**Check:**
```bash
# 1. Is log sink created?
gcloud logging sinks list --project=$PROJECT_ID

# 2. Does it have errors?
gcloud logging sinks describe telemetry-sink \
  --project=$PROJECT_ID \
  --format="value(errors)"

# 3. Does Logging SA have pubsub.publisher?
gcloud pubsub topics get-iam-policy telemetry-logs \
  --project=$TELEMETRY_PROJECT | grep "service-${PROJECT_NUMBER}"
```

**Fix:**
- Re-run Step 4 to grant publisher permission
- Check log filter matches your Reasoning Engine ID

---

### Issue 2: Worker can't fetch traces (403 Forbidden)

**Check:**
```bash
# Does worker SA have cloudtrace.user?
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:telemetry-worker@" \
  --format="value(bindings.role)"
```

**Fix:**
- Re-run Step 5 to grant cloudtrace.user
- Verify worker service account email is correct

---

### Issue 3: Traces found but not processed

**Check:**
```bash
# Check worker logs for errors
gcloud run logs read telemetry-worker \
  --project=$TELEMETRY_PROJECT \
  --limit=100 | grep ERROR
```

**Common issues:**
- Span ID conversion (fixed in otel_transformer.py)
- Portal26 authentication (check .env file)
- Network connectivity to Portal26

---

## 📋 Configuration Checklist

**Before production, verify:**

- [ ] Log sink created and active
- [ ] Log sink service account has pubsub.publisher on topic
- [ ] Worker service account has cloudtrace.user on client project
- [ ] Reasoning Engine ID in log filter is correct
- [ ] Tenant ID is set (label or attribute)
- [ ] Test trace successfully processed end-to-end
- [ ] Traces appear in Portal26 UI
- [ ] Resource attributes are correct (tenant_id, project_id)
- [ ] No error logs in Cloud Logging
- [ ] Pub/Sub has no undelivered messages

---

## 🔄 Multi-Tenant Setup (Multiple Clients)

**For each additional client project:**

1. Repeat Steps 1-5 with new project ID/number
2. Use same Pub/Sub topic (central buffer)
3. Grant cloudtrace.user to same worker SA
4. Use different tenant_id for isolation

**No restart needed!** Worker picks up new tenants automatically.

---

## 📞 Support

**If issues persist:**

1. Check all commands in this guide
2. Review worker logs: `tail -f flask_fixed_8082.log`
3. Check ARCHITECTURE_EXPLAINED.md for detailed flow
4. Verify TESTING_GUIDE.md scenarios

**Key files:**
- `ARCHITECTURE_FINAL.md` - Complete design with IAM
- `CLIENT_SETUP_GUIDE.md` - This file
- `TESTING_GUIDE.md` - Test scenarios
- `SUCCESS_SUMMARY.md` - Current working status

---

## ✅ Summary

**What you configured:**

1. ✅ **Log Sink** - Routes Vertex AI logs to Pub/Sub
2. ✅ **Pub/Sub Publisher** - Logging SA can publish messages
3. ✅ **Cloud Trace Reader** - Worker SA can read traces
4. ✅ **Tenant Labeling** - Logs tagged with tenant_id

**What happens now:**

```
Vertex AI Agent → Log → Cloud Logging → Log Sink → Pub/Sub 
    → Telemetry Worker → Cloud Trace API → OTEL Transform 
    → Portal26 Export ✅
```

**Next steps:**
- Test with real agent queries
- Verify traces in Portal26
- Monitor for errors
- Scale to production
