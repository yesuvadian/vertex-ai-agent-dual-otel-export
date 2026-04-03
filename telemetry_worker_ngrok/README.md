# Telemetry Worker - Local Testing with ngrok

**Local development and testing setup - no Cloud Run permissions needed!**

---

## 🎯 Purpose

Test the telemetry worker locally using ngrok to:
- ✅ Bypass Cloud Run permission issues
- ✅ See real-time logs in terminal
- ✅ Test Portal26 export immediately
- ✅ Debug and iterate quickly
- ✅ Verify full flow end-to-end

**Folder structure:**
- `telemetry_worker/` - Production Cloud Run deployment
- `telemetry_worker_ngrok/` - **Local testing** (this folder)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd telemetry_worker_ngrok
pip install -r requirements.txt
```

### 2. Start Flask App

**Terminal 1:**
```bash
python main.py
```

**Expected:**
```
INFO:__main__:TraceProcessor initialized successfully
INFO:werkzeug: * Running on http://0.0.0.0:8080
```

### 3. Start ngrok

**Terminal 2:**
```bash
ngrok http 8080
```

**Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)

### 4. Update Pub/Sub Subscription

**Terminal 3:**
```bash
# Replace with your ngrok URL
NGROK_URL="https://abc123.ngrok.io"

# Point Pub/Sub to your local ngrok
gcloud pubsub subscriptions update telemetry-processor \
  --push-endpoint="${NGROK_URL}/process" \
  --project=agentic-ai-integration-490716

# Verify
gcloud pubsub subscriptions describe telemetry-processor \
  --project=agentic-ai-integration-490716 \
  --format="value(pushConfig.pushEndpoint)"
```

---

## 🧪 Testing

### Test 1: Direct POST

```bash
# Test with real trace ID
python test_local.py \
  agentic-ai-integration-490716 \
  677b68ce5e429ca85cdc16ef54631ee6 \
  test_tenant_local \
  ${NGROK_URL}/process
```

**Expected:** Status 200, logs in Terminal 1

---

### Test 2: Pub/Sub → ngrok

```bash
# Publish test message
cat > test_log.json <<EOF
{
  "insertId": "test-$(date +%s)",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "trace": "projects/agentic-ai-integration-490716/traces/677b68ce5e429ca85cdc16ef54631ee6",
  "labels": {"tenant_id": "test_pubsub"},
  "resource": {
    "type": "aiplatform.googleapis.com/ReasoningEngine",
    "labels": {
      "project_id": "agentic-ai-integration-490716",
      "reasoning_engine_id": "8081657304514035712",
      "location": "us-central1"
    }
  }
}
EOF

gcloud pubsub topics publish vertex-telemetry-topic \
  --project=agentic-ai-integration-490716 \
  --message="$(cat test_log.json | base64)"

# Watch Terminal 1 for processing
```

---

### Test 3: Full Flow with Agent

```bash
# Setup log sink (one time)
gcloud logging sinks create vertex-ai-telemetry-sink \
  pubsub.googleapis.com/projects/agentic-ai-integration-490716/topics/vertex-telemetry-topic \
  --project=agentic-ai-integration-490716 \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  2>&1 || echo "Sink already exists"

# Grant Pub/Sub publisher (one time)
WRITER_SA=$(gcloud logging sinks describe vertex-ai-telemetry-sink \
  --project=agentic-ai-integration-490716 \
  --format='value(writerIdentity)')

gcloud pubsub topics add-iam-policy-binding vertex-telemetry-topic \
  --project=agentic-ai-integration-490716 \
  --member="$WRITER_SA" \
  --role="roles/pubsub.publisher"

# Invoke agent via Console UI
# https://console.cloud.google.com/vertex-ai/agents/agent-engines/8081657304514035712
# Send: "What is the weather in Tokyo?"

# Watch Terminal 1 for automatic processing!
```

---

## 📊 What You'll See

**Terminal 1 (Flask):**
```
INFO:__main__:Processing message test-message-123, insertId: test-123
INFO:trace_processor:Processing trace 677b68ce... for tenant test_pubsub
INFO:trace_fetcher:Fetching trace: projects/.../traces/677b68ce...
INFO:trace_fetcher:Fetched trace 677b68ce... with 5 spans
INFO:otel_transformer:Transformed 5 spans to OTEL format
INFO:portal26_exporter:Exporting 5 spans for tenant test_pubsub
INFO:portal26_exporter:Successfully exported traces for tenant test_pubsub
```

**Terminal 2 (ngrok):**
- Live HTTP traffic dashboard
- Request/response inspection
- Open: http://localhost:4040

---

## 🔍 Monitoring

### ngrok Dashboard

Open: `http://localhost:4040`

