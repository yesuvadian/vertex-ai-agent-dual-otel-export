# IAM Commands - Quick Reference

## 🚀 Quick Setup (Copy-Paste Ready)

### Variables Setup
```bash
# YOUR VALUES - UPDATE THESE
CLIENT_PROJECT_ID="agentic-ai-integration-490716"
CLIENT_PROJECT_NUMBER="961756870884"
TELEMETRY_PROJECT="agentic-ai-integration-490716"
REASONING_ENGINE_ID="8081657304514035712"
TENANT_ID="tenant1"

# DERIVED VALUES - DON'T CHANGE
LOGGING_SA="service-${CLIENT_PROJECT_NUMBER}@gcp-sa-logging.iam.gserviceaccount.com"
WORKER_SA="telemetry-worker@${TELEMETRY_PROJECT}.iam.gserviceaccount.com"
```

---

## 📋 All Commands in Order

### 1. Enable APIs
```bash
gcloud services enable cloudtrace.googleapis.com --project=$CLIENT_PROJECT_ID
gcloud services enable logging.googleapis.com --project=$CLIENT_PROJECT_ID
gcloud services enable pubsub.googleapis.com --project=$TELEMETRY_PROJECT
gcloud services enable run.googleapis.com --project=$TELEMETRY_PROJECT
```

### 2. Create Pub/Sub Topic (Telemetry Project)
```bash
gcloud pubsub topics create telemetry-logs \
  --project=$TELEMETRY_PROJECT \
  --message-retention-duration=7d
```

### 3. Create Pub/Sub Subscription (Telemetry Project)
```bash
gcloud pubsub subscriptions create telemetry-processor \
  --topic=telemetry-logs \
  --project=$TELEMETRY_PROJECT \
  --ack-deadline=600 \
  --message-retention-duration=7d \
  --push-endpoint="https://YOUR_NGROK_OR_CLOUDRUN_URL/process"
```

### 4. Create Log Sink (Client Project)
```bash
gcloud logging sinks create telemetry-sink \
  pubsub.googleapis.com/projects/${TELEMETRY_PROJECT}/topics/telemetry-logs \
  --log-filter="resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND resource.labels.reasoning_engine_id=\"${REASONING_ENGINE_ID}\"" \
  --project=$CLIENT_PROJECT_ID
```

### 5. Grant Pub/Sub Publisher (Telemetry Project)
```bash
gcloud pubsub topics add-iam-policy-binding telemetry-logs \
  --project=$TELEMETRY_PROJECT \
  --member="serviceAccount:${LOGGING_SA}" \
  --role="roles/pubsub.publisher"
```

### 6. Grant Cloud Trace User (Client Project)
```bash
gcloud projects add-iam-policy-binding $CLIENT_PROJECT_ID \
  --member="serviceAccount:${WORKER_SA}" \
  --role="roles/cloudtrace.user"
```

### 7. Create Service Account for Worker (if not exists)
```bash
gcloud iam service-accounts create telemetry-worker \
  --display-name="Telemetry Worker Service Account" \
  --project=$TELEMETRY_PROJECT
```

### 8. Grant Pub/Sub Subscriber to Worker (Telemetry Project)
```bash
gcloud pubsub subscriptions add-iam-policy-binding telemetry-processor \
  --project=$TELEMETRY_PROJECT \
  --member="serviceAccount:${WORKER_SA}" \
  --role="roles/pubsub.subscriber"
```

### 9. Grant Cloud Run Invoker (Production Only)
```bash
# For Pub/Sub to invoke Cloud Run
gcloud run services add-iam-policy-binding telemetry-worker \
  --member="serviceAccount:service-${TELEMETRY_PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=us-central1 \
  --project=$TELEMETRY_PROJECT
```

---

## ✅ Verification Commands

### Check Log Sink
```bash
gcloud logging sinks describe telemetry-sink --project=$CLIENT_PROJECT_ID
```

### Check Pub/Sub Topic IAM
```bash
gcloud pubsub topics get-iam-policy telemetry-logs --project=$TELEMETRY_PROJECT
```

### Check Cloud Trace IAM
```bash
gcloud projects get-iam-policy $CLIENT_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:telemetry-worker@" \
  --format="table(bindings.role)"
```

### Check Pub/Sub Subscription
```bash
gcloud pubsub subscriptions describe telemetry-processor --project=$TELEMETRY_PROJECT
```

### Test Log Export
```bash
# Trigger agent, then check Pub/Sub
gcloud pubsub subscriptions pull telemetry-processor \
  --project=$TELEMETRY_PROJECT \
  --limit=1 \
  --format=json
```

---

## 🔄 Update Commands

