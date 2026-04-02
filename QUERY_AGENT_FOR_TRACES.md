# Query gcp_traces_agent to Generate Real Traces

## Agent Details

**Agent ID:** 8517380568462131200  
**Service Name:** gcp_traces_agent  
**Exporter:** Google Cloud Trace (native)

---

## How to Query the Agent

### Step 1: Open Agent in Console

**Direct link:**
https://console.cloud.google.com/vertex-ai/agents/agent-engines/8517380568462131200?project=agentic-ai-integration-490716

### Step 2: Send a Query

**Test queries:**
- "What is the weather in Tokyo?"
- "What is the current time in Bengaluru?"
- "What's the weather like in New York?"

**Wait:** 30-60 seconds for response

### Step 3: View Traces in Cloud Trace

**Open Cloud Trace:**
https://console.cloud.google.com/traces?project=agentic-ai-integration-490716

**Filter:**
- Service: `gcp_traces_agent`
- Time: Last 15 minutes

**You should see:**
- Agent query processing
- LLM calls to Gemini
- Tool executions (get_weather, get_current_time)
- Response generation
- Full timing and attributes

---

## Expected Trace Structure

When you query the agent, Cloud Trace will show:

```
Root Span: Agent Request
├── LLM Call (Planning)
├── Tool Execution: get_weather(city="tokyo")
│   └── Function Execution
├── LLM Call (Response Generation)
└── Final Response
```

**Attributes you'll see:**
- Service: gcp_traces_agent
- Query text
- Tool inputs/outputs
- LLM model: gemini-2.5-flash
- Response data
- Timing for each operation

---

## Troubleshooting

**Q: Span appears but no data?**

A: 
1. Click on the span to expand details
2. Check "Attributes" tab for data
3. Check "Timeline" for nested child spans
4. Wait 1-2 minutes for full trace data to appear

**Q: No new traces after querying agent?**

A:
1. Refresh Cloud Trace page
2. Expand time range to "Last 30 minutes"
3. Verify agent responded successfully
4. Check service filter is set to "gcp_traces_agent"

**Q: Trace looks incomplete?**

A: Agent Engine traces may take 2-3 minutes to fully appear in Cloud Trace. Refresh the page after waiting.

---

## Local Test Already Generated

**What was sent:**
- Root span: `agent_query`
- Child spans: `llm_call`, `tool_execution`, `llm_response`
- Full attributes and timing

**This proves the exporter is working!** Now query the deployed agent to see real agent traces.

---

## Compare with Portal26

**portal26_otel_agent** sends to Portal26:
- Agent ID: 7483734085236424704
- Dashboard: https://portal26.in
- Filter: tenant_id=tenant1, user_id=relusys

**gcp_traces_agent** sends to Cloud Trace:
- Agent ID: 8517380568462131200
- Dashboard: https://console.cloud.google.com/traces
- Filter: service=gcp_traces_agent

Both work! Different destinations, same telemetry capability.
