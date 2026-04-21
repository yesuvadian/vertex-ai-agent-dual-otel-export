# UI Flow Guide - AWS and GCP Console

## Complete Flow from Console UI Perspective

```
┌─────────────────────────────────────────────────────────────┐
│                    GCP Console Flow                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              AWS Console Flow                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1: GCP Console Flow

### Step 1: Navigate to Vertex AI Agent Engine

**Console Path:**
```
GCP Console → Vertex AI → Agent Builder → Agent Engine
```

**URL:**
```
https://console.cloud.google.com/vertex-ai/agents/agent-engines
```

**What you see:**
- List of deployed reasoning engines
- Engine: `adk-style-monitoring-agent`
- Engine ID: `8336963904483622912`
- Status: Active

---

### Step 2: View Agent Details

**Click on**: `adk-style-monitoring-agent`

**Tabs available:**
1. **Dashboard** - Overview and metrics
2. **Runtime metrics** - Performance stats
3. **Traces** - Execution traces
4. **Sessions** - User sessions
5. **Playground** - Testing interface (shows "not available for Python-deployed agents")
6. **Memories** - User memory data
7. **Evaluation** - Performance evaluation

**What you see in Dashboard:**
- Engine Name: adk-style-monitoring-agent
- Engine ID: 8336963904483622912
- Location: us-central1
- Created: 2026-04-21
- Status: Active

---

### Step 3: Test Agent (Alternative - Use Python API)

Since Playground is not available, use Python locally or Cloud Shell:

```python
import vertexai
from vertexai.preview import reasoning_engines

vertexai.init(
    project="agentic-ai-integration-490716",
    location="us-central1",
    staging_bucket="gs://agentic-ai-integration-490716-reasoning-engine"
)

engine = reasoning_engines.ReasoningEngine(
    "projects/961756870884/locations/us-central1/reasoningEngines/8336963904483622912"
)

# Test query
result = engine.query(
    message="What is the temperature in London?",
    user_id="test-user-001",
    session_id="session-001"
)

print(result)
```

---

### Step 4: View Cloud Logging

**Console Path:**
```
GCP Console → Logging → Logs Explorer
```

**URL:**
```
https://console.cloud.google.com/logs
```

**Filter query:**
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
resource.labels.reasoning_engine_id="8336963904483622912"
```

**What you see:**
- All print statements from agent code
- Query inputs and outputs
- Tool executions
- Analysis results
- Timestamps

**Sample log entry:**
```
[AGENT] Query called: message='What is the temperature in London?...', user=test-user-001, session=session-001
[TOOL] get_temperature called for: London
[TOOL] Temperature result: {'city': 'London', 'temperature_celsius': 15, ...}
```

---

### Step 5: View Log Sink Configuration

**Console Path:**
```
GCP Console → Logging → Log Router
```

**URL:**
```
https://console.cloud.google.com/logs/router
```

**What you see:**

**Sink Name:** `reasoning-engine-to-pubsub`

**Details:**
- Destination: Pub/Sub Topic `reasoning-engine-logs-topic`
- Filter:
  ```
  resource.type="aiplatform.googleapis.com/ReasoningEngine" AND
  resource.labels.reasoning_engine_id="8336963904483622912"
  ```
- Status: Active
- Service Account: `service-961756870884@gcp-sa-logging.iam.gserviceaccount.com`

---

### Step 6: View Pub/Sub Topic

**Console Path:**
```
GCP Console → Pub/Sub → Topics
```

**URL:**
```
https://console.cloud.google.com/cloudpubsub/topic/list
```

**What you see:**

**Topic:** `reasoning-engine-logs-topic`

**Details:**
- Subscriptions: 1 (reasoning-engine-logs-to-aws)
- Messages published: Count
- Retention: 7 days

**Click on topic to see:**
- Message throughput graph
- Subscription details
- Published messages count

---

### Step 7: View Pub/Sub Subscription

**Console Path:**
```
GCP Console → Pub/Sub → Subscriptions
```

**URL:**
```
https://console.cloud.google.com/cloudpubsub/subscription/list
```

**What you see:**

