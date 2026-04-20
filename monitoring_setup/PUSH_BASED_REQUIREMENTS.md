# Push-Based (Event-Driven) Implementation Requirements

## What is Push-Based?

Instead of a continuously running forwarder that pulls messages, **Pub/Sub automatically triggers a function** when messages arrive.

```
Message arrives → Pub/Sub automatically calls your function → Process → Done
```

**No always-on server needed!**

---

## Requirements for Push-Based

### 1. Choose a Serverless Platform

You need ONE of these:

#### Option A: Google Cloud Function (Recommended)
```yaml
What it is: Serverless function that runs code in response to events
Trigger: Pub/Sub message arrival
Pricing: Pay per invocation ($0.40 per million invocations)
Deployment: Managed by Google
Scaling: Automatic
```

#### Option B: Google Cloud Run
```yaml
What it is: Containerized HTTP endpoint
Trigger: Pub/Sub sends HTTP POST to your endpoint
Pricing: Pay per request + container runtime
Deployment: Container-based
Scaling: Automatic (0 to N)
```

#### Option C: AWS Lambda (If deployed on AWS)
```yaml
What it is: AWS serverless function
Trigger: EventBridge or custom bridge from GCP
Pricing: Pay per invocation
Deployment: Requires cross-cloud setup
Complexity: Higher (need bridge between GCP and AWS)
```

---

## Option A: Cloud Function (Easiest)

### What You Need:

#### 1. Cloud Function Code

**File:** `cloud_function/main.py`

```python
"""
Cloud Function triggered by Pub/Sub
Automatically invoked when message arrives in vertex-telemetry-topic
"""
import json
import os
import base64
import requests
from datetime import datetime, timezone

# Configuration (from environment variables)
PORTAL26_ENDPOINT = os.environ.get("PORTAL26_ENDPOINT")
PORTAL26_AUTH = os.environ.get("PORTAL26_AUTH")
TENANT_ID = os.environ.get("TENANT_ID", "tenant1")
USER_ID = os.environ.get("USER_ID", "relusys_terraform")

def pubsub_to_portal26(event, context):
    """
    Cloud Function entry point
    Triggered by Pub/Sub message
    
    Args:
        event (dict): Pub/Sub event data
        context (google.cloud.functions.Context): Event metadata
    """
    try:
        # Decode Pub/Sub message
        if 'data' in event:
            message_data = base64.b64decode(event['data']).decode('utf-8')
        else:
            print("No data in event")
            return
        
        # Parse GCP log entry
        log_entry = json.loads(message_data)
        
        # Filter for Reasoning Engine logs only
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', '')
        
        if resource_type != 'aiplatform.googleapis.com/ReasoningEngine':
            print(f"Skipping non-Reasoning Engine log: {resource_type}")
            return
        
        # Convert to OTEL format
        otel_log = convert_to_otel(log_entry)
        
        # Send to Portal26
        send_to_portal26([otel_log])
        
        print(f"Successfully forwarded log to Portal26")
        
    except Exception as e:
        print(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()

def convert_to_otel(log_entry):
    """Convert GCP log entry to OTEL log format"""
    timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)
    
    severity = log_entry.get('severity', 'INFO')
    text_payload = log_entry.get('textPayload', '')
    json_payload = log_entry.get('jsonPayload', {})
    resource = log_entry.get('resource', {})
    labels = log_entry.get('labels', {})
    
    # Severity mapping
    severity_map = {
        "DEBUG": 5, "INFO": 9, "NOTICE": 10, "WARNING": 13,
        "ERROR": 17, "CRITICAL": 21, "ALERT": 22, "EMERGENCY": 23
    }
    
    otel_log = {
        "timeUnixNano": str(timestamp_ns),
        "severityText": severity,
        "severityNumber": severity_map.get(severity, 9),
        "body": {
            "stringValue": text_payload if text_payload else json.dumps(json_payload)
        },
        "attributes": []
    }
    
    # Add resource attributes
    resource_labels = resource.get('labels', {})
    for key, value in resource_labels.items():
        otel_log["attributes"].append({
            "key": f"resource.{key}",
            "value": {"stringValue": str(value)}
        })
    
    # Add labels
    for key, value in labels.items():
        otel_log["attributes"].append({
            "key": key,
            "value": {"stringValue": str(value)}
        })
    
    # Add trace/span
    if 'trace' in log_entry:
        trace_id = log_entry['trace'].split('/')[-1] if '/' in log_entry['trace'] else log_entry['trace']
        otel_log["traceId"] = trace_id
    if 'spanId' in log_entry:
        otel_log["spanId"] = log_entry['spanId']
    
    return otel_log

def send_to_portal26(logs):
    """Send logs to Portal26"""
    payload = {
        "resourceLogs": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "gcp-vertex-monitor"}},
                    {"key": "source", "value": {"stringValue": "cloud-function"}},
                    {"key": "tenant.id", "value": {"stringValue": TENANT_ID}},
                    {"key": "user.id", "value": {"stringValue": USER_ID}}
                ]
            },
            "scopeLogs": [{
                "scope": {
                    "name": "cloud-function-forwarder",
                    "version": "1.0.0"
                },
                "logRecords": logs
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": PORTAL26_AUTH
    }
    
    response = requests.post(
        f"{PORTAL26_ENDPOINT}/v1/logs",
        json=payload,
        headers=headers,
        timeout=10
    )
    
    if response.status_code not in [200, 201, 202]:
        raise Exception(f"Portal26 returned {response.status_code}: {response.text}")
```

