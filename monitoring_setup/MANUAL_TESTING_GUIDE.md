# Manual Testing Guide - See Your Logs!

## 🎯 Two New Verbose Scripts

I've created verbose versions that **print everything to the console** so you can see exactly what's happening.

---

## Option 1: Just View Logs (No Portal26 forwarding)

### Script: `monitor_pubsub_verbose.py`

**What it does:**
- Pulls logs from Pub/Sub
- Prints EVERYTHING to console
- Shows you exactly what logs are coming in
- Does NOT send to Portal26 (just for viewing)

**Run manually:**
```bash
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup
python monitor_pubsub_verbose.py
```

**Or double-click:**
```
test_verbose.bat
```

**Output example:**
```
================================================================================
MESSAGE #1
================================================================================
Timestamp:      2026-04-19T05:51:05.073664154Z
Severity:       INFO
Resource Type:  aiplatform.googleapis.com/ReasoningEngine
Engine ID:      6010661182900273152
Trace ID:       0a503a1cda88df237e05ea154005ffef
Span ID:        7a9402879a14ad62
>>> MATCHED: Reasoning Engine Log #1 <<<

JSON Payload:
----------------------------------------
{
  "content": {
    "parts": [
      {
        "text": "Here is the information about your Cloud Storage buckets..."
      }
    ],
    "role": "model"
  },
  "finish_reason": "STOP"
}
```

---

## Option 2: View Logs AND Forward to Portal26

### Script: `monitor_to_portal26_verbose.py`

**What it does:**
- Pulls logs from Pub/Sub
- Prints each log to console
- Shows batch building process
- Forwards to Portal26
- Shows Portal26 response

**Run manually:**
```bash
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup
python monitor_to_portal26_verbose.py
```

**Or double-click:**
```
run_verbose.bat
```

**Output example:**
```
--------------------------------------------------------------------------------
RECEIVED LOG #1
--------------------------------------------------------------------------------
Time:      2026-04-19T05:51:05.073664154Z
Severity:  INFO
Engine:    6010661182900273152
Text:      Here is the information about your Cloud Storage buckets...
JSON keys: ['content', 'finish_reason', 'index']
>>> Added to batch (1/10) <<<

--------------------------------------------------------------------------------
RECEIVED LOG #2
--------------------------------------------------------------------------------
Time:      2026-04-19T05:51:06.123456789Z
Severity:  INFO
Engine:    6010661182900273152
JSON keys: ['content']
>>> Added to batch (2/10) <<<

...

>>> BATCH FULL - Flushing to Portal26 >>>
================================================================================
SENDING BATCH TO PORTAL26 (10 logs)
================================================================================
POST https://otel-tenant1.portal26.in:4318/v1/logs
Payload size: 12345 bytes
Headers: ['Content-Type', 'Authorization']
Response: 200
Body: {"partialSuccess":{}}
[SUCCESS] Sent 10 logs to Portal26
[TOTAL] 10 logs forwarded so far
```

---

## 🧪 Testing Steps

### Step 1: Start Verbose Monitor

**Terminal 1:**
```bash
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup
python monitor_to_portal26_verbose.py
```

Leave this running!

### Step 2: Trigger Reasoning Engine

**In Google Console UI:**
1. Go to your Reasoning Engine: `6010661182900273152`
2. Send a test prompt
3. Wait 1-2 minutes

### Step 3: Watch the Output

In Terminal 1, you should see:
```
RECEIVED LOG #1
...
>>> Added to batch (1/10) <<<
```

When batch fills or timeout happens:
```
SENDING BATCH TO PORTAL26 (10 logs)
...
[SUCCESS] Sent 10 logs to Portal26
```

### Step 4: Verify in Portal26

Open Portal26 dashboard and search:
```
service.name = "gcp-vertex-monitor"
tenant.id = "tenant1"
```

---

## 📊 What You'll See

### When Logs Arrive:
```
RECEIVED LOG #1
--------------------------------------------------------------------------------
Time:      2026-04-19T05:51:05Z
Severity:  INFO
Engine:    6010661182900273152
Text:      Your prompt response...
>>> Added to batch (1/10) <<<
```

### When No Logs:
```
Listening for 60 seconds...
Press Ctrl+C to stop early

(no output = no logs coming in)
```

### When Forwarding:
```
SENDING BATCH TO PORTAL26 (10 logs)
POST https://otel-tenant1.portal26.in:4318/v1/logs
Response: 200
[SUCCESS] Sent 10 logs to Portal26
```

---

## 🔍 Debugging

### If No Logs Appear

**Check 1: Are logs in Cloud Logging?**
```bash
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine"' --limit=5 --project=agentic-ai-integration-490716
```

Should show recent logs.

**Check 2: Is log sink working?**
```bash
gcloud logging sinks describe vertex-ai-telemetry-sink --project=agentic-ai-integration-490716
```

Should show:
```
destination: pubsub.googleapis.com/.../vertex-telemetry-topic
filter: resource.type="aiplatform.googleapis.com/ReasoningEngine"
```

**Check 3: Are messages in Pub/Sub?**
```bash
gcloud pubsub subscriptions pull vertex-telemetry-subscription --limit=5 --project=agentic-ai-integration-490716
```

### If Logs Arrive But Portal26 Fails

**Check error message:**
```
[ERROR] Portal26 returned 401
```

→ Check authentication in .env

```
[ERROR] Portal26 returned 500
```

→ Portal26 service issue

```
[ERROR] Failed to send: Timeout
```

→ Network/firewall issue

---

## ⚙️ Configuration

Both scripts use the same `.env` file:

```bash
# GCP
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription

# Portal26
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_SERVICE_NAME=gcp-vertex-monitor
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==

# Multi-tenant
PORTAL26_TENANT_ID=tenant1
PORTAL26_USER_ID=relusys_terraform

# Batching
PORTAL26_BATCH_SIZE=10        # Logs per batch
PORTAL26_BATCH_TIMEOUT=5      # Seconds before auto-flush
```

---

## 🎬 Quick Start

### Just to see logs (no forwarding):
```bash
# Windows
test_verbose.bat

# Or manually
python monitor_pubsub_verbose.py
```

### To forward to Portal26 (with verbose output):
```bash
# Windows
run_verbose.bat

# Or manually  
python monitor_to_portal26_verbose.py
```

---

## 📝 Summary

| Script | Purpose | Forwards to Portal26? | Output |
|--------|---------|----------------------|--------|
| `monitor_pubsub_verbose.py` | View only | ❌ No | Full log details |
| `monitor_to_portal26_verbose.py` | View + Forward | ✅ Yes | Logs + forwarding status |
| `monitor_pubsub_to_portal26.py` | Production | ✅ Yes | Minimal output |

**For manual testing:** Use the verbose versions!

---

## 🚀 Next Steps

1. **Run verbose forwarder:**
   ```bash
   python monitor_to_portal26_verbose.py
   ```

2. **Trigger a prompt** in Google Console UI

3. **Wait 1-2 minutes** for logs to flow

4. **Watch the output** - you'll see everything!

5. **Check Portal26** - logs should be there

---

**Questions?** Just run the verbose scripts and you'll see exactly what's happening!
