# UI Flow - GCP and AWS Console

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                         GCP Environment                                 │
│  Project: agentic-ai-integration-490716                                │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Vertex AI Reasoning Engine                                       │ │
│  │                                                                    │ │
│  │  Name: adk-style-monitoring-agent                                 │ │
│  │  ID: 8213677864684355584                                          │ │
│  │  Location: us-central1                                            │ │
│  │                                                                    │ │
│  │  Features:                                                         │ │
│  │  • Session management                                              │ │
│  │  • User memory (error tracking)                                    │ │
│  │  • Tools:                                                          │ │
│  │    - get_temperature(city)                                         │ │
│  │    - get_location_info(city)                                       │ │
│  │    - get_capital(country)                                          │ │
│  │                                                                    │ │
│  │  Query Interface:                                                  │ │
│  │  engine.query(message, user_id, session_id)                       │ │
│  └────────────────────────┬───────────────────────────────────────────┘ │
│                           │                                              │
│                           │ Automatic OTEL Logging                       │
│                           │ (1-2 seconds)                                │
│                           ↓                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Cloud Logging                                                    │ │
│  │                                                                    │ │
│  │  Log Type: aiplatform.googleapis.com/ReasoningEngine              │ │
│  │  Captures:                                                         │ │
│  │  • [AGENT] Query calls                                             │ │
│  │  • [TOOL] Tool executions                                          │ │
│  │  • [AGENT] Analysis results                                        │ │
│  │  • Session and memory operations                                   │ │
│  │                                                                    │ │
│  │  Retention: 30 days (default)                                      │ │
│  └────────────────────────┬───────────────────────────────────────────┘ │
│                           │                                              │
│                           │ Log Sink Filter                              │
│                           │ reasoning-engine-to-pubsub                   │
│                           ↓                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Pub/Sub Topic                                                    │ │
│  │                                                                    │ │
│  │  Topic: reasoning-engine-logs-topic                               │ │
│  │  Message Format: Base64 encoded JSON                              │ │
│  │  Retention: 7 days                                                 │ │
│  │                                                                    │ │
│  │  Filter Criteria:                                                  │ │
│  │  resource.labels.reasoning_engine_id="8213677864684355584"        │ │
│  └────────────────────────┬───────────────────────────────────────────┘ │
│                           │                                              │
│                           │ Push Subscription                            │
│                           │ reasoning-engine-logs-to-aws                 │
│                           │ (Ack deadline: 10s)                          │
│                           ↓                                              │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            │ HTTPS Push
                            │ (1-2 minutes)
                            │
┌───────────────────────────┼──────────────────────────────────────────────┐
│                           ↓                  AWS Environment             │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Lambda Function                                                  │ │
│  │                                                                    │ │
│  │  Name: gcp-pubsub-test                                            │ │
│  │  Runtime: Python 3.11                                             │ │
│  │  Memory: 128 MB                                                    │ │
│  │  Timeout: 2 minutes                                                │ │
│  │  Region: us-east-1                                                 │ │
│  │                                                                    │ │
│  │  Function URL (Public):                                            │ │
│  │  https://klxwmowvbumembf63ikfl5q3de0iiygk                         │ │
│  │        .lambda-url.us-east-1.on.aws/                              │ │
│  │                                                                    │ │
│  │  Processing:                                                       │ │
│  │  1. Receive Pub/Sub push message                                   │ │
│  │  2. Decode base64 message data                                     │ │
│  │  3. Log to CloudWatch                                              │ │
│  │  4. Return 200 OK (ack to Pub/Sub)                                 │ │
│  │                                                                    │ │
│  │  Next Step: Forward to Portal26 OTEL endpoint                     │ │
│  └────────────────────────┬───────────────────────────────────────────┘ │
│                           │                                              │
│                           │ Automatic Logging                            │
│                           ↓                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  CloudWatch Logs                                                  │ │
│  │                                                                    │ │
│  │  Log Group: /aws/lambda/gcp-pubsub-test                           │ │
│  │  Retention: Configurable (default: never expire)                  │ │
│  │                                                                    │ │
│  │  Log Contents:                                                     │ │
│  │  • Lambda execution START/END                                      │ │
│  │  • Decoded GCP agent logs                                          │ │
│  │  • Tool execution results                                          │ │
│  │  • Performance metrics (duration, memory)                          │ │
│  │                                                                    │ │
│  │  Analysis Tools:                                                   │ │
│  │  • CloudWatch Insights (SQL-like queries)                          │ │
│  │  • Metric filters                                                  │ │
│  │  • Alarms and dashboards                                           │ │
│  └────────────────────────┬───────────────────────────────────────────┘ │
│                           │                                              │
│                           │ Future: Forward to Portal26                  │
│                           ↓                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Portal26 OTEL Endpoint (Next Step)                              │ │
│  │                                                                    │ │
│  │  • OTLP format conversion                                          │ │
│  │  • Multi-tenant support                                            │ │
│  │  • Trace/log correlation                                           │ │
│  │  • Dashboard and alerting                                          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Details

