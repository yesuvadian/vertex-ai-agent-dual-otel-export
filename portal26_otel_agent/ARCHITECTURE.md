# Portal26 OTEL Agent - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Query via Console                        │
│              (Vertex AI Playground / API Call)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Vertex AI Reasoning Engine                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  portal26_otel_complete Agent                             │  │
│  │  (Cloud Run Container - Managed by Vertex AI)            │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  OpenTelemetry Instrumentation                  │    │  │
│  │  │  ┌──────────┬──────────┬──────────┐            │    │  │
│  │  │  │ Traces   │ Metrics  │  Logs    │            │    │  │
│  │  │  │ (200 OK) │ (404*)   │ (200 OK) │            │    │  │
│  │  │  └────┬─────┴────┬─────┴────┬─────┘            │    │  │
│  │  │       │          │          │                   │    │  │
│  │  └───────┼──────────┼──────────┼───────────────────┘    │  │
│  │          │          │          │                         │  │
│  │  ┌───────▼──────────▼──────────▼─────────────────┐      │  │
│  │  │  OTLP HTTP Exporters                          │      │  │
│  │  │  - OTLPSpanExporter                           │      │  │
│  │  │  - OTLPMetricExporter                         │      │  │
│  │  │  - OTLPLogExporter                            │      │  │
│  │  └─────────────────┬─────────────────────────────┘      │  │
│  └────────────────────┼────────────────────────────────────┘  │
└───────────────────────┼───────────────────────────────────────┘
                        │
                        │ OTLP/HTTP (Protobuf)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│           Portal26 OTEL Collector                                │
│        https://otel-tenant1.portal26.in:4318                    │
│                                                                   │
│  Endpoints:                                                      │
│    /v1/traces  → ✓ 200 OK                                       │
│    /v1/metrics → ✗ 404 (Disabled in staging)                    │
│    /v1/logs    → ✓ 200 OK                                       │
│                                                                   │
│  Authentication: Basic Auth (base64 encoded)                     │
│  Multi-tenant tags: tenant1, relusys                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ OTLP Data
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              AWS Kinesis Data Stream                             │
│        stg_otel_source_data_stream (us-east-2)                  │
│                                                                   │
│  Shards: shardId-000000000006                                   │
│  Retention: 24 hours                                             │
│  Format: JSON (not base64 encoded)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Pull via boto3
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Data Collection & Analysis                          │
│                                                                   │
│  pull_agent_logs.py                                             │
│    ↓                                                              │
│  agent_logs_TIMESTAMP.jsonl                                     │
│    ↓                                                              │
│  show_traces.py → Parsed trace structure                        │
│    ↓                                                              │
│  all_traces.json → Complete trace data                          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Vertex AI Reasoning Engine
- **Platform**: Google Cloud Vertex AI
- **Runtime**: Managed Cloud Run container
- **Python Version**: 3.11
- **Region**: us-central1
- **Auto-scaling**: Managed by Vertex AI
- **Observability**: Built-in OTEL instrumentation

### 2. Agent Code (agent.py)

```python
# Initialization Order (Critical!)
1. Import OpenTelemetry libraries
2. Configure OTEL exporters (module load time)
3. Set global tracer/meter/logger providers
4. Import Google ADK Agent
5. Define tools (get_weather, get_current_time)
6. Create Agent instance
```

**Resource Attributes:**
```python
{
    "service.name": "portal26_otel_agent",
    "portal26.tenant_id": "tenant1",
    "portal26.user.id": "relusys",
    "agent.type": "otel-direct"
}
```

### 3. OpenTelemetry Signals

#### Traces
- **Exporter**: `OTLPSpanExporter`
- **Processor**: `BatchSpanProcessor`
- **Endpoint**: `https://otel-tenant1.portal26.in:4318/v1/traces`
- **Protocol**: HTTP + Protobuf
- **Status**: ✓ 200 OK

**Captured Data:**
- Trace ID, Span ID, Parent Span ID
- Span name, kind, timing
- HTTP request/response metadata
- LLM call metadata (model, operation)
- Token usage (input, output, reasoning)
- Tool execution timing
- Resource attributes (tenant, user, service)

