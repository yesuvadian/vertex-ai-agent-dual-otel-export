# Complete Architecture: Agent → Pub/Sub → AWS Lambda with OIDC

## OIDC Authentication Chain

```
1. GCP Service Account → Generates JWT token
2. JWT Token → Signed by Google's private key
3. Pub/Sub → Adds token to Authorization header
4. AWS Lambda → Receives token
5. Google OAuth API → Verifies token signature
6. Lambda → Validates audience matches Lambda URL
7. Lambda → Validates issuer is Google
8. Result → ✅ Authenticated and processed OR ❌ Rejected
```

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGENT PROMPT / QUERY                                 │
│                                                                              │
│  User Query: "What's the temperature in London?"                            │
│  OR                                                                          │
│  Monitoring Alert: "Database ERROR detected"                                │
│  OR                                                                          │
│  API Request: engine.query(message="...", user_id="...")                    │
└─────────────────────────────┬────────────────────────────────────────────────┘
                              │
                              │ Query submitted to Agent
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOOGLE CLOUD PLATFORM                                │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  VERTEX AI REASONING ENGINE                                            │ │
│  │  Name: adk-style-monitoring-agent                                      │ │
│  │  ID: 8213677864684355584                                               │ │
│  │                                                                         │ │
│  │  SimpleADKAgent:                                                        │ │
│  │  • Receives: "What's temperature in London?"                           │ │
│  │  • Thinks: "I need get_temperature tool"                               │ │
│  │  • Executes: get_temperature('London')                                 │ │
│  │  • Result: {temp: 15°C, condition: "Cloudy"}                           │ │
│  │  • Logs: Query received, tool executed, results generated              │ │
│  └────────────────────────┬────────────────────────────────────────────────┘ │
│                           │                                                  │
│                           │ Automatic (stdout/stderr capture)                │
│                           │ Latency: ~1-2 seconds                            │
│                           ↓                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  CLOUD LOGGING                                                         │ │
│  │  Service: aiplatform.googleapis.com/ReasoningEngine                    │ │
│  │                                                                         │ │
│  │  Logs captured with:                                                    │ │
│  │  • Engine ID: 8213677864684355584                                      │ │
│  │  • Project ID: agentic-ai-integration-490716                           │ │
│  │  • Log content: Agent actions, tool calls, results                     │ │
│  │  • Timestamps: Automatic                                               │ │
│  │                                                                         │ │
│  │  Retention: 30 days (default)                                          │ │
│  └────────────────────────┬────────────────────────────────────────────────┘ │
│                           │                                                  │
│                           │ Log Sink Filter                                  │
│                           │ Latency: ~1-2 seconds                            │
│                           ↓                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  LOG SINK                                                              │ │
│  │  Name: reasoning-engine-to-pubsub                                      │ │
│  │                                                                         │ │
│  │  Filter Rule:                                                           │ │
│  │  resource.type="aiplatform.googleapis.com/ReasoningEngine"             │ │
│  │  AND reasoning_engine_id="8213677864684355584"                         │ │
│  │                                                                         │ │
│  │  Action:                                                                │ │
│  │  IF log matches → Forward to Pub/Sub                                   │ │
│  │  ELSE → Ignore                                                          │ │
│  │                                                                         │ │
│  │  Destination: projects/.../topics/reasoning-engine-logs-topic          │ │
│  └────────────────────────┬────────────────────────────────────────────────┘ │
│                           │                                                  │
│                           │ Forwards matching logs                           │
│                           ↓                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  PUB/SUB TOPIC                                                         │ │
│  │  Name: reasoning-engine-logs-topic                                     │ │
│  │                                                                         │ │
│  │  Message Queue:                                                         │ │
│  │  • Stores log entries from Cloud Logging                               │ │
│  │  • Encoded format for transmission                                     │ │
│  │  • Includes message ID and timestamp                                   │ │
│  │                                                                         │ │
│  │  Retention: 7 days                                                     │ │
│  └────────────────────────┬────────────────────────────────────────────────┘ │
│                           │                                                  │
│                           │ Subscription pulls messages                      │
│                           ↓                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  PUB/SUB SUBSCRIPTION                                                  │ │
│  │  Name: reasoning-engine-to-oidc                                        │ │
│  │  Type: Push (actively sends to endpoint)                               │ │
│  │                                                                         │ │
│  │  Configuration:                                                         │ │
│  │  • Push Endpoint: https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor...         │ │
│  │  • Authentication: OIDC                                                 │ │
│  │  • Service Account: pubsub-oidc-invoker@...                           │ │
│  │  • Token Audience: https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor...        │ │
│  │  • Ack Deadline: 10 seconds                                            │ │
│  │                                                                         │ │
│  │  Before sending each message:                                           │ │
│  │  1. Request JWT token from GCP IAM ─────────────────┐                 │ │
│  └─────────────────────────┬────────────────────────────┼─────────────────┘ │
│                            │                            │                   │
│                            │                            ↓                   │
│  ┌─────────────────────────┼────────────────────────────────────────────┐ │
│  │  GCP IAM (Identity & Access Management)             │                 │ │
│  │                                                      │                 │ │
│  │  Generates JWT Token with:                          │                 │ │
│  │  • Issuer: Google                                   │                 │ │
│  │  • Service Account ID                               │                 │ │
│  │  • Audience: Lambda URL                             │                 │ │
│  │  • Expiration: 1 hour                               │                 │ │
│  │  • Signature: Google's private key                  │                 │ │
│  │                                                      │                 │ │
│  │  Returns token to Pub/Sub ──────────────────────────┘                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                            │                                                 │
│                            │ Token received                                  │
│                            ↓                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  PUB/SUB SUBSCRIPTION (continued)                                      │ │
│  │                                                                         │ │
│  │  2. Sends HTTPS POST to AWS Lambda                                      │ │
│  │     • Endpoint: Lambda Function URL                                    │ │
│  │     • Headers: Authorization with JWT token                            │ │
│  │     • Body: Encoded log data with metadata                             │ │
│  │     • Includes automatic retry on failure                              │ │
│  └────────────────────────┬────────────────────────────────────────────────┘ │
│                           │                                                  │
└───────────────────────────┼──────────────────────────────────────────────────┘
                            │
                            │ HTTPS POST with JWT token
                            │ Cross-cloud communication (GCP → AWS)
                            │ Latency: ~1-2 minutes (batching + retries)
                            ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AMAZON WEB SERVICES                                  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  AWS LAMBDA FUNCTION                                                   │ │
