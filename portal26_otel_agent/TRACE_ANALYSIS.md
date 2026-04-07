# Portal26 OTEL Trace Analysis

## Query: "local time new york"
**Session ID**: 67599958119767088896  
**Trace ID**: `0000000000000000cefd10716a1122d1`  
**Agent**: portal26_agent_clean (ID: 3188531493748080640)  
**Service**: portal26_otel_agent  
**Tenant**: tenant1  
**User**: relusys

---

## Complete Trace Hierarchy

```
Trace: 0000000000000000cefd10716a1122d1
│
├─ [679829ab32d82cbc] POST /api/stream_reasoning_engine (root span)
│  │
│  ├─ [9a34b81634e53ac1] http receive (0.06ms)
│  │   └─ Body: 273 bytes
│  │
│  ├─ [c6e66c2e63602358] http send - response.start (0.07ms)
│  │   └─ Status: 200 OK, Body: 298 bytes
│  │
│  ├─ [f12e3226357ac2de] http send - response.body (0.04ms)
│  │   └─ Body: 276 bytes
│  │
│  └─ [c366b935272537a0] http send - response.body (0.03ms)
│      └─ Body: 276 bytes
│
├─ [dc74ddd9f6f249ae] Agent execution (parent)
│  │
│  └─ [1165f3a91b5440a8] call_llm (1219.85ms)
│      │   Model: gemini-2.5-flash
│      │   Input tokens: 106
│      │   Output tokens: 6
│      │   Reasoning tokens: 46
│      │   Session: 4778411975933689856
│      │   Invocation: e-602829e5-993f-413a-af31-af9f62f93089
│      │
│      ├─ [9af226ff09117061] generate_content gemini-2.5-flash (973.19ms)
│      │   └─ First LLM call - decides to use get_current_time tool
│      │
│      └─ [23cb64284bc077b0] execute_tool get_weather (0.37ms)
│          └─ Tool: get_weather (FunctionTool)
│              Call ID: adk-7302b108-2254-432f-9cf9-97bfac4b53db
│
└─ [4b2a457bda8dca29] Second LLM call (parent)
   │
   └─ [779e8a9d755186f8] generate_content gemini-2.5-flash (3776.50ms)
       └─ Second call with tool results
```

---

## Span Details

### 1. HTTP Layer (FastAPI Instrumentation)

**Span**: `POST /api/stream_reasoning_engine http receive`  
- **Span ID**: 9a34b81634e53ac1  
- **Parent**: 679829ab32d82cbc  
- **Duration**: 0.06ms  
- **Type**: http.request  
- **Body**: 273 bytes  

**Span**: `POST /api/stream_reasoning_engine http send`  
- **Span ID**: c6e66c2e63602358  
- **Parent**: 679829ab32d82cbc  
- **Duration**: 0.07ms  
- **Type**: http.response.start  
- **Status**: 200 OK  
- **Body**: 298 bytes  

**Span**: `POST /api/stream_reasoning_engine http send` (x2)  
- **Span IDs**: f12e3226357ac2de, c366b935272537a0  
- **Duration**: 0.04ms, 0.03ms  
- **Type**: http.response.body (streaming chunks)  

---

### 2. Agent Layer (GCP Vertex Agent)

**Span**: `call_llm`  
- **Span ID**: 1165f3a91b5440a8  
- **Parent**: dc74ddd9f6f249ae  
- **Duration**: 1219.85ms  
- **Model**: gemini-2.5-flash  
- **Session**: 4778411975933689856  
- **Invocation**: e-602829e5-993f-413a-af31-af9f62f93089  
- **Token Usage**:
  - Input: 106 tokens
  - Output: 6 tokens
  - Reasoning: 46 tokens
- **Finish reason**: stop  

**Span**: `execute_tool get_weather`  
- **Span ID**: 23cb64284bc077b0  
- **Parent**: 1165f3a91b5440a8  
- **Duration**: 0.37ms  
- **Tool**: get_weather (FunctionTool)  
- **Call ID**: adk-7302b108-2254-432f-9cf9-97bfac4b53db  
- **Description**: Call self as a function  