**Sample Span:**
```json
{
  "traceId": "0000000000000000cefd10716a1122d1",
  "spanId": "9af226ff09117061",
  "name": "generate_content gemini-2.5-flash",
  "kind": 1,
  "startTimeUnixNano": "1775558747567648812",
  "endTimeUnixNano": "1775558748540838157",
  "attributes": {
    "gen_ai.request.model": "gemini-2.5-flash",
    "gen_ai.usage.input_tokens": 106,
    "gen_ai.usage.output_tokens": 6
  }
}
```

#### Metrics
- **Exporter**: `OTLPMetricExporter`
- **Reader**: `PeriodicExportingMetricReader` (10s interval)
- **Endpoint**: `https://otel-tenant1.portal26.in:4318/v1/metrics`
- **Status**: ✗ 404 (Disabled in staging environment)

**Impact**: Generates error logs but does not break traces/logs.

#### Logs
- **Exporter**: `OTLPLogExporter`
- **Processor**: `BatchLogRecordProcessor`
- **Endpoint**: `https://otel-tenant1.portal26.in:4318/v1/logs`
- **Status**: ✓ 200 OK
- **Level**: INFO

**Captured Data:**
- Log severity (ERROR, INFO, etc.)
- Log message body
- Timestamp (Unix nano)
- Resource attributes
- Source file/function/line number

### 4. Portal26 OTEL Collector
- **URL**: `https://otel-tenant1.portal26.in:4318`
- **Protocol**: OTLP over HTTP
- **Authentication**: Basic Auth header
- **Multi-tenancy**: Via resource attributes
- **Backend**: AWS Kinesis Data Streams

### 5. AWS Kinesis Data Stream
- **Stream Name**: `stg_otel_source_data_stream`
- **Region**: us-east-2
- **Shard**: `shardId-000000000006`
- **Data Format**: JSON (UTF-8 encoded, not base64)
- **Retention**: 24 hours
- **Access**: AWS credentials (IAM)

**Record Structure:**
```json
{
  "resourceSpans": [...],  // Trace data
  "resourceLogs": [...]    // Log data
}
```

### 6. Data Collection Tools

#### pull_agent_logs.py
```python
# Configuration
STREAM_NAME = "stg_otel_source_data_stream"
SHARD_ID = "shardId-000000000006"
TIME_RANGE = "Last 5 minutes"

# Filters
- tenant1
- relusys
- portal26_agent
- portal26_otel

# Output
agent_logs_TIMESTAMP.jsonl
```

#### show_traces.py
- Parses multi-line JSON records
- Extracts traces and logs
- Displays trace hierarchy
- Shows span timing and attributes

## Data Flow

### Query Processing Flow

```
1. User sends query → Vertex AI Playground
                      ↓
2. ReasoningEngine receives query → AgentWrapper.query()
                      ↓
3. Agent.run_live() → Agent decides to call tool
                      ↓
4. OTEL automatically instruments:
   - HTTP receive span (FastAPI)
   - Agent call_llm span
   - LLM generate_content span
   - Tool execution span
   - HTTP send spans (response chunks)
                      ↓
5. BatchSpanProcessor collects spans (every 30s)
                      ↓
6. OTLPSpanExporter sends to Portal26
                      ↓
7. Portal26 forwards to Kinesis
                      ↓
8. Available for retrieval (1-2 min latency)
```

### Telemetry Export Flow

```
Trace Span Created
       ↓
BatchSpanProcessor buffer (max 512 spans or 30s)
       ↓
OTLPSpanExporter serializes to Protobuf
       ↓
HTTP POST to https://otel-tenant1.portal26.in:4318/v1/traces
       ↓
Portal26 validates & enriches with tenant metadata
       ↓
Kinesis PutRecords API
       ↓
Data available in shardId-000000000006
       ↓
pull_agent_logs.py fetches via GetRecords API
```

## Deployment Architecture

