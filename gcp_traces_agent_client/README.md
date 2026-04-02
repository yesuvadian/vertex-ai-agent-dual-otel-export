# GCP Traces Agent Client

Client for fetching and viewing traces from Google Cloud Trace API.

---

## Installation

```bash
cd gcp_traces_agent_client
pip install -r requirements.txt
```

---

## Usage

### 1. View Recent Traces

Display recent traces in a hierarchical tree format:

```bash
python view_traces.py
```

**Options:**
```bash
python view_traces.py --hours 2 --limit 20
```
- `--hours`: How many hours back to search (default: 1)
- `--limit`: Maximum number of traces (default: 10)

**Output:**
```
Trace ID: abc123...
======================================================================
└─ agent_query [1200.45ms]
  Query: What is the weather in Tokyo?
  └─ llm_call [450.23ms]
    Model: gemini-2.5-flash
  └─ tool_execution [300.12ms]
    Tool: get_weather
    Input: city=tokyo
    Output: Sunny, 28C. Clear skies.
  └─ llm_response [400.10ms]
```

### 2. Get Specific Trace Details

View detailed information about a specific trace:

```bash
python view_traces.py --trace-id <trace_id>
```

Shows:
- Full span hierarchy
- All attributes for each span
- Timing and duration
- Parent-child relationships

### 3. Export Traces to JSON

Export traces to a JSON file:

```bash
python view_traces.py --export traces_export.json --hours 1 --limit 10
```

**Output file format:**
```json
[
  {
    "trace_id": "abc123...",
    "project_id": "agentic-ai-integration-490716",
    "spans": [
      {
        "span_id": "123",
        "name": "agent_query",
        "duration_ms": "1200.45ms",
        "attributes": {
          "query.text": "What is the weather in Tokyo?"
        }
      }
    ]
  }
]
```

### 4. Basic Trace Fetching

Simple script to fetch traces:

```bash
python fetch_traces.py
```

Fetches recent traces and saves them to a timestamped JSON file.

---

## What the Client Does

1. **Connects to Cloud Trace API** using google-cloud-trace
2. **Fetches traces** for project: agentic-ai-integration-490716
3. **Filters by service**: gcp_traces_agent
4. **Displays traces** in hierarchical tree format
5. **Shows attributes** like query text, model, tool calls, outputs
6. **Calculates durations** for each span
7. **Exports to JSON** for further analysis

---

## Trace Structure

**Root Span:** agent_query
- Attribute: query.text
- Attribute: query.timestamp

**Child Span:** llm_call
- Attribute: llm.model
- Attribute: llm.prompt
- Attribute: llm.response

**Child Span:** tool_execution
- Attribute: tool.name
- Attribute: tool.input.city
- Attribute: tool.output

**Child Span:** llm_response
- Attribute: llm.model
- Attribute: llm.final_response

---

## Examples

### Example 1: View Last Hour of Traces

```bash
python view_traces.py --hours 1 --limit 5
```

### Example 2: Export Last 2 Hours to JSON

```bash
python view_traces.py --export recent_traces.json --hours 2 --limit 20
```

### Example 3: Get Specific Trace Details

First, list traces to get a trace ID:
```bash
python view_traces.py --limit 1
```

Then get details:
```bash
python view_traces.py --trace-id <trace_id_from_above>
```

---

## Authentication

The client uses Google Cloud default credentials:

1. **If running locally:** 
   ```bash
   gcloud auth application-default login
   ```

2. **If running on GCP:** Uses service account automatically

3. **Environment variable:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   ```

---

## Configuration

Edit the constants at the top of the scripts:

```python
PROJECT_ID = "agentic-ai-integration-490716"
SERVICE_NAME = "gcp_traces_agent"
```

---

## Output Files

**Auto-generated files:**
- `traces_YYYYMMDD_HHMMSS.json` - From fetch_traces.py
- `traces_export.json` - From view_traces.py --export

---

## Troubleshooting

**Q: "Permission denied" error?**

A: Run `gcloud auth application-default login` to authenticate

**Q: No traces found?**

A: 
1. Make sure gcp_traces_agent was queried recently
2. Check time range (increase --hours)
3. Verify traces appear in Cloud Trace Console

**Q: Empty attributes?**

A: Traces may take 1-2 minutes to fully populate in Cloud Trace

---

## Related

- **Cloud Trace Console:** https://console.cloud.google.com/traces?project=agentic-ai-integration-490716
- **Agent Console:** https://console.cloud.google.com/vertex-ai/agents/agent-engines/8517380568462131200
- **Agent Code:** ../gcp_traces_agent/

---

## Summary

This client provides programmatic access to Cloud Trace data, allowing you to:
- Fetch traces via API
- Display in readable format
- Export to JSON
- Analyze trace data
- Build custom dashboards or integrations

All without needing to use the Cloud Trace Console UI!