---

### 3. LLM Layer (Google GenAI Instrumentation)

**Span 1**: `generate_content gemini-2.5-flash`  
- **Span ID**: 9af226ff09117061  
- **Parent**: 1165f3a91b5440a8  
- **Duration**: 973.19ms  
- **Function**: google.genai.AsyncModels.generate_content  
- **Model**: gemini-2.5-flash  
- **Agent**: portal26_agent_clean  
- **Conversation**: 4778411975933689856  
- **Event**: b10a0014-740f-42f2-9cdb-e4c35f3f7f4c  
- **Token Usage**:
  - Input: 106 tokens
  - Output: 6 tokens
- **Finish reason**: stop  

**Span 2**: `generate_content gemini-2.5-flash`  
- **Span ID**: 779e8a9d755186f8  
- **Parent**: 4b2a457bda8dca29  
- **Duration**: 3776.50ms  
- **Function**: google.genai.AsyncModels.generate_content  
- **Model**: gemini-2.5-flash  
- **Agent**: portal26_agent_clean  
- **Conversation**: 4778411975933689856  

---

## Resource Attributes (All Spans)

```json
{
  "telemetry.sdk.language": "python",
  "telemetry.sdk.name": "opentelemetry",
  "telemetry.sdk.version": "1.38.0",
  "service.name": "portal26_otel_agent",
  "portal26.tenant_id": "tenant1",
  "portal26.user.id": "relusys",
  "agent.type": "otel-direct",
  "tenant.domain": "otel-tenant1.portal26.in:4318",
  "tenant.name": "tenant1",
  "tenant_name_suffixed": "tenant1_otel"
}
```

---

## Instrumentation Libraries

1. **FastAPI**: `opentelemetry.instrumentation.fastapi` v0.59b0
   - HTTP request/response spans
   - Schema: https://opentelemetry.io/schemas/1.11.0

2. **Google GenAI**: `opentelemetry.instrumentation.google_genai` v0.7b0
   - LLM generate_content spans
   - Client: google.genai v1.70.0
   - Package: opentelemetry-instrumentation-google-genai
   - Schema: https://opentelemetry.io/schemas/1.30.0

3. **GCP Vertex Agent**: `gcp.vertex.agent` v1.28.1
   - Agent execution spans
   - Tool execution spans
   - Schema: https://opentelemetry.io/schemas/1.36.0

---

## Trace Flow Summary

1. **Request received** (0.06ms) - User query arrives via HTTP
2. **Agent processing** (1219.85ms total):
   - First LLM call (973ms) - Analyzes query, decides to call get_current_time
   - Tool execution (0.37ms) - Executes get_weather (wrong tool initially)
   - Second LLM call (3776ms) - Processes tool result, generates final answer
3. **Response streaming** (0.14ms) - HTTP response chunks sent back

**Total query latency**: ~5 seconds (mostly LLM calls)

---

## Key Observations

✓ **Multi-tenant support**: tenant1/relusys properly tagged on all spans  
✓ **Parent-child relationships**: Proper span hierarchy maintained  
✓ **Tool execution traced**: get_weather tool call captured with timing  
✓ **Token usage tracked**: Input/output/reasoning tokens recorded  
✓ **Multiple LLM calls**: Agent made 2 calls (initial + tool result processing)  
✓ **Streaming responses**: HTTP chunked responses traced individually  
✓ **Session tracking**: Conversation ID maintained across spans  

---

## Data Pipeline

```
Agent (Vertex AI)
    ↓
OpenTelemetry SDK (Python 1.38.0)
    ↓
OTLPSpanExporter (HTTP)
    ↓
Portal26 OTEL Collector (otel-tenant1.portal26.in:4318/v1/traces)
    ↓
AWS Kinesis (stg_otel_source_data_stream, shardId-000000000006)
    ↓
Successfully retrieved and parsed ✓
```

---

## Files

- **Raw traces**: `all_traces.json` (42KB, 6 trace records)
- **Logs**: `agent_logs_20260407_104739.jsonl` (187 records: 6 traces, 180 logs)
- **Analysis**: This document
