# Deployment Complete - Telemetry Worker

**Date:** 2026-04-03  
**Status:** ✅ DEPLOYED (with some permission limitations)

---

## 🎉 Successfully Deployed

###  1. Container Image Built
- **Image:** `gcr.io/agentic-ai-integration-490716/telemetry-worker:v1`
- **Build ID:** `4cbd751b-e7c3-4634-a3c9-cfde0f300dac`
- **Status:** ✅ SUCCESS

### 2. Cloud Run Service Deployed
- **Service Name:** `telemetry-worker`
- **URL:** `https://telemetry-worker-961756870884.us-central1.run.app`
- **Project:** `agentic-ai-integration-490716`
- **Region:** `us-central1`
- **Service Account:** `telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com`
- **Status:** ✅ RUNNING

**Configuration:**
```
PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318/v1/traces
PORTAL26_USERNAME=titaniam
PORTAL26_PASSWORD=helloworld (in env var - not secret)
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1
OTEL_LOG_USER_PROMPTS=1
```

**Scaling:**
- Min instances: 1
- Max instances: 100
- Concurrency: 80
- CPU: 2
- Memory: 1Gi
- Timeout: 60s

### 3. Pub/Sub Infrastructure Created
- **Topic:** `vertex-telemetry-topic`
  - Message retention: 7 days
  - Project: `agentic-ai-integration-490716`
  
- **Subscription:** `telemetry-processor`
  - Type: Push
  - Endpoint: `https://telemetry-worker-961756870884.us-central1.run.app/process`
  - Ack deadline: 60s
  - Project: `agentic-ai-integration-490716`

### 4. Service Account Created
- **Name:** `telemetry-worker`
- **Email:** `telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com`

### 5. Secrets Created
- **portal26-user:** Contains `titaniam`
- **portal26-pass:** Contains `helloworld`

---

## ⚠️ Permission Issues (Requires Admin)

### Issue 1: Cloud Run Unauthenticated Access

**Problem:** Cloud Run service requires authentication  
**Current Status:** Returns 403 Forbidden on health endpoint  
**Needed:** Grant `roles/run.invoker` to `allUsers`

**Command (requires admin):**
```bash
gcloud run services add-iam-policy-binding telemetry-worker \
  --region=us-central1 \
  --member=allUsers \
  --role=roles/run.invoker \
  --project=agentic-ai-integration-490716
```

**Why Needed:** Pub/Sub needs to invoke Cloud Run without authentication

---

### Issue 2: Secret Manager Access

**Problem:** Service account can't access secrets  
**Current Status:** Using environment variables (less secure)  
**Needed:** Grant `roles/secretmanager.secretAccessor` to service account

**Command (requires admin):**
```bash
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Why Needed:** To use secrets instead of environment variables for credentials

---

### Issue 3: Cloud Trace API Access

**Problem:** Service account needs to read traces from this project  
**Current Status:** Not granted yet  
**Needed:** Grant `roles/cloudtrace.user` to service account

**Command (requires admin):**
```bash
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.user"
```

**Why Needed:** To fetch traces from Cloud Trace API

---

## 📋 Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Container Image | ✅ Built | `gcr.io/agentic-ai-integration-490716/telemetry-worker:v1` |
| Cloud Run Service | ✅ Deployed | Requires authentication (403 on /health) |
| Pub/Sub Topic | ✅ Created | `vertex-telemetry-topic` |
| Pub/Sub Subscription | ✅ Created | `telemetry-processor` → Cloud Run |
| Service Account | ✅ Created | `telemetry-worker` |
| Portal26 Config | ✅ Configured | Endpoint + credentials in env vars |
| Unauthenticated Access | ❌ Blocked | Needs admin to grant IAM policy |
| Secret Access | ❌ Blocked | Using env vars instead |
| Cloud Trace Access | ❌ Not granted | Needs admin to grant IAM policy |

---

## 🧪 Testing (After Permissions Granted)

### Test 1: Health Check

```bash
curl https://telemetry-worker-961756870884.us-central1.run.app/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "telemetry-worker",
  "version": "1.0.0"
}
```

### Test 2: Check Logs

```bash
gcloud run services logs read telemetry-worker \
  --project=agentic-ai-integration-490716 \
  --region=us-central1 \
  --limit=50
```

### Test 3: Send Test Message

```bash
cd telemetry_worker
python test_local.py \
  agentic-ai-integration-490716 \
  <trace_id> \
  test_tenant \
  https://telemetry-worker-961756870884.us-central1.run.app/process