### Update Log Sink Filter
```bash
gcloud logging sinks update telemetry-sink \
  --log-filter="resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND resource.labels.reasoning_engine_id=\"${REASONING_ENGINE_ID}\"" \
  --project=$CLIENT_PROJECT_ID
```

### Update Pub/Sub Push Endpoint
```bash
gcloud pubsub subscriptions update telemetry-processor \
  --push-endpoint="https://NEW_URL/process" \
  --project=$TELEMETRY_PROJECT
```

---

## ❌ Cleanup Commands

### Remove Log Sink
```bash
gcloud logging sinks delete telemetry-sink --project=$CLIENT_PROJECT_ID
```

### Remove IAM Bindings
```bash
# Remove pubsub.publisher
gcloud pubsub topics remove-iam-policy-binding telemetry-logs \
  --project=$TELEMETRY_PROJECT \
  --member="serviceAccount:${LOGGING_SA}" \
  --role="roles/pubsub.publisher"

# Remove cloudtrace.user
gcloud projects remove-iam-policy-binding $CLIENT_PROJECT_ID \
  --member="serviceAccount:${WORKER_SA}" \
  --role="roles/cloudtrace.user"
```

---

## 📊 IAM Summary Table

| Permission | Granted On | Granted To | Command |
|------------|------------|------------|---------|
| **pubsub.publisher** | Topic: telemetry-logs | Logging SA | #5 above |
| **cloudtrace.user** | Project: CLIENT | Worker SA | #6 above |
| **pubsub.subscriber** | Sub: telemetry-processor | Worker SA | #8 above |
| **run.invoker** | Cloud Run: telemetry-worker | Pub/Sub SA | #9 above |

---

## 🔐 Service Accounts Reference

### Client Project
```
Cloud Logging Service Account:
  service-{PROJECT_NUMBER}@gcp-sa-logging.iam.gserviceaccount.com
  
Example:
  service-961756870884@gcp-sa-logging.iam.gserviceaccount.com
```

### Telemetry Project
```
Worker Service Account:
  telemetry-worker@{PROJECT_ID}.iam.gserviceaccount.com
  
Example:
  telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com

Pub/Sub Service Account (for Cloud Run):
  service-{PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com
```

---

## 🎯 Current Setup Status

### Completed ✅
- [x] APIs enabled
- [x] Pub/Sub topic created
- [x] Pub/Sub subscription created
- [x] Log sink created
- [x] pubsub.publisher granted
- [x] cloudtrace.user granted (for local testing)
- [x] Worker running on port 8082
- [x] ngrok tunnel active
- [x] Pub/Sub pointing to ngrok
- [x] End-to-end test successful

### Pending (For Production) ⏳
- [ ] Create dedicated service account for worker
- [ ] Deploy to Cloud Run
- [ ] Grant run.invoker to Pub/Sub SA
- [ ] Update subscription to Cloud Run endpoint
- [ ] Remove ngrok dependency

---

## 📝 Notes

**Current Working Setup:**
- Worker running locally on port 8082
- Using your personal gcloud credentials (ADC)
- ngrok tunnel: https://tabetha-unelemental-bibulously.ngrok-free.dev
- Pub/Sub subscription pushing to ngrok
- Successfully processing and exporting traces

**For Production:**
- Deploy worker to Cloud Run
- Create service account with proper IAM
- Update Pub/Sub to push to Cloud Run
- Monitor in Cloud Logging

**Multi-Tenant:**
- Each client repeats commands 4, 5, 6
- Same Pub/Sub topic and worker
- Different tenant_id labels
- No restart needed

---

## 🚨 Important Security Notes

1. **Never use `allUsers` or `allAuthenticatedUsers`**
   - Always grant to specific service accounts

2. **Use least privilege**
   - `cloudtrace.user` (not admin)
   - `pubsub.publisher` (not editor)

3. **Per-project grants**
   - Don't use wildcards
   - Explicit per-client binding

4. **Service account keys**
   - Never download service account keys
   - Use Workload Identity or ADC

5. **Review periodically**
   ```bash
   gcloud projects get-iam-policy $PROJECT_ID
   ```

---

## 📞 Quick Help

**Get project number:**
```bash
gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
```

**List all sinks:**
```bash
gcloud logging sinks list --project=$PROJECT_ID
```

**View recent logs:**
```bash
gcloud logging read "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\"" \
  --project=$PROJECT_ID --limit=10
```

**Check Pub/Sub metrics:**
```bash
gcloud pubsub topics describe telemetry-logs --project=$TELEMETRY_PROJECT
gcloud pubsub subscriptions describe telemetry-processor --project=$TELEMETRY_PROJECT
```