### Message Format Through Pipeline

**1. Reasoning Engine Log (Cloud Logging)**
```json
{
  "timestamp": "2026-04-21T18:05:23.123456Z",
  "severity": "INFO",
  "resource": {
    "type": "aiplatform.googleapis.com/ReasoningEngine",
    "labels": {
      "reasoning_engine_id": "8213677864684355584",
      "project_id": "agentic-ai-integration-490716",
      "location": "us-central1"
    }
  },
  "textPayload": "[AGENT] Query called: message='What is temperature in London?', user=user-001"
}
```

**2. Pub/Sub Message**
```json
{
  "message": {
    "data": "W0FHRU5UXSBRdWVyeSBjYWxsZWQ6IG1lc3NhZ2U9J1doYXQgaXMgdGVtcGVyYXR1cmUgaW4gTG9uZG9uPycsIHVzZXI9dXNlci0wMDE=",
    "messageId": "12345678901234567890",
    "publishTime": "2026-04-21T18:05:24.567890Z"
  },
  "subscription": "projects/agentic-ai-integration-490716/subscriptions/reasoning-engine-logs-to-aws"
}
```

**3. Lambda Receives (decoded)**
```
[AGENT] Query called: message='What is temperature in London?', user=user-001
[TOOL] get_temperature called for: London
[TOOL] Temperature result: {'city': 'London', 'temperature_celsius': 15, 'temperature_fahrenheit': 59, 'condition': 'Cloudy'}
```

**4. CloudWatch Log Entry**
```
2026-04-21T18:05:25.123Z  START RequestId: abc-123-def-456 Version: $LATEST
2026-04-21T18:05:25.234Z  [2026-04-21T18:05:25.234Z] === Received event from GCP Pub/Sub ===
2026-04-21T18:05:25.345Z  [OK] Message Data: [AGENT] Query called: message='What is temperature in London?', user=user-001
2026-04-21T18:05:25.456Z  [OK] Message Data: [TOOL] get_temperature called for: London
2026-04-21T18:05:25.567Z  [OK] Message Data: [TOOL] Temperature result: {'city': 'London', 'temperature_celsius': 15...}
2026-04-21T18:05:25.678Z  END RequestId: abc-123-def-456
2026-04-21T18:05:25.789Z  REPORT RequestId: abc-123-def-456 Duration: 45.67 ms Billed Duration: 46 ms Memory Size: 128 MB Max Memory Used: 35 MB
```

## Component Latencies

```
User Query → Reasoning Engine        : < 1 second
Reasoning Engine → Cloud Logging     : 1-2 seconds
Cloud Logging → Pub/Sub (via sink)   : 1-2 seconds
Pub/Sub → Lambda (push)              : 1-2 minutes
Lambda → CloudWatch                  : < 1 second
──────────────────────────────────────────────────
Total End-to-End Latency             : ~2 minutes
```

## Cost Breakdown

### GCP Costs (per month, 10K messages)

| Component | Cost | Details |
|-----------|------|---------|
| Reasoning Engine | $0 | Pay-per-query only |
| Cloud Logging | $1.00 | 10K log entries @ $0.50/GB |
| Pub/Sub Topic | $0.40 | 10K messages @ $40/million |
| Log Sink | $0 | Free (part of Logging) |
| **GCP Total** | **$1.40** | |

### AWS Costs (per month, 10K messages)

| Component | Cost | Details |
|-----------|------|---------|
| Lambda Invocations | $0.20 | 10K invocations @ $0.20/million |
| Lambda Duration | $0.05 | 10K × 50ms @ $0.0000166667/GB-sec |
| CloudWatch Logs | $0.50 | 1GB ingestion @ $0.50/GB |
| **AWS Total** | **$0.75** | |