#### 2. Requirements File

**File:** `cloud_function/requirements.txt`

```txt
requests==2.31.0
```

#### 3. Deploy Command

```bash
# Deploy Cloud Function
gcloud functions deploy vertex-to-portal26 \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --source cloud_function \
  --entry-point pubsub_to_portal26 \
  --trigger-topic vertex-telemetry-topic \
  --set-env-vars PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318 \
  --set-env-vars PORTAL26_AUTH="Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  --set-env-vars TENANT_ID=tenant1 \
  --set-env-vars USER_ID=relusys_terraform \
  --max-instances 10 \
  --timeout 60s \
  --memory 256MB \
  --project agentic-ai-integration-490716
```

#### 4. What Happens After Deployment

```
1. Message arrives in vertex-telemetry-topic
2. Pub/Sub automatically invokes Cloud Function
3. Function receives message as parameter
4. Function processes and forwards to Portal26
5. Function terminates (no cost until next message)
```

**That's it!** No server to manage, automatic scaling.

---

## Option B: Cloud Run (HTTP Endpoint)

### What You Need:

#### 1. Cloud Run Service Code

**File:** `cloud_run/app.py`

```python
"""
Cloud Run service that receives Pub/Sub push messages
"""
from flask import Flask, request, jsonify
import json
import base64
import requests
import os

app = Flask(__name__)

PORTAL26_ENDPOINT = os.environ.get("PORTAL26_ENDPOINT")
PORTAL26_AUTH = os.environ.get("PORTAL26_AUTH")

@app.route('/', methods=['POST'])
def index():
    """Health check endpoint"""
    return 'Cloud Run service is running', 200

@app.route('/pubsub-webhook', methods=['POST'])
def pubsub_webhook():
    """Receive Pub/Sub push notification"""
    try:
        envelope = request.get_json()
        
        if not envelope:
            return 'No Pub/Sub message received', 400
        
        # Decode Pub/Sub message
        message_data = base64.b64decode(envelope['message']['data'])
        log_entry = json.loads(message_data)
        
        # Process and forward to Portal26
        result = process_log(log_entry)
        
        if result:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failed"}), 500
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def process_log(log_entry):
    """Process log and send to Portal26"""
    # Filter for Reasoning Engine
    resource = log_entry.get('resource', {})
    if resource.get('type') != 'aiplatform.googleapis.com/ReasoningEngine':
        return True  # Skip but return success
    
    # Convert and send to Portal26
    # (same logic as Cloud Function)
    return True

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

#### 2. Dockerfile

**File:** `cloud_run/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

#### 3. Requirements

**File:** `cloud_run/requirements.txt`

```txt
Flask==3.0.0
gunicorn==21.2.0
requests==2.31.0
```

#### 4. Deploy Cloud Run

```bash
# Build and deploy
cd cloud_run

gcloud run deploy vertex-forwarder \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318 \
  --set-env-vars PORTAL26_AUTH="Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  --project agentic-ai-integration-490716
```

#### 5. Create Push Subscription

```bash
# Get Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe vertex-forwarder \
  --region us-central1 \
  --format='value(status.url)')

# Create push subscription
gcloud pubsub subscriptions create vertex-telemetry-push \
  --topic vertex-telemetry-topic \
  --push-endpoint="${CLOUD_RUN_URL}/pubsub-webhook" \
  --project agentic-ai-integration-490716
```

---

## Comparison: What Do You Need?

