# Push-Based Forwarder (Cloud Function)

## What This Is

A **serverless, event-driven** forwarder that automatically processes Pub/Sub messages and forwards them to Portal26.

**Key Difference from Pull-Based:**
- ❌ No server running 24/7
- ✅ Cloud Function triggered automatically when messages arrive
- ✅ Pay only when messages are processed
- ✅ Fully managed by Google Cloud

---

## Architecture

```
Message arrives in Pub/Sub
        ↓ (automatic trigger)
Cloud Function starts
        ↓ (processes message)
Forwards to Portal26
        ↓ (completes)
Cloud Function terminates
        ↓
No cost until next message!
```

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `main.py` | Cloud Function code (processes messages) |
| `requirements.txt` | Python dependencies |
| `deploy.bat` | Windows deployment script |
| `deploy.sh` | Linux/Mac deployment script |
| `test_function.sh` | Test and view logs |
| `README.md` | This file |

---

## Deployment (3 Steps)

### Step 1: Enable Cloud Functions API

```bash
gcloud services enable cloudfunctions.googleapis.com --project=agentic-ai-integration-490716
gcloud services enable cloudbuild.googleapis.com --project=agentic-ai-integration-490716
```

### Step 2: Deploy Cloud Function

**Windows:**
```bash
cd C:\Yesu\ai_agent_projectgcp\push_based_forwarder
deploy.bat
```

**Linux/Mac:**
```bash
cd push_based_forwarder
chmod +x deploy.sh
./deploy.sh
```

**Manual:**
```bash
gcloud functions deploy vertex-to-portal26 \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --source . \
  --entry-point pubsub_to_portal26 \
  --trigger-topic vertex-telemetry-topic \
  --set-env-vars PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318 \
  --set-env-vars PORTAL26_AUTH="Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  --set-env-vars TENANT_ID=tenant1 \
  --set-env-vars USER_ID=relusys_terraform \
  --set-env-vars SERVICE_NAME=gcp-vertex-monitor \
  --max-instances 10 \
  --timeout 60s \
  --memory 256MB \
  --project agentic-ai-integration-490716
```

**Deployment takes:** ~3-5 minutes

### Step 3: Test It

1. **Trigger your Reasoning Engine** (send a test query)
2. **Wait 1-2 minutes** for logs to flow
3. **Check Cloud Function logs:**
   ```bash
   gcloud functions logs read vertex-to-portal26 \
     --region us-central1 \
     --gen2 \
     --project agentic-ai-integration-490716 \
     --limit 10
   ```
4. **Check Portal26 dashboard:**
   - Query: `service.name = "gcp-vertex-monitor"`
   - Source should show: `cloud-function`

---

## How It Works

1. **Message arrives** in `vertex-telemetry-topic`
2. **Pub/Sub automatically triggers** the Cloud Function
3. **Cloud Function:**
   - Decodes the message
   - Filters for Reasoning Engine logs
   - Converts to OTEL format
   - Sends to Portal26
4. **Function terminates** (no cost until next message)

**Total latency:** ~1-3 seconds per message

---

## Viewing Logs

### Real-time logs:
```bash
gcloud functions logs read vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --follow
```

### Recent logs:
```bash
gcloud functions logs read vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --limit 20
```

### In GCP Console:
1. Go to: https://console.cloud.google.com/functions
2. Select project: `agentic-ai-integration-490716`
3. Click: `vertex-to-portal26`
4. Click: **Logs** tab

---

## Monitoring

### Check Function Status:
```bash
gcloud functions describe vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --project agentic-ai-integration-490716
```

### Expected output:
```
name: projects/.../functions/vertex-to-portal26
state: ACTIVE
serviceConfig:
  service: vertex-to-portal26
  timeoutSeconds: 60
  availableMemory: 256M
  environmentVariables:
    PORTAL26_ENDPOINT: https://otel-tenant1.portal26.in:4318
    ...
```

### Metrics in GCP Console:
- Invocations count
- Execution time
- Memory usage
- Error rate

---

## Configuration

All configuration is in environment variables (set during deployment):

```bash
PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318
PORTAL26_AUTH=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
TENANT_ID=tenant1
USER_ID=relusys_terraform
SERVICE_NAME=gcp-vertex-monitor
```

**To update configuration:**
```bash
gcloud functions deploy vertex-to-portal26 \
  --gen2 \
  --region us-central1 \
  --update-env-vars PORTAL26_ENDPOINT=new-value \
  --project agentic-ai-integration-490716
```

---

## Cost

### Cloud Function Pricing:
```
Invocations: $0.40 per million
Compute time: $0.0000025 per 100ms (256MB memory)
Network egress: $0.12 per GB

Example:
10,000 logs/day = 300,000 logs/month
300,000 invocations × $0.40/million = $0.12
Compute time (assume 200ms each): ~$1.50
Total: ~$2-3/month
```