│  │  Name: gcp-pubsub-oidc                                                 │ │
│  │  Runtime: Python 3.11                                                  │ │
│  │  Handler: lambda_with_oidc_simple.lambda_handler                       │ │
│  │  Memory: 256 MB                                                        │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  STEP 1: RECEIVE REQUEST                                         │  │ │
│  │  │                                                                   │  │ │
│  │  │  • Receives HTTPS POST from GCP Pub/Sub                          │  │ │
│  │  │  • Headers contain Authorization token                           │  │ │
│  │  │  • Body contains encoded log data                                │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │           ↓                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  STEP 2: EXTRACT JWT TOKEN                                       │  │ │
│  │  │                                                                   │  │ │
│  │  │  • Reads Authorization header                                    │  │ │
│  │  │  • Extracts JWT token from "Bearer <token>" format               │  │ │
│  │  │                                                                   │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │           ↓                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  STEP 3: VERIFY JWT WITH GOOGLE                                  │  │ │
│  │  │                                                                   │  │ │
│  │  │  • Calls Google OAuth API for verification                       │  │ │
│  │  │                                                                   │  │ │
│  │  │  Google verifies:                                                │  │ │
│  │  │  • Token signature (using Google's public key)                   │  │ │
│  │  │  • Token not expired                                             │  │ │
│  │  │  • Token issuer is Google                                        │  │ │
│  │  │                                                                   │  │ │
│  │  │  Google confirms:                                                 │  │ │
│  │  │  • Valid service account                                         │  │ │
│  │  │  • Token audience and issuer                                     │  │ │
│  │  │                                                                   │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │           ↓                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  STEP 4: VALIDATE AUDIENCE                                       │  │ │
│  │  │                                                                   │  │ │
│  │  │  • Compares token audience with Lambda URL                       │  │ │
│  │  │  • Ensures token is specifically for THIS Lambda                 │  │ │
│  │  │                                                                   │  │ │
│  │  │  if audience doesn't match:                                      │  │ │
│  │  │      return 403 Forbidden                                        │  │ │
│  │  │                                                                   │  │ │
│  │  │  ✅ Audience validated!                                           │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │           ↓                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  STEP 5: VALIDATE ISSUER                                         │  │ │
│  │  │                                                                   │  │ │
│  │  │  • Verifies token issued by Google                               │  │ │
│  │  │  • Ensures not from unauthorized source                          │  │ │
│  │  │                                                                   │  │ │
│  │  │  if issuer is not Google:                                        │  │ │
│  │  │      return 403 Forbidden                                        │  │ │
│  │  │                                                                   │  │ │
│  │  │  ✅ Issuer validated!                                             │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │           ↓                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  STEP 6: PROCESS MESSAGE                                         │  │ │
│  │  │                                                                   │  │ │
│  │  │  ✅ All authentication passed! Safe to process.                   │  │ │
│  │  │                                                                   │  │ │
│  │  │  • Extracts message body                                         │  │ │
│  │  │  • Decodes log data                                              │  │ │
│  │  │  • Processes agent logs                                          │  │ │
│  │  │                                                                   │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │           ↓                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  STEP 7: RETURN SUCCESS RESPONSE                                 │  │ │
│  │  │                                                                   │  │ │
│  │  │  • Returns HTTP 200 OK to Pub/Sub                                │  │ │
│  │  │  • Confirms successful processing                                │  │ │
│  │  │                                                                   │  │ │
│  │  │  This tells Pub/Sub: "Message delivered successfully"            │  │ │
│  │  │  Pub/Sub marks message as acknowledged and removes from queue    │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────┬────────────────────────────────────────────────┘ │
│                           │                                                  │
│                           │ Forwards to Portal26                             │
│                           ↓                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  PORTAL26 OBSERVABILITY PLATFORM                                       │ │
│  │                                                                         │ │
│  │  OTEL (OpenTelemetry) Endpoint:                                        │ │
│  │  • Receives processed data from Lambda                                 │ │
│  │  • Converts to OTEL standard format                                    │ │
│  │  • Traces, Logs, Metrics correlation                                   │ │
│  │                                                                         │ │
│  │  Storage Options:                                                       │ │
│  │  • S3: Long-term storage and archival                                  │ │
│  │  • Kinesis: Real-time streaming analytics                              │ │
│  │                                                                         │ │
│  │  Features:                                                              │ │
│  │  • Multi-tenant support                                                │ │
│  │  • Customer-specific dashboards                                        │ │
│  │  • Alerting and monitoring                                             │ │
│  │  • Query and analysis tools                                            │ │
│  │                                                                         │ │
│  │  Audit Trail:                                                           │ │
│  │  • Service account authentication history                              │ │
│  │  • Message processing timestamps                                       │ │
│  │  • Authentication success/failure logs                                 │ │
│  │  • Complete data lineage (GCP → AWS → Portal26)                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Authentication Flow Detail

```
┌──────────────────────────────────────────────────────────────────────┐
│  OIDC AUTHENTICATION CHAIN                                            │
└──────────────────────────────────────────────────────────────────────┘

Step 1: Service Account Generates Identity
┌─────────────────────────────────────────────┐
│ Service Account                              │
│ pubsub-oidc-invoker@...                     │
│                                              │
│ Purpose: Generate OIDC tokens for Pub/Sub   │
│ Role: Service Account Token Creator          │
│ Unique ID: 110137324543273212422            │
└─────────────────────────────────────────────┘
           │
           │ 1. Pub/Sub needs to send message
           │ 2. Requests JWT token
           ↓
┌─────────────────────────────────────────────┐
│ GCP IAM (Token Generator)                   │
│                                              │
│ Creates JWT Token:                          │
│ • Header: Algorithm, Type, Key ID           │
│ • Payload: Issuer, Subject, Audience, Email │
│ • Signature: Signed with Google private key │
│                                              │
│ Token proves:                                │
│ "I am pubsub-oidc-invoker service account"  │
│ "I want to send to THIS specific Lambda"    │
│ "This token expires in 1 hour"              │
│ "Google issued this token"                  │
└─────────────────────────────────────────────┘
           │
           │ 3. Returns JWT token to Pub/Sub
           ↓
┌─────────────────────────────────────────────┐
│ Pub/Sub Subscription                        │
│                                              │
│ Adds token to HTTP request:                 │
│ Authorization: Bearer <JWT_token>           │
│                                              │
│ Sends to AWS Lambda                         │
└─────────────────────────────────────────────┘
           │
           │ 4. HTTPS POST with JWT token
           │ (Cross-cloud: GCP → AWS)
           ↓
┌─────────────────────────────────────────────┐
│ AWS Lambda                                   │
│                                              │
│ Receives: Authorization header with token   │
│                                              │
│ Extracts token from header                  │
└─────────────────────────────────────────────┘
           │
           │ 5. Needs to verify token
           │ Calls Google OAuth API
           ↓
┌─────────────────────────────────────────────┐
│ Google OAuth API                             │
│ https://oauth2.googleapis.com/tokeninfo     │
│                                              │
│ Verifies:                                    │
│ ✓ Signature valid (using public key)        │
│ ✓ Token not expired                         │
│ ✓ Token issued by Google                    │
│                                              │
│ Returns token info to Lambda                │
└─────────────────────────────────────────────┘
           │
           │ 6. Returns token validation result
           ↓
┌─────────────────────────────────────────────┐
│ AWS Lambda (continued)                       │
│                                              │
│ Validates:                                   │
│ ✓ Audience matches Lambda URL                │
│ ✓ Issuer is Google                          │
│                                              │
│ Decision:                                    │
│ ✅ All checks passed → Process message       │
│ ❌ Any check failed → Reject with 403        │
└─────────────────────────────────────────────┘
```


## Data Flow Timeline

```
Time    Location           Action
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
00:00   Agent Prompt       Query submitted: "What's the temperature in London?"

00:01   Vertex AI          Agent receives query
                          Executes: get_temperature('London')
                          Result: 15°C, Cloudy
                          Logs: [AGENT], [TOOL] messages

00:03   Cloud Logging      Captures all agent log statements
                          Creates structured log entries

00:05   Log Sink           Filters logs by engine ID
                          Forwards matching logs to Pub/Sub

00:07   Pub/Sub Topic      Receives 4 log messages
                          Stores in queue

01:00   Pub/Sub Sub        Retrieves messages from topic
                          Requests JWT token from GCP IAM

01:01   GCP IAM            Generates JWT token
                          Signs with Google's private key
                          Returns token (valid for 1 hour)

01:02   Pub/Sub Sub        Adds JWT to Authorization header
                          Sends HTTPS POST to AWS Lambda

01:03   AWS Lambda         Receives request
                          Extracts JWT token from header

01:04   Lambda → Google    Calls Google OAuth API
                          Verifies JWT signature and claims

01:05   Google → Lambda    Returns: "Token valid, issued by me"

01:06   Lambda             Validates audience & issuer
                          ✅ All checks passed

01:07   Lambda             Decodes message data
                          Reads: [AGENT] Query called...
                          Logs to CloudWatch

01:08   Lambda → Pub/Sub   Returns: 200 OK

01:09   Pub/Sub            Marks message as delivered
                          Removes from queue

01:10   Lambda → Portal26  Forwards to OTEL endpoint

01:11   Portal26           Converts to OTEL format
                          Stores in S3 / Kinesis
                          Updates dashboards

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Latency: ~1 minute 10 seconds (from agent execution to AWS processing)
```

## Component Summary

| Component | Location | Purpose | Authentication |
|-----------|----------|---------|----------------|
| **SimpleADKAgent** | GCP Vertex AI | Executes queries, uses tools, generates logs | N/A (internal) |
| **Cloud Logging** | GCP | Captures agent logs automatically | N/A (automatic) |
| **Log Sink** | GCP | Filters and routes logs to Pub/Sub | N/A (automatic) |
| **Pub/Sub Topic** | GCP | Queues messages for delivery | N/A (internal) |
| **Pub/Sub Subscription** | GCP | Delivers messages with OIDC auth | Generates JWT tokens |
| **GCP IAM** | GCP | Issues JWT tokens for service accounts | N/A (system service) |
| **AWS Lambda** | AWS | Validates JWT and processes messages | Verifies JWT with Google |
| **Portal26 OTEL** | AWS/Portal26 | OTEL endpoint, S3 storage, Kinesis streaming | N/A (receives from Lambda) |

## Key URLs

**GCP Console:**
- Vertex AI Agent: https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/8213677864684355584
- Cloud Logging: https://console.cloud.google.com/logs/query?project=agentic-ai-integration-490716
- Pub/Sub Topic: https://console.cloud.google.com/cloudpubsub/topic/detail/reasoning-engine-logs-topic?project=agentic-ai-integration-490716
- Pub/Sub Subscription: https://console.cloud.google.com/cloudpubsub/subscription/detail/reasoning-engine-to-oidc?project=agentic-ai-integration-490716
- Service Account: https://console.cloud.google.com/iam-admin/serviceaccounts/details/110137324543273212422?project=agentic-ai-integration-490716

**AWS Console:**
- Lambda Function: https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/gcp-pubsub-oidc
- S3 Storage: (Portal26 bucket configuration)
- Kinesis Streams: (Portal26 stream configuration)

**Portal26 Platform:**
- OTEL Endpoint: (Customer-specific endpoint)
- Dashboard: (Multi-tenant observability dashboard)

**Endpoints:**
- Lambda Function URL: https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor.lambda-url.us-east-1.on.aws/
- Google OAuth Verify: https://oauth2.googleapis.com/tokeninfo
