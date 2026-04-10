# OpenTelemetry GenAI Attribute Analysis

**Analysis Date:** 2026-04-08
**Log File:** portal26_otel_agent_logs_20260407_125530.jsonl
**Total Traces:** 9

---

## GenAI Spans Found: 6

### Span #1: generate_content gemini-2.5-flash

- **Service:** portal26_otel_agent
- **Trace ID:** 0000000000000000b019256f57add742
- **Span ID:** 44928d27eb8df4f1
- **Duration:** 619.80ms

#### Attributes Present

```json
{
  "code.function.name": "google.genai.AsyncModels.generate_content",
  "gen_ai.request.model": "gemini-2.5-flash",
  "gen_ai.operation.name": "generate_content",
  "gen_ai.agent.name": "portal26_agent_clean",
  "gen_ai.conversation.id": "6759995811976708096",
  "user.id": "vais-query-reasoning-engine",
  "gcp.vertex.agent.event_id": "a1d65333-f71c-4c80-9ee7-4d1025ca3b5c",
  "gcp.vertex.agent.invocation_id": "e-bc943bf7-cbbb-4373-86b9-077e81868f95",
  "gen_ai.system": "vertex_ai",
  "gen_ai.usage.input_tokens": "289",
  "gen_ai.usage.output_tokens": "29",
  "gen_ai.response.finish_reasons": null,
  "calculated.body_len": "746"
}
```

**Total Attributes:** 13

#### Missing Attributes (Required for Content Capture)

**Basic Operation:**
- [YES] Present: gen_ai.operation.name, gen_ai.request.model, gen_ai.system

**Request Content (Content Capture):**
- [NO] Missing: gen_ai.prompt, gen_ai.request.messages, gen_ai.request.temperature, gen_ai.request.top_p, gen_ai.request.max_tokens

**Response Content (Content Capture):**
- [YES] Present: gen_ai.response.finish_reasons
- [NO] Missing: gen_ai.completion, gen_ai.response.content

**Token Usage:**
- [YES] Present: gen_ai.usage.input_tokens, gen_ai.usage.output_tokens
- [NO] Missing: gen_ai.usage.total_tokens

**Model Configuration:**
- [NO] Missing: gen_ai.request.frequency_penalty, gen_ai.request.presence_penalty, gen_ai.response.model

---

### Span #2: call_llm

- **Service:** portal26_otel_agent
- **Trace ID:** 0000000000000000b019256f57add742
- **Span ID:** 3f33446963e8009b
- **Duration:** 779.36ms

#### Attributes Present

```json
{
  "gen_ai.system": "gcp.vertex.agent",
  "gen_ai.request.model": "gemini-2.5-flash",
  "gcp.vertex.agent.invocation_id": "e-bc943bf7-cbbb-4373-86b9-077e81868f95",
  "gcp.vertex.agent.session_id": "6759995811976708096",
  "gcp.vertex.agent.event_id": "a1d65333-f71c-4c80-9ee7-4d1025ca3b5c",
  "gcp.vertex.agent.llm_request": "{}",
  "gcp.vertex.agent.llm_response": "{}",
  "gen_ai.usage.input_tokens": "289",
  "gen_ai.usage.output_tokens": "29",
  "gen_ai.response.finish_reasons": null,
  "calculated.body_len": "623"
}
```

**Total Attributes:** 11

#### Missing Attributes (Required for Content Capture)

**Basic Operation:**
- [YES] Present: gen_ai.request.model, gen_ai.system
- [NO] Missing: gen_ai.operation.name

**Request Content (Content Capture):**
- [NO] Missing: gen_ai.prompt, gen_ai.request.messages, gen_ai.request.temperature, gen_ai.request.top_p, gen_ai.request.max_tokens

**Response Content (Content Capture):**
- [YES] Present: gen_ai.response.finish_reasons
- [NO] Missing: gen_ai.completion, gen_ai.response.content

**Token Usage:**
- [YES] Present: gen_ai.usage.input_tokens, gen_ai.usage.output_tokens
- [NO] Missing: gen_ai.usage.total_tokens

**Model Configuration:**
- [NO] Missing: gen_ai.request.frequency_penalty, gen_ai.request.presence_penalty, gen_ai.response.model

---

### Span #3: invoke_agent portal26_agent_clean

- **Service:** portal26_otel_agent
- **Trace ID:** 0000000000000000b019256f57add742
- **Span ID:** 850f16b86bf897ff
- **Duration:** 2256.23ms

#### Attributes Present

```json
{
  "gen_ai.operation.name": "invoke_agent",
  "gen_ai.agent.description": "City assistant with Portal26 telemetry - Traces and Logs only",
  "gen_ai.agent.name": "portal26_agent_clean",
  "gen_ai.conversation.id": "6759995811976708096",
  "calculated.body_len": "437"
}
```

**Total Attributes:** 5

#### Missing Attributes (Required for Content Capture)

**Basic Operation:**
- [YES] Present: gen_ai.operation.name
- [NO] Missing: gen_ai.request.model, gen_ai.system

**Request Content (Content Capture):**
- [NO] Missing: gen_ai.prompt, gen_ai.request.messages, gen_ai.request.temperature, gen_ai.request.top_p, gen_ai.request.max_tokens

**Response Content (Content Capture):**
- [NO] Missing: gen_ai.completion, gen_ai.response.content, gen_ai.response.finish_reasons

**Token Usage:**
- [NO] Missing: gen_ai.usage.input_tokens, gen_ai.usage.output_tokens, gen_ai.usage.total_tokens

**Model Configuration:**
- [NO] Missing: gen_ai.request.frequency_penalty, gen_ai.request.presence_penalty, gen_ai.response.model

---

## Summary

### Content Capture Status: NOT WORKING

**Critical Missing Attributes:**

1. [MISSING] `gen_ai.prompt` / `gen_ai.request.messages` - No prompt content captured
2. [MISSING] `gen_ai.completion` / `gen_ai.response.content` - No response content captured
3. [MISSING] `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` - No token usage captured

**What IS Being Captured:**

- [OK] Span structure (trace_id, span_id, timestamps)
- [OK] Basic metadata (operation name, model name)
- [OK] Code context (function name)
- [OK] HTTP request/response spans

**Configuration Status:**

| Setting | Value | Status |
|---------|-------|--------|
| API | `agent_engines.create()` | [OK] Correct |
| env_vars | Passed via `otel_config.OTEL_CONFIG` | [OK] Correct |
| OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT | `true` | [OK] Set |
| VertexAIInstrumentor | `.instrument()` called | [OK] Correct |
| Package structure | `extra_packages=["./portal26_agent"]` | [OK] Correct |
| Traces exporting | Portal26 OTEL endpoint | [OK] Working |

### Conclusion

Despite all correct configurations, the Vertex AI Agent Engine runtime is **not capturing LLM prompt/response content**. This suggests the platform may be blocking content capture at a deeper level, regardless of the API used or environment variables set.

**Possible Causes:**
1. Vertex AI managed runtime may strip sensitive environment variables
2. Platform security policy may prevent content capture for compliance reasons
3. The `opentelemetry-instrumentation-vertexai` package may not support content capture in managed environments
4. Additional authentication or permissions may be required for content capture