Shows:
- All incoming requests
- Request headers and body
- Response status
- Timing

### Flask Logs

Watch Terminal 1 for:
- Pub/Sub message delivery
- Trace processing
- Portal26 export status
- Any errors

---

## 🛠 Configuration

### Environment Variables (.env)

```bash
# Portal26 Endpoint
PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318/v1/traces

# Basic Auth
PORTAL26_USERNAME=titaniam
PORTAL26_PASSWORD=helloworld

# Resource Attributes
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1

# Other Settings
OTEL_LOG_USER_PROMPTS=1
PORTAL26_TIMEOUT=30
DEDUP_CACHE_TTL=3600
LOG_LEVEL=INFO
```

### GCP Credentials

For Cloud Trace API access:

```bash
# Option 1: Use your user credentials
gcloud auth application-default login

# Option 2: Use service account key
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

---

## 🧹 Cleanup

When done testing:

```bash
# Stop Flask (Terminal 1)
Ctrl+C

# Stop ngrok (Terminal 2)
Ctrl+C

# Point Pub/Sub back to Cloud Run
gcloud pubsub subscriptions update telemetry-processor \
  --push-endpoint="https://telemetry-worker-961756870884.us-central1.run.app/process" \
  --project=agentic-ai-integration-490716
```

---

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Install dependencies
pip install -r requirements.txt
```

### Issue: ngrok 403 Forbidden

Free ngrok may require browser verification.

**Fix:** Get ngrok authtoken from https://ngrok.com/
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### Issue: Permission Denied on Cloud Trace

```bash
# Login with application-default
gcloud auth application-default login

# Or grant your user cloudtrace.user role
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/cloudtrace.user"
```

### Issue: Port 8080 Already in Use

```bash
# Kill process on port 8080
# Windows:
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Change port in main.py (last line):
port = int(os.environ.get('PORT', 8081))
```

---

## 📝 Files

- `main.py` - Flask app with /process endpoint
- `trace_processor.py` - Core processing logic
- `trace_fetcher.py` - Cloud Trace API client
- `otel_transformer.py` - GCP → OTEL transformation
- `portal26_exporter.py` - Export to Portal26
- `dedup_cache.py` - Deduplication cache
- `config.py` - Configuration management
- `test_local.py` - Local testing script
- `.env` - Environment variables
- `requirements.txt` - Python dependencies

---

## 🔄 Workflow

1. **Start Flask** - Terminal 1
2. **Start ngrok** - Terminal 2  
3. **Update Pub/Sub** - Point to ngrok URL
4. **Test** - Send messages or invoke agent
5. **Monitor** - Watch logs and ngrok dashboard
6. **Debug** - Add print statements, restart Flask
7. **Verify** - Check Portal26 for traces
8. **Cleanup** - Stop services, restore Pub/Sub

---

## ✅ Benefits

**vs Cloud Run:**
- ✅ No permission issues
- ✅ Instant updates (no redeploy)
- ✅ Real-time logs
- ✅ Easy debugging

**vs Pure Local:**
- ✅ Test with real Pub/Sub
- ✅ Test with real Cloud Trace API
- ✅ Test with real Portal26
- ✅ End-to-end validation

---

## 🚀 Production vs Local

**Production (telemetry_worker/):**
- Deployed to Cloud Run
- Scales automatically
- Production credentials
- Monitored in Cloud Console

**Local Testing (telemetry_worker_ngrok/):**
- Runs on laptop
- Quick iteration
- Same code, different setup
- ngrok for external access

---

## Next Steps

After testing locally:
1. ✅ Verify traces in Portal26
2. ✅ Test with multiple tenants
3. ✅ Test error handling
4. ✅ Once satisfied, use production Cloud Run

**Start testing now:**
```bash
python main.py
```

Then open Terminal 2 and run `ngrok http 8080`!
