# Pull vs Push Architecture

## Current Implementation: Pull-Based ✅

### How It Works:
```
┌─────────────────┐
│   Forwarder     │ <── Runs continuously
│   (Always On)   │
└────────┬────────┘
         │
         │ Pull request every few seconds
         │ "Give me new messages"
         ▼
┌─────────────────┐
│  Pub/Sub        │
│  Subscription   │
└─────────────────┘
```

**Characteristics:**
- ✅ Forwarder actively pulls from Pub/Sub
- ✅ Runs in continuous loop
- ✅ Processes messages immediately
- ✅ Simple to deploy (single Python script)
- ✅ Works from anywhere (Windows, AWS, etc.)

**Current Code:**
```python
# continuous_forwarder.py
streaming_pull_future = subscriber.subscribe(subscription_path, callback)
while running:
    # Continuously pulling in background
    time.sleep(1)
```

---

## Alternative: Push-Based (Event-Driven)

### How It Works:
```
┌─────────────────┐
│  Pub/Sub        │ <── Message arrives
│  Subscription   │
└────────┬────────┘
         │
         │ HTTP POST automatically
         │ (triggered by message arrival)
         ▼
┌─────────────────┐
│  Cloud Function │
│  or Cloud Run   │ <── Only runs when message arrives
└─────────────────┘
         │
         │ Forwards to Portal26
         ▼
┌─────────────────┐
│  Portal26       │
└─────────────────┘
```

**Characteristics:**
- ✅ Pub/Sub automatically triggers processing
- ✅ No always-on server needed
- ✅ Scales automatically (serverless)
- ✅ Pay only when messages arrive
- ❌ Requires Cloud Function or Cloud Run deployment
- ❌ More complex setup

---

## Comparison

| Feature | Pull-Based (Current) | Push-Based (Event) |
|---------|---------------------|-------------------|
| **Trigger** | Forwarder pulls continuously | Pub/Sub pushes automatically |
| **Always Running** | Yes | No (starts on message) |
| **Deployment** | Single Python script | Cloud Function/Run |
| **Cost** | Fixed (server always on) | Variable (per invocation) |
| **Latency** | Low (~1-2 seconds) | Very low (<1 second) |
| **Complexity** | Simple | Moderate |
| **Scaling** | Manual (add more forwarders) | Automatic (serverless) |
| **Best For** | Consistent workload | Variable/spiky workload |

---

## Push-Based Implementation

### Option 1: Cloud Function (Serverless)

**File:** `cloud_function_forwarder.py`

```python
"""
Cloud Function triggered by Pub/Sub
Automatically invoked when message arrives
"""
import json
import os
import requests
from google.cloud import logging as cloud_logging

# Configuration from environment
PORTAL26_ENDPOINT = os.environ.get("PORTAL26_ENDPOINT")
OTEL_HEADERS = os.environ.get("OTEL_HEADERS")

def pubsub_to_portal26(event, context):
    """
    Triggered by Pub/Sub message
    
    Args:
        event (dict): Pub/Sub message data
        context (google.cloud.functions.Context): Event metadata
    """
    try:
        # Decode Pub/Sub message
        import base64
        message_data = base64.b64decode(event['data']).decode('utf-8')
        log_entry = json.loads(message_data)
        
        # Filter for Reasoning Engine logs
        resource = log_entry.get('resource', {})
        if resource.get('type') != 'aiplatform.googleapis.com/ReasoningEngine':
            print(f"Skipping non-Reasoning Engine log")
            return
        
        # Convert to OTEL format
        otel_log = convert_to_otel(log_entry)
        
        # Send to Portal26
        payload = {
            "resourceLogs": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "gcp-vertex-monitor"}},
                        {"key": "tenant.id", "value": {"stringValue": "tenant1"}}
                    ]
                },
                "scopeLogs": [{
                    "scope": {"name": "cloud-function", "version": "1.0.0"},
                    "logRecords": [otel_log]
                }]
            }]
        }
        
        headers = {"Content-Type": "application/json"}
        if OTEL_HEADERS:
            for header in OTEL_HEADERS.split(','):
                if '=' in header:
                    key, value = header.split('=', 1)
                    headers[key.strip()] = value.strip()
        
        response = requests.post(
            f"{PORTAL26_ENDPOINT}/v1/logs",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201, 202]:
            print(f"Successfully forwarded log to Portal26")
        else:
            print(f"Error: Portal26 returned {response.status_code}")
            
    except Exception as e:
        print(f"Error processing message: {e}")

def convert_to_otel(log_entry):
    """Convert GCP log to OTEL format"""
    # Same as continuous_forwarder.py
    pass
```

