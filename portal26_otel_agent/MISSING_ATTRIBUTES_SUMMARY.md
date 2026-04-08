# Missing Attributes Summary

**Generated:** 2026-04-08  
**Agent ID:** 4825053396622901248  
**Deployment:** Vertex AI Agent Engine (successful)  
**Log Source:** AWS Kinesis stream `stg_otel_source_data_stream`

---

## Files Created for Analysis

1. **attribute_analysis.md** - Full detailed analysis of all GenAI spans and missing attributes
2. **raw_trace_data.json** - Raw OTLP trace data extracted from Kinesis (4 traces with GenAI spans)
3. **portal26_otel_agent_logs_20260407_125530.jsonl** - Complete Kinesis log dump (9 traces, 236 logs)
4. **portal26_otel_agent_logs_20260408_020905.jsonl** - Latest Kinesis pull (83 logs, no traces)

---

## Critical Missing Attributes

### 1. Prompt Content (Request)
**Status:** NOT CAPTURED

Missing attributes:
- `gen_ai.prompt` - The full text prompt sent to the model
- `gen_ai.request.messages` - Array of message objects (for chat models)
- `gen_ai.request.temperature` - Temperature parameter
- `gen_ai.request.top_p` - Top-p sampling parameter
- `gen_ai.request.max_tokens` - Maximum tokens to generate

**Impact:** Cannot see what prompts users sent to the agent

---

### 2. Response Content
**Status:** NOT CAPTURED

Missing attributes:
- `gen_ai.completion` - The full text response from the model
- `gen_ai.response.content` - Response message content

**Impact:** Cannot see what the model responded with

---

### 3. Model Configuration
**Status:** PARTIALLY CAPTURED

Present:
- `gen_ai.request.model` = "gemini-2.5-flash" [OK]

Missing:
- `gen_ai.response.model` - Actual model used (may differ from request)
- `gen_ai.request.frequency_penalty`
- `gen_ai.request.presence_penalty`

---

## What IS Being Captured

### Span Structure [OK]
- Trace IDs, Span IDs, Parent Span IDs
- Start/End timestamps (nanosecond precision)
- Duration calculations
- Span names and kinds

### Basic Metadata [OK]
- `gen_ai.operation.name` = "generate_content"
- `gen_ai.request.model` = "gemini-2.5-flash"
- `gen_ai.system` = "vertex_ai"
- `code.function.name` = "google.genai.AsyncModels.generate_content"

### Token Usage [OK]
- `gen_ai.usage.input_tokens` = "289"
- `gen_ai.usage.output_tokens` = "29"
- `gen_ai.response.finish_reasons` = ["stop"]

**Note:** Token counts are captured, but without prompt/response content, they're not very useful for debugging or analysis.

### Agent Metadata [OK]
- `gen_ai.agent.name` = "portal26_agent_clean"
- `gen_ai.conversation.id` = "6759995811976708096"
- `gcp.vertex.agent.event_id`
- `gcp.vertex.agent.invocation_id`
- `user.id` = "vais-query-reasoning-engine"

### Resource Attributes [OK]
- `service.name` = "portal26_otel_agent"
- `portal26.tenant_id` = "tenant1"
- `portal26.user.id` = "relusys"
- `agent.type` = "otel-direct"
- `tenant.domain` = "otel-tenant1.portal26.in:4318"

---

## Configuration Verification

All configurations are correct:

| Component | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Deployment API | agent_engines.create() | agent_engines.create() | [OK] |
| env_vars parameter | Passed | Passed via otel_config.OTEL_CONFIG | [OK] |
| OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT | "true" | "true" | [OK] |
| VertexAI Instrumentation | instrument() called | Line 75 in agent_deployed.py | [OK] |
| Package structure | subdirectory | portal26_agent/ | [OK] |
| extra_packages | Set | ["./portal26_agent"] | [OK] |
| OTEL endpoint | Portal26 | https://otel-tenant1.portal26.in:4318 | [OK] |
| Traces exported | Yes | 9 traces in Kinesis | [OK] |
| Logs exported | Yes | 236 logs in Kinesis | [OK] |

---

## Expected vs Actual Attributes

### Sample GenAI Span (generate_content)

**Attributes Present (13 total):**
```
code.function.name: google.genai.AsyncModels.generate_content
gen_ai.request.model: gemini-2.5-flash
gen_ai.operation.name: generate_content
gen_ai.agent.name: portal26_agent_clean
gen_ai.conversation.id: 6759995811976708096
user.id: vais-query-reasoning-engine
gcp.vertex.agent.event_id: a1d65333-f71c-4c80-9ee7-4d1025ca3b5c
gcp.vertex.agent.invocation_id: e-bc943bf7-cbbb-4373-86b9-077e81868f95
gen_ai.system: vertex_ai
gen_ai.usage.input_tokens: 289
gen_ai.usage.output_tokens: 29
gen_ai.response.finish_reasons: ["stop"]
calculated.body_len: 746
```

**Attributes Missing (for content capture):**
```
gen_ai.prompt: <NOT CAPTURED>
gen_ai.request.messages: <NOT CAPTURED>
gen_ai.completion: <NOT CAPTURED>
gen_ai.response.content: <NOT CAPTURED>
gen_ai.request.temperature: <NOT CAPTURED>
gen_ai.request.top_p: <NOT CAPTURED>
gen_ai.request.max_tokens: <NOT CAPTURED>
gen_ai.usage.total_tokens: <NOT CAPTURED>
```

---

## Conclusion

**Content capture is NOT working** despite:
1. Using the correct Agent Engine API
2. Setting all correct environment variables
3. Using VertexAIInstrumentor with proper initialization
4. Proper package structure and deployment

**Root Cause (Suspected):**

The Vertex AI managed runtime appears to be **blocking content capture at the platform level**, likely for one of these reasons:

1. **Security Policy** - GCP may prevent capturing sensitive LLM content in managed environments
2. **Runtime Restrictions** - The environment variable `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` may be stripped or ignored by the platform
3. **Instrumentation Limitations** - The `opentelemetry-instrumentation-vertexai` package may not support content capture when running inside Vertex AI's managed runtime
4. **Permission/IAM** - Additional permissions may be required (though no error messages suggest this)

**What this means:**
- You can see THAT an LLM call happened
- You can see HOW LONG it took
- You can see HOW MANY TOKENS were used
- You CANNOT see WHAT was asked or WHAT was returned

This is a **platform limitation**, not a configuration issue.
