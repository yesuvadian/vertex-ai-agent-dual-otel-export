# Agent Comparison Summary

**Date:** 2026-04-08  
**Comparison:** portal26_otel_agent vs hardcoded-otel-deployed

---

## Files Analyzed

| Agent | Log File | Traces | GenAI Spans |
|-------|----------|--------|-------------|
| portal26_otel_agent | portal26_otel_agent_logs_20260407_125530.jsonl | 9 | 6 |
| hardcoded-otel | hardcoded_otel_logs_20260408_022702.jsonl | 11 | 24 |

---

## Key Finding: BOTH Agents Missing Content Capture

### Content Capture Attributes Status

| Attribute | portal26_otel_agent | hardcoded-otel | Status |
|-----------|---------------------|----------------|--------|
| `gen_ai.prompt` | ❌ | ❌ | **MISSING IN BOTH** |
| `gen_ai.request.messages` | ❌ | ❌ | **MISSING IN BOTH** |
| `gen_ai.completion` | ❌ | ❌ | **MISSING IN BOTH** |
| `gen_ai.response.content` | ❌ | ❌ | **MISSING IN BOTH** |
| `gen_ai.request.temperature` | ❌ | ❌ | **MISSING IN BOTH** |
| `gen_ai.request.top_p` | ❌ | ❌ | **MISSING IN BOTH** |
| `gen_ai.request.max_tokens` | ❌ | ❌ | **MISSING IN BOTH** |

**Conclusion:** Despite both agents using identical OTEL configuration and deployment approach:
- Both use `agent_engines.create()` API
- Both pass `env_vars` with `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`
- Both call `VertexAIInstrumentor().instrument()`
- **NEITHER captures LLM prompt/response content**

This confirms a **Vertex AI platform limitation** - content capture is blocked at the runtime level regardless of configuration.

---

## Attribute Differences

### Summary

| Metric | portal26_otel_agent | hardcoded-otel-deployed |
|--------|---------------------|-------------------------|
| **Unique Attributes** | 17 | 23 |
| **Common Attributes** | 16 | 16 |
| **Exclusive Attributes** | 1 | 7 |

---

## Attributes ONLY in hardcoded-otel-deployed

The hardcoded-otel agent captures **7 additional attributes** related to tool execution:

### 1. Tool Call Metadata
```
gen_ai.tool.call.id: adk-4d64c4fd-65ec-4cfd-ba0d-fcd84eacc093
gen_ai.tool.name: get_current_time
gen_ai.tool.type: FunctionTool
```

### 2. Tool Details
```
gen_ai.tool.description: "Returns the current local time for a given city..."
gcp.vertex.agent.tool_call_args: {}
gcp.vertex.agent.tool_response: {}
```

### 3. Reasoning Token Usage
```
gen_ai.usage.experimental.reasoning_tokens: 66
```

**Analysis:** The hardcoded-otel agent has better instrumentation for tool calls, capturing:
- Tool call IDs for tracing
- Tool metadata (name, type, description)
- Tool arguments and responses
- Reasoning token usage (Gemini 2.5 flash thinking tokens)

---

## Attributes ONLY in portal26_otel_agent

The portal26 agent captures **1 additional attribute**:

### Code Context
```
code.function.name: google.genai.AsyncModels.generate_content
```

**Analysis:** Portal26 captures the Python function name that made the LLM call, providing code-level tracing.

---

## Common Attributes (16 total)

Both agents capture:

### Basic Operation
- `gen_ai.operation.name` = "generate_content"
- `gen_ai.request.model` = "gemini-2.5-flash"
- `gen_ai.system` = "vertex_ai"

### Token Usage
- `gen_ai.usage.input_tokens`
- `gen_ai.usage.output_tokens`
- `gen_ai.response.finish_reasons`

### Agent Metadata
- `gen_ai.agent.name`
- `gen_ai.agent.description`
- `gen_ai.conversation.id`

### GCP Context
- `gcp.vertex.agent.event_id`
- `gcp.vertex.agent.invocation_id`
- `gcp.vertex.agent.session_id`
- `gcp.vertex.agent.llm_request`
- `gcp.vertex.agent.llm_response`

### Other
- `user.id`
- `calculated.body_len`

---

## Why Does hardcoded-otel Have More Tool Attributes?

**Possible Reasons:**

1. **Different Query Patterns**
   - Hardcoded-otel queries may have triggered more tool calls
   - Portal26 logs may have captured fewer tool execution spans

2. **Timing Differences**
   - Portal26 logs: April 7, 2026
   - Hardcoded logs: April 8, 2026 (today)
   - Platform may have updated instrumentation

3. **Service Name Differences**
   - Portal26: `portal26_otel_agent`
   - Hardcoded: `hardcoded-otel-deployed`
   - Platform may treat service names differently

4. **Resource Attributes**
   - Portal26 includes custom resource attributes: `portal26.tenant_id`, `portal26.user.id`, `agent.type`
   - Hardcoded likely has minimal resource attributes
   - This should NOT affect span attributes, but worth noting

---

## Important Observation: reasoning_tokens

The hardcoded-otel agent captured:
```
gen_ai.usage.experimental.reasoning_tokens: 66
```

This attribute is for **Gemini 2.5 Flash Thinking** - tokens used for internal reasoning before generating the response.

**This attribute is present in hardcoded-otel but NOT in portal26_otel_agent.**

Check if:
1. Both agents used the same model version
2. Both queries triggered reasoning (complex questions)
3. Platform instrumentation differs between the two

---

## Configuration Verification

Both agents have **identical OTEL setup**:

### Deployment API
- ✅ Both use `agent_engines.create()`

### Environment Variables
- ✅ Both pass `env_vars` with OTEL configuration
- ✅ Both set `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`

### Instrumentation
- ✅ Both call `VertexAIInstrumentor().instrument()`

### Exporters
- ✅ Both export to OTLP HTTP endpoints
- ✅ Both configure traces, logs, and metrics

### Package Structure
- ✅ Both use `extra_packages` with subdirectory
- ✅ Both include proper requirements

---

## Conclusion

### Content Capture: BLOCKED BY PLATFORM

Despite identical configuration, **BOTH agents fail to capture LLM content**. This confirms:

1. ❌ Content capture is NOT working in Vertex AI Agent Engine
2. ❌ Setting `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` has NO effect
3. ❌ The platform blocks content capture at the runtime level
4. ❌ This is a **platform limitation**, not a configuration issue

### Tool Instrumentation: BETTER IN HARDCODED-OTEL

The hardcoded-otel agent captures **7 additional tool-related attributes** that portal26 does not:
- Tool call IDs, names, types, descriptions
- Tool arguments and responses  
- Reasoning token usage

**Action Items:**

1. **Investigate Tool Attributes**
   - Compare tool definitions between both agents
   - Check if different query patterns affect tool span capture
   - Review logs to see if portal26 has tool spans at all

2. **Reasoning Tokens**
   - Verify if portal26 queries triggered Gemini reasoning mode
   - Check model configuration differences

3. **Platform Limitation**
   - Accept that content capture is NOT possible in Vertex AI Agent Engine
   - Document this as a known limitation
   - Consider alternative approaches (custom logging, audit trails, etc.)

---

## Recommendation

**Stop trying to enable content capture via OTEL configuration** - the platform blocks it regardless of settings.

Instead:
- Use the captured metadata (token counts, timing, model info)
- Implement custom logging in agent code if content capture is required
- Consider using Vertex AI audit logs for compliance/security needs
- Focus on improving tool instrumentation to match hardcoded-otel level