### Grand Total

**$2.15/month** for 10K messages (or $0.000215 per message)

## Quick Reference: Console Navigation

```
GCP: Vertex AI → Cloud Logging → Pub/Sub → AWS Lambda → CloudWatch
```

---

## GCP Console Flow

### 1. Vertex AI - Agent Engine

**URL**: https://console.cloud.google.com/vertex-ai/agents/agent-engines

**Navigate**: 
```
GCP Console → Vertex AI → Agent Builder → Agent Engine
```

**View**:
- Engine: `adk-style-monitoring-agent`
- Engine ID: `8213677864684355584`
- Status: Active
- Location: us-central1

**Actions**:
- Click engine name to view details
- View Dashboard, Traces, Sessions, Memories tabs
- Note: Playground not available (Python-deployed agent)

---

### 2. Cloud Logging

**URL**: https://console.cloud.google.com/logs/query

**Navigate**:
```
GCP Console → Logging → Logs Explorer
```

**Filter**:
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
resource.labels.reasoning_engine_id="8213677864684355584"
```

**View**:
```
[2026-04-21T18:05:23] [AGENT] Query called: message='What is temperature in London?', user=user-001
[2026-04-21T18:05:23] [TOOL] get_temperature called for: London
[2026-04-21T18:05:23] [TOOL] Temperature result: {'city': 'London', 'temperature_celsius': 15}
[2026-04-21T18:05:23] [AGENT] Analysis complete: INFO - Normal monitoring data
```

---

### 3. Log Router (Sinks)

**URL**: https://console.cloud.google.com/logs/router

**Navigate**:
```
GCP Console → Logging → Log Router
```

**View Sink**: `reasoning-engine-to-pubsub`

**Configuration**:
- Destination: `pubsub.googleapis.com/projects/agentic-ai-integration-490716/topics/reasoning-engine-logs-topic`
- Filter: `resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="8213677864684355584"`
- Service Account: `service-961756870884@gcp-sa-logging.iam.gserviceaccount.com`

---

### 4. Pub/Sub - Topics

**URL**: https://console.cloud.google.com/cloudpubsub/topic/list

**Navigate**:
```
GCP Console → Pub/Sub → Topics
```

**Click**: `reasoning-engine-logs-topic`

**View**:
- Subscriptions: 1 (reasoning-engine-logs-to-aws)
- Message retention: 7 days
- Published messages: [Graph showing message throughput]

**Tabs**:
- Overview
- Metrics (message publish rate)
- Subscriptions
- Schema

---

### 5. Pub/Sub - Subscriptions

**URL**: https://console.cloud.google.com/cloudpubsub/subscription/list

**Navigate**:
```
GCP Console → Pub/Sub → Subscriptions
```

**Click**: `reasoning-engine-logs-to-aws`

**Configuration**:
- Delivery type: Push
- Endpoint: `https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/`
- Ack deadline: 10 seconds
- Message retention: 7 days

**Metrics**:
- Messages published/sec
- Push request latencies
- Unacked message count
- Oldest unacked message age

---

## AWS Console Flow

### 6. Lambda - Functions

**URL**: https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions

**Navigate**:
```
AWS Console → Lambda → Functions
```

**Click**: `gcp-pubsub-test`

**View**:
- Runtime: Python 3.11
- Handler: lambda_function.lambda_handler
- Memory: 128 MB
- Timeout: 2 minutes
- Last modified: [Date]

---

### 7. Lambda - Code Tab

**View Code**:
```python
import json
import base64
from datetime import datetime

def lambda_handler(event, context):
    # Process GCP Pub/Sub message
    if 'body' in event:
        body = json.loads(event['body'])
    else:
        body = event
    
    message = body['message']
    decoded = base64.b64decode(message['data']).decode('utf-8')
    
    print(f"[OK] Message: {decoded}")
    
    return {'statusCode': 200, 'body': 'success'}