**Subscription:** `reasoning-engine-logs-to-aws`

**Details:**
- Type: Push
- Push endpoint: `https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/`
- Delivery type: PUSH
- Ack deadline: 10 seconds
- Retention: 7 days
- Status: Active

**Metrics visible:**
- Messages published/second
- Oldest unacked message age
- Unacked message count
- Push request latencies

---

## Part 2: AWS Console Flow

### Step 8: Navigate to Lambda Function

**Console Path:**
```
AWS Console → Lambda → Functions
```

**URL:**
```
https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions
```

**What you see:**
- List of Lambda functions
- Function: `gcp-pubsub-test`
- Runtime: Python 3.11
- Last modified: Date

---

### Step 9: View Lambda Function Details

**Click on**: `gcp-pubsub-test`

**Tabs available:**
1. **Code** - Function code editor
2. **Test** - Test event configuration
3. **Monitor** - CloudWatch metrics
4. **Configuration** - Runtime settings
5. **Aliases** - Version aliases
6. **Versions** - Function versions

**What you see in Code tab:**
```python
import json
import base64
from datetime import datetime

def lambda_handler(event, context):
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] === Received event from GCP Pub/Sub ===")
    
    # Process Pub/Sub message
    if 'body' in event:
        body = json.loads(event['body'])
    else:
        body = event
    
    message = body['message']
    encoded_data = message['data']
    decoded_bytes = base64.b64decode(encoded_data)
    message_data = decoded_bytes.decode('utf-8')
    
    print(f"[OK] Message Data: {message_data}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'success',
            'message': 'Message received and processed',
            'messageId': message.get('messageId'),
            'dataPreview': message_data[:100]
        })
    }
```

---

### Step 10: View Function URL Configuration

**In Lambda Console → Configuration tab → Function URL**

**What you see:**
- Function URL: `https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/`
- Auth type: NONE (public access)
- CORS: Not configured
- Creation time: Date
- Status: Active

**URL is used by:** GCP Pub/Sub push subscription

---

### Step 11: View Lambda Metrics (Monitor Tab)

**Console shows:**

**Invocations:**
- Graph showing invocations over time
- Total invocations count
- Success rate

**Duration:**
- Average execution time
- P50, P90, P99 latencies

**Error count:**
- Failed invocations
- Error rate percentage

**Concurrent executions:**
- Number of concurrent function executions

**Throttles:**
- Throttled invocation count

---

### Step 12: View CloudWatch Logs

**From Lambda Console → Monitor tab → View CloudWatch logs**

**Or direct path:**
```
AWS Console → CloudWatch → Log groups
```

**URL:**
```
https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups
```

**Log group:** `/aws/lambda/gcp-pubsub-test`

**What you see:**

**Log streams** (one per Lambda execution):
```
2026/04/21/[$LATEST]abc123def456
```

**Log entries:**
```
START RequestId: abc-123-def-456 Version: $LATEST

[2026-04-21T18:05:23.123Z] === Received event from GCP Pub/Sub ===

[OK] Message Data: [AGENT] Query called: message='What is the temperature in London?...', user=test-user-001, session=session-001

[OK] Message Data: [TOOL] get_temperature called for: London

[OK] Message Data: [TOOL] Temperature result: {'city': 'London', 'temperature_celsius': 15, ...}

END RequestId: abc-123-def-456
REPORT RequestId: abc-123-def-456
Duration: 45.67 ms
Billed Duration: 46 ms
Memory Size: 128 MB
Max Memory Used: 35 MB
```

---

### Step 13: CloudWatch Logs Insights (Advanced)

**Console Path:**
```
CloudWatch → Logs → Insights
```

**Select log group:** `/aws/lambda/gcp-pubsub-test`

**Sample queries:**

**Query 1: Count messages per user**
```
fields @timestamp, @message
| filter @message like /user_id/
| parse @message "user_id='*'" as user
| stats count() by user
```

