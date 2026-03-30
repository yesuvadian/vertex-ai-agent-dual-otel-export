# Testing Your AI Agent in Google Cloud Console

## 🎯 Method 1: Cloud Shell (Recommended - Built-in Terminal)

### Step 1: Open Cloud Shell

1. Go to your Cloud Run service:
   👉 https://console.cloud.google.com/run/detail/us-central1/ai-agent?project=agentic-ai-integration-490716

2. Click the **Cloud Shell** icon (>_) in the top-right corner of the console

3. Wait for Cloud Shell to activate (takes 10-15 seconds)

### Step 2: Test Status Endpoint

In Cloud Shell, run:

```bash
# Get authentication token
TOKEN=$(gcloud auth print-identity-token)

# Test status endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://ai-agent-961756870884.us-central1.run.app/status
```

**Expected Output:**
```json
{"agent_mode":"manual","manual_agent_enabled":true,"adk_agent_enabled":false}
```

### Step 3: Test Chat Endpoint

```bash
# Test weather query
curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Tokyo?"}'
```

**Expected Output:**
```json
{"final_answer":"The weather in Tokyo is 28°C and sunny."}
```

### Step 4: Test Order Status

```bash
curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order XYZ123?"}'
```

**Expected Output:**
```json
{"final_answer":"Order XYZ123 is shipped."}
```

---

## 🎯 Method 2: API Explorer (No Code Required)

### Step 1: Enable Public Access (Temporary)

First, make your service publicly accessible for testing:

1. Go to Cloud Run service page:
   👉 https://console.cloud.google.com/run/detail/us-central1/ai-agent?project=agentic-ai-integration-490716

2. Click **"PERMISSIONS"** tab

3. Click **"+ GRANT ACCESS"**

4. In the "New principals" field, enter: `allUsers`

5. In the "Role" dropdown, select: **"Cloud Run Invoker"**

6. Click **"SAVE"**

### Step 2: Test Without Authentication

Now you can use simple curl commands or your browser:

**In Cloud Shell:**
```bash
# No token needed now!
curl https://ai-agent-961756870884.us-central1.run.app/status
```

**In Browser:**
Just visit: https://ai-agent-961756870884.us-central1.run.app/status

### Step 3: Test Chat Endpoint

**Using Cloud Shell:**
```bash
curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Paris?"}'
```

**Using Browser + Extension:**
- Install "Talend API Tester" or "Postman" Chrome extension
- URL: `https://ai-agent-961756870884.us-central1.run.app/chat`
- Method: `POST`
- Headers: `Content-Type: application/json`
- Body: `{"message": "What is the weather in Paris?"}`

### Step 4: Re-enable Authentication (After Testing)

1. Go back to **PERMISSIONS** tab
2. Find the `allUsers` principal
3. Click the trash icon to remove it
4. Click **"SAVE"**

---

## 🎯 Method 3: Cloud Run Logs (View Real Requests)

### Step 1: Open Logs

1. Go to your service:
   👉 https://console.cloud.google.com/run/detail/us-central1/ai-agent?project=agentic-ai-integration-490716

2. Click the **"LOGS"** tab

### Step 2: Make a Request

Open Cloud Shell and run:
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from console!"}'
```

### Step 3: Watch Logs Appear

You'll see:
- ✅ HTTP request received
- ✅ Agent initialization
- ✅ LLM calls
- ✅ Tool execution
- ✅ Response sent
- ✅ Telemetry exported to Portal26

**Look for these log entries:**
```
[agent_manual] Initialized Gemini API with API key - Model: models/gemini-2.5-flash
[router] Manual agent executed successfully
INFO: 127.0.0.1:xxxxx - "POST /chat HTTP/1.1" 200 OK
```

---

## 🎯 Method 4: Cloud Console Terminal (Testing UI)

### Option A: Cloud Run Testing UI (If Available)

1. Go to service page:
   👉 https://console.cloud.google.com/run/detail/us-central1/ai-agent?project=agentic-ai-integration-490716

2. Look for **"TESTING"** or **"TEST YOUR SERVICE"** tab (may vary by region/UI version)

3. If available, you can send test requests directly from the UI

### Option B: API Gateway (Advanced)

If you want a web UI for testing, you can set up API Gateway:

1. Go to API Gateway:
   👉 https://console.cloud.google.com/api-gateway?project=agentic-ai-integration-490716

2. Create a new gateway pointing to your Cloud Run service

3. Enable API testing in the console

---

## 🎯 Method 5: Using Postman/Insomnia (External Tools)

### Step 1: Get Auth Token

In Cloud Shell:
```bash
gcloud auth print-identity-token
```

Copy the token (it's a long JWT string starting with `eyJ...`)

### Step 2: Configure Postman

1. Open Postman (or download from postman.com)

2. Create new request:
   - **Method**: `POST`
   - **URL**: `https://ai-agent-961756870884.us-central1.run.app/chat`

3. Add Headers:
   - Key: `Authorization`
   - Value: `Bearer YOUR_TOKEN_HERE`
   - Key: `Content-Type`
   - Value: `application/json`

4. Add Body (raw JSON):
```json
{
  "message": "What is the weather in London?"
}
```

5. Click **"Send"**

---

## 🎯 Method 6: Monitoring Dashboard

### View Request Metrics

1. Go to Cloud Run service:
   👉 https://console.cloud.google.com/run/detail/us-central1/ai-agent?project=agentic-ai-integration-490716