### Packaging
```
reasoning_engine/
├── reasoning_engine.pkl      # Serialized AgentWrapper
├── requirements.txt          # Python dependencies
└── dependencies.tar.gz       # Extra packages (agent.py, tools)
```

### Vertex AI Deployment

```python
reasoning_engines.ReasoningEngine.create(
    wrapped_agent,  # AgentWrapper with query() method
    requirements=[
        "google-cloud-aiplatform[reasoningengine,langchain]",
        "opentelemetry-api",
        "opentelemetry-sdk",
        "opentelemetry-instrumentation",
        "opentelemetry-exporter-otlp-proto-http"
    ]
)
```

**Deployed Container:**
- Base image: Vertex AI managed Python runtime
- OpenTelemetry SDK installed at container start
- OTEL providers initialized at module import time
- Environment variables set via Vertex AI config

### Multi-Tenant Isolation

All telemetry data tagged with:
```json
{
  "portal26.tenant_id": "tenant1",
  "portal26.user.id": "relusys"
}
```

Kinesis records filtered by these tags during retrieval.

## Security

### Authentication
- **Portal26**: Basic Auth (base64 encoded credentials)
- **Kinesis**: AWS IAM credentials (Access Key + Secret)
- **Vertex AI**: Google Cloud IAM (Application Default Credentials)

### Data Privacy
- Vertex AI limitation: Cannot capture full prompt/response content
- Only metadata, timing, and structure captured
- No PII in default telemetry configuration

## Scalability

### Vertex AI Auto-scaling
- Automatic based on request volume
- Cold start: ~2-3 seconds
- Warm instances maintained by platform

### Kinesis Throughput
- 1 MB/s write per shard
- 5 reads/s per shard
- Current usage: <<1% capacity

### OTEL Batch Processing
- Spans batched (max 512 or 30s)
- Reduces network overhead
- Automatic retry on failure

## Monitoring & Observability

### Agent Health
- Check Vertex AI Reasoning Engine status
- Monitor Cloud Run logs
- Verify OTEL initialization messages

### Telemetry Pipeline Health
- Portal26 endpoint status (200 OK expected)
- Kinesis stream throughput metrics
- Data latency (typically 1-2 minutes)

### Key Metrics
- Trace export success rate
- Log export success rate
- Metrics export failure rate (404 expected)
- Average span duration
- Token usage per request

---

## Platform Constraints (Vertex AI Reasoning Engine)

### Managed Runtime Limitations

Vertex AI Reasoning Engine provides a **fully managed environment** which means:

#### ✗ No Direct Access
- **No SSH/console** access to Cloud Run container
- **No file system** inspection after deployment
- **No debugger** attachment to running processes
- **Cannot modify** running container configuration
- **Limited visibility** into OTEL internal state

#### ✗ Environment Control
```
Deployment Package → GCS Bucket → Cloud Run Container
                                         ↓
                            Platform injects OTEL
                            Platform sets env vars
                            Platform manages lifecycle
                                         ↓
                            Your code runs (limited control)
```

- **Cannot set env vars** via Vertex AI API
- **.env files ignored** during deployment
- **Must hardcode configuration** in Python code
- **No runtime config updates** without redeployment

#### ✗ OpenTelemetry Customization
```python
# What you CANNOT do:
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"  # Ignored
trace.set_tracer_provider(custom_provider)  # Overridden by platform

# What you CAN do:
trace.set_tracer_provider(provider)  # Set BEFORE platform injection
# Must happen at module load time
```

**Platform behavior:**
1. Your agent.py imports and sets OTEL providers
2. Platform wraps agent with additional instrumentation
3. Platform's instrumentation takes precedence for GenAI spans
4. Your traces work, but content capture controlled by platform

#### ✗ Network and Security
- **Outbound HTTPS only** - Portal26 must use HTTPS
- **No custom VPC** configuration via API
- **No static IP** - changes with auto-scaling
- **Certificate management** handled by platform
- **Cannot whitelist** specific Cloud Run instances