**Query 2: Find all ERROR messages**
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
```

**Query 3: Get tool execution counts**
```
fields @timestamp, @message
| filter @message like /TOOL/
| parse @message "[TOOL] * called" as tool_name
| stats count() by tool_name
```

---

## Complete End-to-End Flow (UI Perspective)

### User Journey

**1. Developer deploys agent (Local)**
```bash
python create_simple_adk_agent.py
```

**2. View in GCP Console**
```
Vertex AI → Agent Engine → adk-style-monitoring-agent
Status: Active ✓
```

**3. Test agent (Local)**
```bash
python test_local.py
```

**4. See logs in GCP (1-2 seconds)**
```
Logging → Logs Explorer
Filter: reasoning_engine_id="8336963904483622912"
Result: Agent logs visible
```

**5. Logs forwarded to Pub/Sub (automatic)**
```
Pub/Sub → Topics → reasoning-engine-logs-topic
Status: Messages publishing ✓
```

**6. Push to AWS Lambda (1-2 minutes)**
```
Pub/Sub → Subscriptions → reasoning-engine-logs-to-aws
Push to: Lambda URL
Status: Delivering ✓
```

**7. View in AWS Lambda Logs**
```
Lambda → Monitor → View CloudWatch logs
Result: GCP logs appearing in AWS ✓
```

---

## Visual Flow Chart

```
┌──────────────────────────────────────────────────────────────────┐
│  GCP Console: Vertex AI → Agent Engine                           │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  adk-style-monitoring-agent (ACTIVE)                   │     │
│  │  Engine ID: 8336963904483622912                        │     │
│  │  [Dashboard] [Traces] [Sessions]                       │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ Automatic logging
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│  GCP Console: Logging → Logs Explorer                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Filter: reasoning_engine_id="8336963904483622912"     │     │
│  │  [Agent logs] [Tool calls] [Results]                   │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ Log Sink
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│  GCP Console: Pub/Sub → Topics                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  reasoning-engine-logs-topic                           │     │
│  │  Messages: [Graph] Subscriptions: 1                    │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ Push subscription
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│  GCP Console: Pub/Sub → Subscriptions                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  reasoning-engine-logs-to-aws (PUSH)                   │     │
│  │  Endpoint: Lambda URL                                  │     │
│  │  Status: Active, Ack: 10s                              │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ HTTPS Push
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│  AWS Console: Lambda → Functions                                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  gcp-pubsub-test (Python 3.11)                         │     │
│  │  [Code] [Monitor] [Configuration]                      │     │
│  │  Function URL: Active                                  │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ Logs to CloudWatch
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│  AWS Console: CloudWatch → Log groups                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  /aws/lambda/gcp-pubsub-test                           │     │
│  │  [Log streams] [Messages] [Metrics]                    │     │
│  │  [2026-04-21T18:05:23] Received from GCP Pub/Sub       │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Summary of Console URLs

### GCP Console

1. **Agent Engine**
   ```
   https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/8336963904483622912
   ```

2. **Cloud Logging**
   ```
   https://console.cloud.google.com/logs/query
   ```

3. **Log Router (Sinks)**
   ```
   https://console.cloud.google.com/logs/router
   ```

4. **Pub/Sub Topics**
   ```
   https://console.cloud.google.com/cloudpubsub/topic/detail/reasoning-engine-logs-topic
   ```

5. **Pub/Sub Subscriptions**
   ```
   https://console.cloud.google.com/cloudpubsub/subscription/detail/reasoning-engine-logs-to-aws
   ```

### AWS Console

1. **Lambda Function**
   ```
   https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/gcp-pubsub-test
   ```

2. **Lambda Monitoring**
   ```
   https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/gcp-pubsub-test?tab=monitoring
   ```

3. **CloudWatch Logs**
   ```
   https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252Fgcp-pubsub-test
   ```

4. **CloudWatch Insights**
   ```
   https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights
   ```

---

## Key Takeaways

1. **No Playground UI** for Python-deployed Reasoning Engines - use Python API for testing
2. **Cloud Logging** shows real-time agent execution logs (1-2 second delay)
3. **Pub/Sub** provides reliable message delivery with metrics
4. **Lambda** receives and processes logs automatically
5. **CloudWatch** stores all logs for analysis and monitoring

**Everything is visible in the console - full observability!**