| Requirement | Cloud Function | Cloud Run | Pull-Based (Current) |
|-------------|---------------|-----------|---------------------|
| **Code** | Python function | Flask app + Dockerfile | Python script |
| **Deployment** | gcloud command | gcloud + container | Copy script |
| **Infrastructure** | None | None | Server/PC |
| **Always Running** | No | No | Yes |
| **Trigger** | Automatic (Pub/Sub) | Automatic (HTTP) | Continuous pull |
| **Scaling** | Automatic | Automatic | Manual |
| **Cost** | Per invocation | Per request + runtime | Fixed |
| **Complexity** | Low | Medium | Very Low |
| **Setup Time** | 10 minutes | 20 minutes | 2 minutes |

---

## Step-by-Step: Cloud Function Setup

### Step 1: Create Directory

```bash
mkdir -p cloud_function
cd cloud_function
```

### Step 2: Create Files

Save the code above as:
- `main.py` - Cloud Function code
- `requirements.txt` - Dependencies

### Step 3: Deploy

```bash
gcloud functions deploy vertex-to-portal26 \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --source . \
  --entry-point pubsub_to_portal26 \
  --trigger-topic vertex-telemetry-topic \
  --set-env-vars PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318,PORTAL26_AUTH="Basic dGl0YW5pYW06aGVsbG93b3JsZA==",TENANT_ID=tenant1,USER_ID=relusys_terraform \
  --max-instances 10 \
  --timeout 60s \
  --memory 256MB \
  --project agentic-ai-integration-490716
```

### Step 4: Verify

```bash
# Check function exists
gcloud functions describe vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --project agentic-ai-integration-490716

# View logs
gcloud functions logs read vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --project agentic-ai-integration-490716
```

### Step 5: Test

Trigger your Reasoning Engine, then check:

```bash
# Check function invocations
gcloud functions logs read vertex-to-portal26 \
  --region us-central1 \
  --gen2 \
  --limit 10

# Check Portal26 dashboard
# Query: service.name = "gcp-vertex-monitor"
```

---

## Cost Comparison

### Pull-Based (Current)
```
AWS EC2 t3.micro: $10/month (always running)
GCP Pub/Sub: $5/month
Total: ~$15/month fixed
```

### Push-Based (Cloud Function)
```
Cloud Function invocations: $0.40 per million
Assuming 10,000 logs/day = 300,000/month = $0.12
GCP Pub/Sub: $5/month
Total: ~$5-6/month variable
```

**Push-based is cheaper if:**
- Low to moderate log volume (<1M logs/month)
- Variable workload (not continuous)

**Pull-based is better if:**
- High log volume (always running anyway)
- Consistent workload
- You prefer simpler deployment

---

## Pros and Cons

### Push-Based (Cloud Function)

**Pros:**
- ✅ Fully serverless (no server management)
- ✅ Automatic scaling (0 to thousands)
- ✅ Pay only for what you use
- ✅ No always-on server needed
- ✅ Managed by Google
- ✅ Lower cost for variable workload

**Cons:**
- ❌ Cold start latency (~1-5 seconds first invocation)
- ❌ More complex debugging
- ❌ Limited to 60 seconds per invocation (gen2)
- ❌ Need to understand Cloud Functions
- ❌ Slightly higher latency per message

### Pull-Based (Current)

**Pros:**
- ✅ Very simple (single Python script)
- ✅ Easy to debug (see all logs)
- ✅ No cold starts
- ✅ Lower latency
- ✅ Batch processing efficient
- ✅ Already working!

**Cons:**
- ❌ Requires always-on server/PC
- ❌ Fixed cost (even if no logs)
- ❌ Manual scaling (add more instances)
- ❌ Need to manage deployment

---

## My Recommendation

### Keep Pull-Based (Current) If:
- ✅ You have consistent log volume
- ✅ You want simple deployment
- ✅ You're already running on EC2/local
- ✅ You want easy debugging
- ✅ **Your current setup is working!**

### Switch to Push-Based If:
- ✅ You want zero operational overhead
- ✅ Log volume is very variable (spiky)
- ✅ You want automatic scaling
- ✅ Cost is a concern
- ✅ You're comfortable with serverless

---

## Quick Answer to "What's Required?"

**Minimum requirements for push-based:**

1. **Code** - Cloud Function (main.py + requirements.txt)
2. **Deployment** - One gcloud command
3. **Configuration** - Environment variables (Portal26 endpoint, auth)
4. **GCP Services** - Cloud Functions (enable API)

**That's it!** 

The Cloud Function automatically:
- Receives messages from Pub/Sub
- Processes them
- Forwards to Portal26
- Scales automatically
- Only costs money when invoked

---

## Want Me to Create the Files?

I can create:
- ✅ Complete Cloud Function code
- ✅ Deployment script
- ✅ Testing guide
- ✅ Monitoring setup

Just let me know if you want to try push-based! Otherwise, your current pull-based setup is excellent and working perfectly. 🚀