```

---

### 8. Lambda - Configuration Tab

**Function URL**:
- URL: `https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/`
- Auth type: NONE
- CORS: Not configured

**General configuration**:
- Memory: 128 MB
- Ephemeral storage: 512 MB
- Timeout: 2 min

**Permissions**:
- Execution role: `gcp-pubsub-test-role-xyz`

---

### 9. Lambda - Monitor Tab

**Metrics** (Graphs):

**Invocations**:
- Total invocations over time
- Success rate: 100%

**Duration**:
- Average: 45 ms
- P50: 42 ms
- P90: 58 ms
- P99: 75 ms

**Errors**:
- Error count: 0
- Error rate: 0%

**Throttles**:
- Throttled invocations: 0

**Concurrent executions**:
- Current: 1-2

---

### 10. CloudWatch - Logs

**URL**: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups

**Navigate**:
```
AWS Console → CloudWatch → Log groups
OR
Lambda → Monitor tab → View CloudWatch logs
```

**Log Group**: `/aws/lambda/gcp-pubsub-test`

**Log Streams** (latest first):
```
2026/04/21/[$LATEST]abc123def456
2026/04/21/[$LATEST]xyz789ghi012
```

**Log Events**:
```
START RequestId: abc-123 Version: $LATEST

[2026-04-21T18:05:24.123Z] === Received event from GCP Pub/Sub ===

[OK] Message Data: [AGENT] Query called: message='What is temperature in London?'

[OK] Message Data: [TOOL] get_temperature called for: London

[OK] Message Data: [TOOL] Temperature result: {'city': 'London', 'temperature_celsius': 15}

END RequestId: abc-123
REPORT RequestId: abc-123
    Duration: 45.67 ms
    Billed Duration: 46 ms
    Memory Size: 128 MB
    Max Memory Used: 35 MB
```

---

### 11. CloudWatch - Logs Insights

**URL**: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights

**Navigate**:
```
CloudWatch → Logs → Insights
```

**Select Log Group**: `/aws/lambda/gcp-pubsub-test`

**Query 1: Find all tool calls**
```sql
fields @timestamp, @message
| filter @message like /\[TOOL\]/
| sort @timestamp desc
| limit 100
```

**Query 2: Count errors by user**
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| parse @message "user_id='*'" as user
| stats count() by user
```

**Query 3: Get temperature tool usage**
```sql
fields @timestamp, @message
| filter @message like /get_temperature/
| parse @message "called for: *" as city
| stats count() by city
```

**Query 4: Track session activity**
```sql
fields @timestamp, @message
| filter @message like /session_id/
| parse @message "session_id='*'" as session
| stats count() by session
| sort count() desc
```

---

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ GCP Console: Vertex AI → Agent Engine                       │
│                                                              │
│ https://console.cloud.google.com/vertex-ai/agents/          │
│ agent-engines/locations/us-central1/agent-engines/          │
│ 8213677864684355584                                         │
│                                                              │
│ Engine: adk-style-monitoring-agent                          │
│ Status: Active                                              │
│ [Dashboard] [Traces] [Sessions] [Memories]                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Automatic logging (1-2 sec)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ GCP Console: Cloud Logging → Logs Explorer                  │
│                                                              │
│ https://console.cloud.google.com/logs/query                 │
│                                                              │
│ Filter: reasoning_engine_id="8213677864684355584"           │
│                                                              │
│ [AGENT] Query called                                        │
│ [TOOL] get_temperature called                               │
│ [TOOL] Temperature result                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Log Sink (automatic)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ GCP Console: Logging → Log Router                           │
│                                                              │
│ https://console.cloud.google.com/logs/router                │
│                                                              │
│ Sink: reasoning-engine-to-pubsub                            │
│ Destination: Pub/Sub topic                                  │
│ Status: Active                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Forward to Pub/Sub
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ GCP Console: Pub/Sub → Topics                               │
│                                                              │
│ https://console.cloud.google.com/cloudpubsub/topic/detail/  │
│ reasoning-engine-logs-topic                                 │
│                                                              │
│ Messages: [Graph]                                           │
│ Subscriptions: 1 (reasoning-engine-logs-to-aws)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Push subscription
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ GCP Console: Pub/Sub → Subscriptions                        │
│                                                              │
│ https://console.cloud.google.com/cloudpubsub/subscription/  │
│ detail/reasoning-engine-logs-to-aws                         │
│                                                              │
│ Type: Push                                                  │
│ Endpoint: Lambda Function URL                               │
│ Metrics: [Message rate] [Latency] [Ack]                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTPS Push (1-2 min delay)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ AWS Console: Lambda → Functions → gcp-pubsub-test           │
│                                                              │
│ https://us-east-1.console.aws.amazon.com/lambda/home        │
│ region=us-east-1#/functions/gcp-pubsub-test                 │
│                                                              │
│ Runtime: Python 3.11                                        │
│ [Code] [Test] [Monitor] [Configuration]                     │
│                                                              │
│ Function URL: Active (receives Pub/Sub pushes)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Logs to CloudWatch
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ AWS Console: CloudWatch → Logs                              │
│                                                              │
│ https://us-east-1.console.aws.amazon.com/cloudwatch/home    │
│ region=us-east-1#logsV2:log-groups/log-group/              │
│ $252Faws$252Flambda$252Fgcp-pubsub-test                    │
│                                                              │
│ [Log Streams] → Latest stream                               │
│                                                              │
│ START RequestId...                                          │
│ [OK] Message Data: [AGENT] Query...                         │
│ [OK] Message Data: [TOOL] get_temperature...                │
│ END RequestId...                                            │
│ REPORT Duration: 45ms Memory: 35MB                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Testing Flow