2. Click **"METRICS"** tab

You'll see:
- 📊 Request count (per minute)
- 📊 Request latency (50th, 95th, 99th percentile)
- 📊 Container instance count
- 📊 CPU utilization
- 📊 Memory utilization
- 📊 Error rate

### Step 2: Make Some Requests

```bash
# In Cloud Shell, send multiple requests
TOKEN=$(gcloud auth print-identity-token)

for i in {1..10}; do
  echo "Request $i:"
  curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test request $i\"}" \
    -w "\nStatus: %{http_code}\n\n"
done
```

### Step 3: Watch Metrics Update

Refresh the Metrics tab to see:
- Request count increase
- Latency graphs
- Instance scaling (if traffic is high)

---

## 🎯 Method 7: Cloud Trace (Detailed Performance)

### View Request Traces

1. Go to Cloud Trace:
   👉 https://console.cloud.google.com/traces/list?project=agentic-ai-integration-490716

2. Filter by:
   - Service: `ai-agent`
   - Time range: Last 1 hour

3. Click on any trace to see:
   - Total request time
   - Breakdown by component
   - Database/API calls
   - HTTP requests

### Compare with Portal26

Your traces are also in Portal26 with more detailed spans:
- `agent_run`
- `llm_call`
- `tool:get_weather`
- `llm_final`

---

## 📝 Quick Testing Checklist

### Pre-Test Setup
- [ ] Open Cloud Console: https://console.cloud.google.com
- [ ] Navigate to Cloud Run service
- [ ] Open Cloud Shell (top-right icon)

### Test Endpoints
```bash
# Get auth token
TOKEN=$(gcloud auth print-identity-token)

# Test 1: Health check
curl https://ai-agent-961756870884.us-central1.run.app/ \
  -H "Authorization: Bearer $TOKEN"

# Test 2: Status check
curl https://ai-agent-961756870884.us-central1.run.app/status \
  -H "Authorization: Bearer $TOKEN"

# Test 3: Weather query
curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Tokyo?"}'

# Test 4: Order status query
curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order ABC123?"}'
```

### Verify Results
- [ ] All responses return 200 status
- [ ] Weather query returns mock weather data
- [ ] Order status query returns shipping status
- [ ] Logs show successful execution
- [ ] Metrics show request count increase
- [ ] Portal26 shows new traces (if checking)

---

## 🔍 Troubleshooting

### Error: "Failed to get auth token"

**Solution:**
```bash
gcloud auth login
gcloud config set project agentic-ai-integration-490716
```

### Error: "Permission denied"

**Solution:**
```bash
# Ensure you're authenticated
gcloud auth application-default login

# Or make service public (temporary)
# See Method 2 above
```

### Error: "Connection timeout"

**Cause:** Service might be cold starting (first request after idle)

**Solution:** Wait 3-5 seconds and retry

### Error: "500 Internal Server Error"

**Solution:**
```bash
# Check logs
gcloud run services logs read ai-agent --region us-central1 --limit 50
```

Common causes:
- API key not set correctly
- Generative Language API not enabled
- Memory limit exceeded

---

## 🎬 Video Tutorial (Step-by-Step)

### 1. Access Cloud Shell
[![Cloud Shell](https://img.shields.io/badge/Open-Cloud%20Shell-4285F4?logo=google-cloud)](https://console.cloud.google.com/?cloudshell=true&project=agentic-ai-integration-490716)

### 2. Click the Terminal Icon
Look for `>_` in the top-right corner

### 3. Copy & Paste Test Commands
```bash
# All-in-one test script
TOKEN=$(gcloud auth print-identity-token)

echo "Testing AI Agent..."
echo ""
echo "1. Status Check:"
curl -s https://ai-agent-961756870884.us-central1.run.app/status \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo ""
echo "2. Weather Query:"
curl -s -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Paris?"}' | python -m json.tool

echo ""
echo "3. Order Status Query:"
curl -s -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order XYZ789?"}' | python -m json.tool

echo ""
echo "✅ All tests complete!"
```

---

## 📊 Expected Results

### Successful Test Output

```json
Testing AI Agent...

1. Status Check:
{
    "agent_mode": "manual",
    "manual_agent_enabled": true,
    "adk_agent_enabled": false
}

2. Weather Query:
{
    "final_answer": "The weather in Paris is 28°C and sunny."
}

3. Order Status Query:
{
    "final_answer": "Order XYZ789 is shipped."
}

✅ All tests complete!
```

---

## 🎓 Next Steps

After testing in the console:

1. **Check Logs**: View detailed execution logs
2. **View Metrics**: See request patterns and latency
3. **Check Portal26**: Verify telemetry is working
4. **Load Test**: Send many requests to test auto-scaling
5. **Integrate**: Connect from your application

---

## 📞 Quick Links

- **Service Console**: https://console.cloud.google.com/run/detail/us-central1/ai-agent?project=agentic-ai-integration-490716
- **Logs**: https://console.cloud.google.com/logs?project=agentic-ai-integration-490716
- **Metrics**: https://console.cloud.google.com/monitoring?project=agentic-ai-integration-490716
- **Traces**: https://console.cloud.google.com/traces?project=agentic-ai-integration-490716
- **Cloud Shell**: https://console.cloud.google.com/?cloudshell=true&project=agentic-ai-integration-490716

---

**Ready to test? Open Cloud Shell and start testing!** 🚀