```

---

## 🚀 Next Steps

### Immediate (Requires Admin Permissions)

1. **Grant unauthenticated access to Cloud Run:**
   ```bash
   gcloud run services add-iam-policy-binding telemetry-worker \
     --region=us-central1 \
     --member=allUsers \
     --role=roles/run.invoker \
     --project=agentic-ai-integration-490716
   ```

2. **Grant Cloud Trace access:**
   ```bash
   gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
     --member="serviceAccount:telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com" \
     --role="roles/cloudtrace.user"
   ```

3. **Test health endpoint:**
   ```bash
   curl https://telemetry-worker-961756870884.us-central1.run.app/health
   ```

### After Permissions Granted

4. **Configure Log Sink on this project (test client):**
   ```bash
   gcloud logging sinks create vertex-ai-telemetry-sink \
     pubsub.googleapis.com/projects/agentic-ai-integration-490716/topics/vertex-telemetry-topic \
     --project=agentic-ai-integration-490716 \
     --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine"'
   ```

5. **Add tenant_id label to log sink:**
   ```bash
   gcloud logging sinks update vertex-ai-telemetry-sink \
     --project=agentic-ai-integration-490716 \
     --add-labels=tenant_id=test_tenant_001
   ```

6. **Grant Pub/Sub publisher to Logging SA:**
   ```bash
   WRITER_SA=$(gcloud logging sinks describe vertex-ai-telemetry-sink \
     --project=agentic-ai-integration-490716 \
     --format='value(writerIdentity)')
   
   gcloud pubsub topics add-iam-policy-binding vertex-telemetry-topic \
     --project=agentic-ai-integration-490716 \
     --member="$WRITER_SA" \
     --role="roles/pubsub.publisher"
   ```

7. **Test with gcp_traces_agent:**
   - Use existing agent: `8081657304514035712`
   - Send test query via Console UI
   - Logs should flow: Agent → Cloud Logging → Log Sink → Pub/Sub → Cloud Run → Portal26

8. **Verify in Portal26:**
   - Login to Portal26
   - Check for traces with:
     - `portal26.user.id=relusys`
     - `portal26.tenant_id=tenant1`
     - `tenant.id=test_tenant_001`

---

## 📊 Architecture Deployed

```
[Current Setup - Single Project]

┌─────────────────────────────────────────────────────────────┐
│         Project: agentic-ai-integration-490716              │
│                                                             │
│  gcp_traces_agent (Vertex AI Agent)                        │
│         ↓                                                   │
│  Cloud Logging                                              │
│         ↓                                                   │
│  Log Sink (to be created)                                   │
│         ↓                                                   │
│  Pub/Sub Topic: vertex-telemetry-topic ✅                   │
│         ↓                                                   │
│  Pub/Sub Subscription: telemetry-processor ✅               │
│         ↓                                                   │
│  Cloud Run: telemetry-worker ✅                             │
│    (requires auth currently - needs fix)                    │
│         ↓                                                   │
│  Cloud Trace API (to fetch traces)                          │
│    (needs cloudtrace.user role)                             │
│         ↓                                                   │
│  Transform to OTEL                                          │
│         ↓                                                   │
│  Export to Portal26                                         │
│    https://otel-tenant1.portal26.in:4318/v1/traces         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Notes

**Current Setup:**
- ❌ Portal26 credentials in environment variables (visible in Cloud Run console)
- ❌ Cloud Run requires authentication (can't receive Pub/Sub messages)
- ❌ Service account can't access Cloud Trace

**After Admin Grants Permissions:**
- ✅ Can move credentials to Secret Manager
- ✅ Cloud Run accepts Pub/Sub push messages
- ✅ Can fetch traces from Cloud Trace API

---

## 💰 Cost Estimate

**Monthly costs (estimated for 1M agent invocations):**

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Run | 1M requests, 100ms avg, 2 CPU, 1GB | ~$30 |
| Pub/Sub | 10M messages (10 per invocation) | ~$5 |
| Cloud Trace API | 1M GetTrace calls | ~$4 |
| Cloud Logging | 20GB logs | ~$10 |
| Secret Manager | 2 secrets, minimal access | ~$0.10 |
| **Total** | | **~$49/month** |

---

## 📞 Admin Actions Required

Please have an admin run these commands:

```bash
# 1. Allow unauthenticated access to Cloud Run
gcloud run services add-iam-policy-binding telemetry-worker \
  --region=us-central1 \
  --member=allUsers \
  --role=roles/run.invoker \
  --project=agentic-ai-integration-490716

# 2. Grant Cloud Trace access
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.user"

# 3. (Optional) Grant Secret Manager access
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**After these are granted, the telemetry worker will be fully functional.**

---

## ✅ What Works Now

- ✅ Container image built and pushed
- ✅ Cloud Run service deployed and running
- ✅ Pub/Sub topic and subscription created
- ✅ Portal26 endpoint configured
- ✅ Service account created

## ⏳ What Needs Admin Permissions

- ❌ Unauthenticated access to Cloud Run (for Pub/Sub)
- ❌ Cloud Trace API access (to fetch traces)
- ❌ Secret Manager access (for secure credentials)

**Once permissions are granted, system will be fully operational.**
