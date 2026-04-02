# GCP Traces Agent Client - Usage Guide

## ✅ Successfully Created!

Client for fetching traces from Google Cloud Trace API and saving them to local folder.

---

## Quick Start

### 1. View Recent Traces (Console Output)

```bash
cd gcp_traces_agent_client
python view_traces.py --limit 5
```

**Output:**
```
Trace ID: 0470fe6f...
======================================================================
invocation [5278.96ms]
  |- invoke_agent gcp_traces_agent [2869.04ms]
    |- call_llm [1864.57ms]
      |- generate_content gemini-2.5-flash [1863.84ms]
        |- execute_tool get_weather [0.52ms]
    |- call_llm [987.43ms]
```

### 2. Export Traces to JSON (Local Folder)

```bash
python view_traces.py --export traces/my_traces.json --limit 10
```

**Saves to:** `gcp_traces_agent_client/traces/my_traces.json`

### 3. Fetch and Auto-Save Traces

```bash
python fetch_traces.py
```

**Auto-saves to:** `gcp_traces_agent_client/traces/traces_YYYYMMDD_HHMMSS.json`

---

## Current Traces in Folder

**Location:** `gcp_traces_agent_client/traces/`

**Files created:**
- `gcp_traces_export.json` - Manual export (42KB)
- `traces_20260402_121052.json` - Auto-generated (41KB)

---

## What's Captured

### Trace Structure

```json
{
  "trace_id": "0470fe6f...",
  "project_id": "agentic-ai-integration-490716",
  "spans": [
    {
      "span_id": 16192661119187584351,
      "parent_span_id": 0,
      "name": "invocation",
      "duration_ms": "5278.96ms",
      "labels": {
        "gen_ai.agent.name": "gcp_traces_agent",
        "gen_ai.request.model": "gemini-2.5-flash",
        "gen_ai.usage.input_tokens": "110",
        "gen_ai.usage.output_tokens": "5"
      }
    }
  ]
}
```

### Labels Captured

**Agent info:**
- `gen_ai.agent.name`: gcp_traces_agent
- `gen_ai.agent.description`: Agent using GCP Cloud Trace

**LLM calls:**
- `gen_ai.request.model`: gemini-2.5-flash
- `gen_ai.usage.input_tokens`: Token counts
- `gen_ai.usage.output_tokens`: Token counts
- `gen_ai.response.finish_reasons`: stop

**Tool executions:**
- `tool.name`: get_weather
- `tool.input.city`: tokyo
- `tool.output`: Sunny, 28C. Clear skies.

**Custom labels from test:**
- `query.text`: What is the weather in Tokyo?
- `llm.prompt`: User prompt
- `llm.response`: LLM response
- `llm.final_response`: Final answer

---

## Command Options

### view_traces.py

**View recent traces:**
```bash
python view_traces.py --hours 2 --limit 10
```

**Get specific trace:**
```bash
python view_traces.py --trace-id <trace_id>
```

**Export to JSON:**
```bash
python view_traces.py --export traces/output.json --hours 1 --limit 20
```

**Options:**
- `--hours`: How many hours back (default: 1)
- `--limit`: Max traces to fetch (default: 10)
- `--trace-id`: Get specific trace details
- `--export`: Export to JSON file

### fetch_traces.py

```bash
python fetch_traces.py
```

Auto-fetches last hour of traces and saves to `traces/traces_TIMESTAMP.json`

---

## Examples

### Example 1: Export Last 2 Hours

```bash
python view_traces.py --export traces/last_2hours.json --hours 2 --limit 20
```

### Example 2: View Agent Query Details

```bash
# First, list traces
python view_traces.py --limit 1

# Copy trace ID from output, then:
python view_traces.py --trace-id 0470fe6f3ccf3ec1c1b86731f3c1cc0b
```

### Example 3: Continuous Monitoring

```bash
# Every 5 minutes, fetch and save new traces
while true; do
  python fetch_traces.py
  sleep 300
done
```

---

## Traces Folder Contents

```
gcp_traces_agent_client/
└── traces/
    ├── gcp_traces_export.json          (42KB - manual export)
    ├── traces_20260402_121052.json     (41KB - auto fetch)
    └── <more files as you run scripts>
```

**Files include:**
- Full trace hierarchy
- All span details
- Labels and attributes
- Timing information
- LLM token counts
- Tool execution data

---

## What the Data Shows

### Real Agent Traces

From `gcp_traces_agent` (our test agent):

**Trace shows:**
1. **Root span:** invocation (5278ms total)
2. **Agent execution:** invoke_agent gcp_traces_agent (2869ms)
3. **First LLM call:** Planning (1864ms)
   - Input: "What is the weather in Tokyo?"
   - Tool selected: get_weather
4. **Tool execution:** get_weather (0.52ms)
   - Input: city=tokyo
   - Output: "Sunny, 28C. Clear skies."
5. **Second LLM call:** Response generation (987ms)
   - Final response constructed

### Test Traces

From `test_full_trace.py`:

**Trace shows:**
- Span: test_gcp_trace_span
- Custom labels we added:
  - query.text: "What is the weather in Tokyo?"
  - test.type: local_verification
  - llm.model, tool.name, etc.

---

## Authentication

Uses Google Cloud default credentials.

**Setup:**
```bash
gcloud auth application-default login
```

---

## Integration Ideas

**Use these traces for:**

1. **Performance monitoring:** Track LLM response times
2. **Cost analysis:** Count tokens per request
3. **Debugging:** See full execution flow
4. **Analytics:** Build custom dashboards
5. **Audit logs:** Track all agent interactions
6. **Optimization:** Identify slow operations

---

## Summary

✅ **Client created and working**
✅ **Traces fetched from Cloud Trace API**
✅ **Saved to local `traces/` folder as JSON**
✅ **Captures full agent execution details**
✅ **Includes LLM calls, tools, timing, tokens**

**All traces are now stored locally for analysis!**