### Test from Local Machine

**Step 1: Run test**
```bash
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup\lambda_poc
python test_local.py
```

### Step 2: View in GCP Console (1-2 seconds)

**Go to Cloud Logging**:
```
https://console.cloud.google.com/logs/query
```

**Filter**:
```
resource.labels.reasoning_engine_id="8213677864684355584"
```

**See**:
- Agent logs appear immediately
- Tool calls visible
- Analysis results shown

### Step 3: View in Pub/Sub (1-2 seconds)

**Go to Pub/Sub Topic**:
```
https://console.cloud.google.com/cloudpubsub/topic/detail/reasoning-engine-logs-topic
```

**See**:
- Message count increases
- Publish rate graph updates

### Step 4: View in Pub/Sub Subscription (1-2 seconds)

**Go to Subscription**:
```
https://console.cloud.google.com/cloudpubsub/subscription/detail/reasoning-engine-logs-to-aws
```

**See**:
- Messages being pushed to Lambda
- Push latency metrics
- Ack deadline tracking

### Step 5: View in AWS Lambda Monitor (1-2 minutes)

**Go to Lambda Monitor**:
```
https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/gcp-pubsub-test?tab=monitoring
```

**See**:
- Invocation count increases
- Duration metrics update
- Success rate: 100%

### Step 6: View in CloudWatch Logs (1-2 minutes)

**Go to CloudWatch Logs**:
```
https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups
```

**Click**: `/aws/lambda/gcp-pubsub-test`

**See**:
- New log stream created
- GCP agent logs visible in AWS
- Tool execution results shown

---

## Quick Access URLs

### GCP Console

| Component | URL |
|-----------|-----|
| Vertex AI Agent | https://console.cloud.google.com/vertex-ai/agents/agent-engines |
| Cloud Logging | https://console.cloud.google.com/logs/query |
| Log Router | https://console.cloud.google.com/logs/router |
| Pub/Sub Topics | https://console.cloud.google.com/cloudpubsub/topic/list |
| Pub/Sub Subscriptions | https://console.cloud.google.com/cloudpubsub/subscription/list |

### AWS Console

| Component | URL |
|-----------|-----|
| Lambda Functions | https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions |
| CloudWatch Logs | https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups |
| CloudWatch Insights | https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights |

---

## Timing Reference

| Event | Timing |
|-------|--------|
| Agent executes query | Immediate |
| Logs appear in Cloud Logging | 1-2 seconds |
| Logs forwarded to Pub/Sub | 1-2 seconds |
| Pub/Sub pushes to Lambda | 1-2 minutes |
| Logs visible in CloudWatch | 1-2 minutes |

**Total end-to-end latency: ~2 minutes**

---

## Summary

**GCP Side (5 screens)**:
1. Vertex AI Agent Engine - View agent status
2. Cloud Logging - Real-time agent logs
3. Log Router - Sink configuration
4. Pub/Sub Topic - Message queue
5. Pub/Sub Subscription - Push delivery

**AWS Side (3 screens)**:
1. Lambda Function - Code and config
2. Lambda Monitor - Metrics and graphs
3. CloudWatch Logs - Log analysis

**All components visible in console UI - complete observability!**