**Deployment:**
```bash
# Deploy Cloud Function
gcloud functions deploy pubsub-to-portal26 \
  --runtime python311 \
  --trigger-topic vertex-telemetry-topic \
  --entry-point pubsub_to_portal26 \
  --set-env-vars PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318 \
  --set-env-vars OTEL_HEADERS="Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  --region us-central1 \
  --project agentic-ai-integration-490716
```

**How It Works:**
1. Message arrives in Pub/Sub topic
2. Pub/Sub automatically triggers Cloud Function
3. Function processes ONE message
4. Function forwards to Portal26
5. Function terminates (no cost until next message)

---

### Option 2: Cloud Run (Push Endpoint)

**Create Push Subscription:**
```bash
# Create push subscription (instead of pull)
gcloud pubsub subscriptions create vertex-telemetry-push \
  --topic vertex-telemetry-topic \
  --push-endpoint https://your-cloud-run-service.run.app/webhook \
  --project agentic-ai-integration-490716
```

**Cloud Run Service:**
```python
"""
Cloud Run service that receives push from Pub/Sub
"""
from flask import Flask, request, jsonify
import base64
import json
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive Pub/Sub push"""
    try:
        envelope = request.get_json()
        
        # Decode message
        message_data = base64.b64decode(envelope['message']['data'])
        log_entry = json.loads(message_data)
        
        # Process and forward to Portal26
        forward_to_portal26(log_entry)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

---

## Which Should You Use?

### Use Pull-Based (Current) If:
- ✅ You want simple deployment
- ✅ You have consistent log volume
- ✅ You're running on Windows/AWS/local
- ✅ You want full control
- ✅ You prefer a single Python script

**This is what we have and it works great!**

### Use Push-Based If:
- ✅ You want fully serverless (no always-on server)
- ✅ Log volume is variable/spiky
- ✅ You want automatic scaling
- ✅ You want minimal operational overhead
- ✅ You're comfortable with GCP Cloud Functions

---

## Your Question: "Will it not trigger automatically?"

**Answer depends on mode:**

### Pull-Based (Current):
- ❌ No automatic trigger from Pub/Sub
- ✅ Forwarder runs continuously
- ✅ Forwarder actively asks for messages
- **Analogy:** You checking your mailbox every few seconds

### Push-Based:
- ✅ Yes! Automatic trigger from Pub/Sub
- ✅ Cloud Function/Run only runs when message arrives
- ✅ Pub/Sub sends HTTP request automatically
- **Analogy:** Mailman rings doorbell when mail arrives

---

## Recommendation

**Keep pull-based (current) because:**

1. ✅ **Already working** - We tested it successfully
2. ✅ **Simple** - Single Python script, easy to debug
3. ✅ **Flexible** - Can run anywhere (Windows, AWS, local)
4. ✅ **Predictable cost** - Fixed cost, no surprises
5. ✅ **Low latency** - Processes immediately

**Only switch to push if:**
- You want fully serverless
- Log volume is very spiky (0 logs for hours, then burst)
- You want zero operational overhead

---

## Current System is Correct!

Your current continuous pull-based forwarder:
```
✅ Runs continuously
✅ Actively pulls from Pub/Sub
✅ Processes messages immediately
✅ Low latency (~2-5 seconds)
✅ Simple to deploy and debug
```

This is the **recommended approach** for your use case!

The push-based approach is available if you want to go serverless in the future, but the pull-based approach works perfectly for consistent monitoring.