#### ✗ Deployment Constraints
- **Build time**: 2-5 minutes average
- **Max package size**: ~500MB (Cloud Run limit)
- **Python version**: Platform-managed (3.11)
- **System packages**: Only via requirements.txt
- **Binary dependencies**: Limited support

### Implications for This Project

#### Content Capture Disabled
```
User Query → Vertex AI Agent → Platform OTEL → Portal26
                                      ↓
                            Content redacted by platform
                            Only metadata exported
```

**Why:**
- Platform controls `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`
- Set to `false` for privacy/compliance
- No API to override this setting
- Managed runtime doesn't expose container env vars

**Workaround:**
- Accept limitation for managed deployment
- OR deploy to Cloud Run directly (lose Vertex AI features)

#### Query Method Requirement
```python
# Required by Vertex AI:
class AgentWrapper:
    def query(self, *, user_input: str):
        return self.agent.run_live(user_input=user_input)

# Cannot use:
def process_query(message):  # Wrong signature
def query(user_input):       # Missing keyword-only
```

**Why:**
- Vertex AI API expects specific signature
- Platform validates callable has `query()` method
- TypeError raised if signature doesn't match

#### Deployment Failures
```
Agent Created → Cloud Run Container Starting → Startup Failed
       ↓                      ↓                       ↓
    (200 OK)           (Platform logs)         (400 Bad Request)
                               ↓
                    "failed to start and cannot serve traffic"
```

**Common causes:**
- Module import errors (OTEL config issues)
- Missing dependencies in requirements.txt
- Syntax errors in agent.py
- Network timeouts during startup
- Platform service disruptions

**Debugging:**
- Check deployment output for LRO ID
- Look for OTEL_INIT messages
- Verify imports work locally
- Retry on network errors

### Best Practices for Managed Runtime

#### 1. Configuration Management
```python
# ✓ GOOD - Hardcode defaults, allow overrides
endpoint = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "https://otel-tenant1.portal26.in:4318"  # Default
)

# ✗ BAD - Rely on .env file
load_dotenv()  # Won't find .env in Cloud Run
```

#### 2. Error Handling
```python
# ✓ GOOD - Graceful degradation
try:
    setup_otel()
except Exception as e:
    print(f"OTEL setup failed: {e}")
    # Continue without OTEL

# ✗ BAD - Crash on OTEL failure
setup_otel()  # Unhandled exception crashes container
```

#### 3. Logging
```python
# ✓ GOOD - Structured logging
print(f"[OTEL_INIT] Traces configured: {endpoint}")

# ✗ BAD - Silent failures
provider = TracerProvider()  # Did it work? Unknown.
```

#### 4. Testing
```bash
# ✓ GOOD - Test locally first
python agent.py  # See OTEL_INIT messages

# ✗ BAD - Deploy without testing
python deploy.py  # Hope it works
```

### Workarounds for Limitations

#### Get Full Content Capture
**Option 1: Cloud Run Direct Deployment**
```
Deploy agent.py to Cloud Run (not via Vertex AI)
  ↓
Full control over environment variables
  ↓
Set OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
  ↓
Lose Vertex AI managed features (auto-scaling, built-in observability)
```

**Option 2: Custom Logging**
```python
def get_weather(city: str) -> dict:
    # Log manually before/after tool call
    logging.info(f"Tool called: get_weather({city})")
    result = {"status": "success", ...}
    logging.info(f"Tool result: {result}")
    return result
```

#### Debug Deployment Failures
```bash
# Check LRO (Long-Running Operation) status
gcloud alpha ai reasoning-engines describe [ID] \
  --region=us-central1

# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 --format=json

# Test agent locally
python -c "from agent import root_agent; print(root_agent.name)"
```

#### Handle Network Issues
```python
# Retry logic in deployment script
max_retries = 3
for attempt in range(max_retries):
    try:
        reasoning_engine = reasoning_engines.ReasoningEngine.create(...)
        break
    except TimeoutError:
        if attempt < max_retries - 1:
            print(f"Retry {attempt + 1}/{max_retries}...")
            time.sleep(30)
        else:
            raise
```
