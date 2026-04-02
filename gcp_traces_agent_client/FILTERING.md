# Agent Filtering - gcp_traces_agent_client

## ✅ Filter by Agent ID Enabled

**By default, the client now fetches ONLY traces from `gcp_traces_agent`**, not all agents in the project.

---

## Configuration

### .env File

All configuration is in `.env`:

```env
# GCP Project ID
PROJECT_ID=agentic-ai-integration-490716

# Service name to filter traces (agent name)
SERVICE_NAME=gcp_traces_agent

# Default filter behavior (true = only gcp_traces_agent, false = all agents)
FILTER_BY_AGENT=true

# Default time range (hours)
DEFAULT_HOURS=1

# Default max results
DEFAULT_LIMIT=10
```

**To change which agent to filter by:**
```env
SERVICE_NAME=your_other_agent_name
```

---

## Usage

### 1. Fetch Only gcp_traces_agent Traces (Default)

```bash
python view_traces.py --limit 10
```

**Output:**
```
Filter: Only traces from gcp_traces_agent
Total traces found: 3
```

Only shows traces where `gen_ai.agent.name = gcp_traces_agent`

### 2. Fetch ALL Agent Traces

```bash
python view_traces.py --limit 10 --no-filter
```

**Output:**
```
Total traces found: 10  (includes all agents)
```

Shows traces from:
- gcp_traces_agent
- portal26_otel_agent
- Any other agents in the project

### 3. Export Filtered Traces

```bash
python view_traces.py --export traces/gcp_only.json --limit 20
```

Exports only gcp_traces_agent traces.

### 4. Export All Agent Traces

```bash
python view_traces.py --export traces/all_agents.json --limit 20 --no-filter
```

Exports traces from all agents.

---

## How Filtering Works

### Filter Logic

The client checks each trace's spans for the label:
```
gen_ai.agent.name = gcp_traces_agent
```

**If found:** Include trace  
**If not found:** Skip trace

### Example Trace Labels

**gcp_traces_agent trace:**
```json
{
  "labels": {
    "gen_ai.agent.name": "gcp_traces_agent",
    "gen_ai.agent.description": "Agent using GCP Cloud Trace"
  }
}
```
✅ **Included** (matches filter)

**Other agent trace:**
```json
{
  "labels": {
    "gen_ai.agent.name": "portal26_otel_agent"
  }
}
```
❌ **Excluded** (doesn't match filter)

---

## Benefits

### Before Filtering

**Problem:** Fetched traces from ALL agents in the project
- Mixed results from different agents
- Hard to find relevant traces
- Slower queries
- Larger exports

### After Filtering

**Solution:** Only gcp_traces_agent traces
- ✅ Clean, focused results
- ✅ Faster queries
- ✅ Smaller export files
- ✅ Easy to analyze

---

## Command Options

### view_traces.py

```bash
# Filtered by default
python view_traces.py --limit 10

# Include all agents
python view_traces.py --limit 10 --no-filter

# Export filtered
python view_traces.py --export traces/output.json --limit 20

# Export all agents
python view_traces.py --export traces/output.json --limit 20 --no-filter

# Get specific trace (no filtering applied)
python view_traces.py --trace-id <trace_id>
```

### fetch_traces.py

```bash
# Filtered by default (only gcp_traces_agent)
python fetch_traces.py
```

Auto-saves to `traces/traces_TIMESTAMP.json` with only gcp_traces_agent traces.

---

## Configuration Options

### Change Filter Target

Edit `.env` to filter by different agent:

```env
SERVICE_NAME=portal26_otel_agent
```

Now filters to only portal26_otel_agent traces.

### Disable Filtering by Default

Edit `.env`:

```env
FILTER_BY_AGENT=false
```

Now fetches all agents by default (can still use `--no-filter` flag).

### Change Defaults

Edit `.env`:

```env
DEFAULT_HOURS=2      # Look back 2 hours
DEFAULT_LIMIT=20     # Fetch up to 20 traces
```

---

## Comparison

| Mode | Command | Result |
|------|---------|--------|
| **Filtered (default)** | `python view_traces.py` | Only gcp_traces_agent |
| **All agents** | `python view_traces.py --no-filter` | All agents in project |
| **Export filtered** | `--export traces/out.json` | Only gcp_traces_agent |
| **Export all** | `--export traces/out.json --no-filter` | All agents |

---

## Multiple Agents in Project

**Agents in this project:**
1. gcp_traces_agent (filtered by default)
2. portal26_otel_agent
3. portal26_ngrok_agent
4. Other agents you may create

**Default behavior:** Only fetch gcp_traces_agent  
**To see all:** Use `--no-filter` flag

---

## Examples

### Example 1: Daily Export of gcp_traces_agent

```bash
python view_traces.py --export traces/daily_$(date +%Y%m%d).json --hours 24 --limit 100
```

Exports last 24 hours of gcp_traces_agent traces only.

### Example 2: Compare All Agents

```bash
python view_traces.py --export traces/all_agents.json --no-filter --hours 1 --limit 50
```

Exports traces from ALL agents for comparison.

### Example 3: Monitor Specific Agent

Edit `.env`:
```env
SERVICE_NAME=portal26_otel_agent
```

Then run:
```bash
python view_traces.py --limit 10
```

Now monitors portal26_otel_agent instead.

---

## Summary

✅ **Filtering enabled by default**  
✅ **Configuration in .env file**  
✅ **Only gcp_traces_agent traces fetched**  
✅ **Use --no-filter for all agents**  
✅ **Faster queries, cleaner results**

**No more mixed traces from multiple agents!**