**Much cheaper than pull-based ($15/month) for low-moderate volume!**

---

## Comparison: Push vs Pull

| Feature | Push (Cloud Function) | Pull (Continuous) |
|---------|----------------------|-------------------|
| **Server** | None (serverless) | Always running |
| **Cost** | $2-3/month (variable) | $15/month (fixed) |
| **Trigger** | Automatic | Continuous poll |
| **Scaling** | Automatic (0-N) | Manual |
| **Latency** | 1-3 seconds | 2-5 seconds |
| **Cold Start** | Yes (~1-5 sec) | No |
| **Debugging** | Cloud logs | Local logs |
| **Best for** | Variable workload | Consistent workload |

---

## Troubleshooting

### Function not triggering?

**Check 1: Function exists and is active**
```bash
gcloud functions describe vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --project agentic-ai-integration-490716
```

Should show: `state: ACTIVE`

**Check 2: Pub/Sub topic has messages**
```bash
gcloud pubsub subscriptions pull vertex-telemetry-subscription \
  --limit=1 \
  --project agentic-ai-integration-490716
```

**Check 3: Function has proper permissions**
The Cloud Function service account needs permission to be invoked by Pub/Sub (automatically granted during deployment).

### Logs show errors?

**Common errors:**

**"PORTAL26_ENDPOINT not configured"**
- Solution: Redeploy with environment variables

**"Portal26 returned error: 401"**
- Solution: Check PORTAL26_AUTH is correct
- Verify: `echo "dGl0YW5pYW06aGVsbG93b3JsZA==" | base64 -d` → should output `titaniam:helloworld`

**"Failed to send to Portal26: timeout"**
- Solution: Check Portal26 endpoint is accessible
- Test: `curl -X POST https://otel-tenant1.portal26.in:4318/v1/logs`

### No logs in Portal26?

1. **Check Cloud Function logs** - Is it processing messages?
2. **Check Portal26 endpoint** - Is it responding?
3. **Check filter** - Function only forwards Reasoning Engine logs

---

## Updating the Function

### Update code:
1. Edit `main.py`
2. Run `deploy.bat` or `deploy.sh` again

### Update configuration:
```bash
gcloud functions deploy vertex-to-portal26 \
  --gen2 \
  --region us-central1 \
  --update-env-vars KEY=VALUE \
  --project agentic-ai-integration-490716
```

### Delete function:
```bash
gcloud functions delete vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --project agentic-ai-integration-490716
```

---

## Testing

### Manual test (simulate Pub/Sub message):
```bash
# Encode a test log entry
TEST_DATA=$(echo '{"resource":{"type":"aiplatform.googleapis.com/ReasoningEngine","labels":{"reasoning_engine_id":"test-123"}},"severity":"INFO","jsonPayload":{"content":"test"}}' | base64)

# Trigger function
gcloud functions call vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --data '{"data":"'$TEST_DATA'"}' \
  --project agentic-ai-integration-490716
```

### Real test:
1. Trigger Reasoning Engine
2. Check Cloud Function logs in 1-2 minutes
3. Verify in Portal26 dashboard

---

## Next Steps

### After Deployment:

1. ✅ **Monitor logs** for first few invocations
2. ✅ **Verify in Portal26** that logs are arriving
3. ✅ **Set up alerts** in GCP for function failures
4. ✅ **Compare with pull-based** - which works better for you?

### Optional Enhancements:

- Add retry logic for Portal26 failures
- Implement batching (accumulate multiple messages)
- Add Cloud Monitoring metrics
- Set up error alerting via Cloud Monitoring

---

## Support

**Cloud Function Issues:**
- Logs: `gcloud functions logs read vertex-to-portal26 --region us-central1 --gen2`
- Status: Check GCP Console → Cloud Functions

**Portal26 Issues:**
- Test connection: `test_portal26_connection.py` (in monitoring_setup folder)
- Check auth credentials
- Verify endpoint URL

**Deployment Issues:**
- Ensure Cloud Functions API is enabled
- Check IAM permissions
- Verify gcloud is authenticated

---

## Summary

✅ **Serverless** - No server to manage
✅ **Event-driven** - Triggered automatically by Pub/Sub
✅ **Cost-effective** - Pay only for invocations
✅ **Scalable** - Handles 0 to thousands of messages
✅ **Simple** - Just 2 files (main.py + requirements.txt)

**Perfect for:** Variable workload, low-moderate log volume, serverless architecture

**Deployment time:** 5 minutes
**Maintenance:** Zero (fully managed)

---

**Ready to deploy!** Just run `deploy.bat` or `deploy.sh` 🚀
