# Log and Trace Pattern Analysis Guide

## Overview

Tools to study and understand your Reasoning Engine's logging and tracing patterns:
- **How many logs** are generated per agent invocation?
- **What types of logs** are created?
- **How are traces structured** (spans, timing)?
- **What's the size distribution** of logs?

---

## Tools Provided

### 1. **log_pattern_analyzer.py** - Real-Time Log Collection
Captures logs from Pub/Sub and analyzes patterns.

### 2. **trace_visualizer.py** - Trace Timeline Visualization
Creates visual representation of individual traces.

### 3. **Generated Reports** - JSON Data
Detailed machine-readable analysis results.

---

## Quick Start

### Step 1: Run the Analyzer

```bash
cd analysis_tools
python log_pattern_analyzer.py
```

**What it does:**
- Connects to your Pub/Sub subscription
- Captures logs for 5 minutes (default)
- Groups logs by trace ID
- Analyzes patterns in real-time
- Generates comprehensive report

### Step 2: Trigger Your Agent

**While analyzer is running**, trigger your Reasoning Engine:

```python
from vertexai.preview import reasoning_engines

# Query your agent
response = reasoning_engine.query(
    input="What is the weather today?"
)
```

### Step 3: View Results

After 5 minutes (or Ctrl+C), you'll see:
- Total invocations captured
- Logs per invocation
- Severity distribution
- Log type distribution
- Timing analysis
- Size analysis

**Plus:** Detailed JSON report saved to file.

### Step 4: Visualize Specific Trace

```bash
python trace_visualizer.py log_analysis_report_20260420_143000.json 0
```

**Shows:**
- Timeline of all logs in trace
- Span breakdown
- Severity distribution
- Visual bars and charts

---

## What You'll Learn

### 1. Logs Per Invocation

**Question:** How many logs does one agent query generate?

**Answer from analysis:**
```
Example Output:
  Trace 1: 23 logs
  Trace 2: 18 logs
  Trace 3: 25 logs

  Average: 22 logs per invocation
```

**Insights:**
- Simple queries: 15-20 logs
- Complex queries: 30-50 logs
- Errors: 5-10 additional error logs

---

### 2. Trace Structure

**Question:** How are logs organized into spans?

**Example Output:**
```
Trace: abc123...
  Span 1 (main): 10 logs
  Span 2 (llm_call): 8 logs
  Span 3 (tool_use): 5 logs

  Total: 3 spans, 23 logs
```

**Insights:**
- Each LLM call creates a span
- Tool invocations create child spans
- Most logs in main span

---

### 3. Log Types

**Question:** What types of logs are generated?

**Example Output:**
```
Log Type Distribution:
  general:    12 logs (52%)
  request:    3 logs (13%)
  response:   3 logs (13%)
  trace:      4 logs (17%)
  error:      1 log (4%)
```

**Insights:**
- General logging (progress, state)
- Request/response pairs (LLM calls)
- Trace metadata
- Error logs (when issues occur)

---

### 4. Severity Levels

**Question:** What's the severity distribution?

**Example Output:**
```
Severity Distribution:
  INFO:       18 logs (78%)
  WARNING:    3 logs (13%)
  DEBUG:      2 logs (9%)
  ERROR:      0 logs (0%)
```

**Insights:**
- Mostly INFO (normal operation)
- Some WARNING (non-critical issues)
- DEBUG (detailed tracing)
- ERROR (failures)

---

### 5. Timing Patterns

**Question:** How long does an invocation take? When do logs appear?

**Example Output:**
```
Duration: 2.345 seconds

Timeline:
  0.000s: Request received (INFO)
  0.150s: LLM call started (INFO)
  1.850s: LLM response received (INFO)
  2.100s: Tool invocation (INFO)
  2.300s: Final response (INFO)
```

**Insights:**
- Most time in LLM calls (1.7s)
- Tool calls add 0.2s
- Overhead is ~0.4s

---

### 6. Log Size Patterns

**Question:** How big are the logs? Which ones are large?

**Example Output:**
```
Size Statistics:
  Min: 234 bytes (0.2 KB)
  Max: 15,234 bytes (14.9 KB)
  Avg: 2,456 bytes (2.4 KB)

Total per invocation: 56 KB

Large logs:
  - LLM response: 12 KB (full response text)
  - Trace metadata: 8 KB (spans, context)
  - Request: 3 KB (input query)
```

**Insights:**
- Small logs: Progress updates (<500 bytes)
- Medium logs: Requests/responses (2-5 KB)
- Large logs: Full LLM outputs (10-20 KB)

---

## Configuration

### Change Analysis Duration

```bash
# Analyze for 10 minutes
export ANALYSIS_DURATION=600
python log_pattern_analyzer.py
```

### Change Project/Subscription

Edit `.env` file:
```bash
GCP_PROJECT_ID=your-project
PUBSUB_SUBSCRIPTION=your-subscription
```

---

## Understanding the Output

### Real-Time Statistics (Every 30 seconds)

```
========================================
CURRENT STATISTICS
========================================
Total traces captured: 5
Time elapsed: 150.3s

Total logs: 112
Average logs per trace: 22.4

Severity Distribution:
  INFO        :    95 (84.8%)
  WARNING     :    12 (10.7%)
  DEBUG       :     5 (4.5%)

Log Type Distribution:
  general     :    58 (51.8%)
  request     :    15 (13.4%)
  response    :    15 (13.4%)
  trace       :    20 (17.9%)
  error       :     4 (3.6%)

Recent Traces (last 5):
  1. Trace: abc123def456...
     Engine: 6010661182900273152
     Logs: 23
     Spans: 3
     Duration: 2.45s
     Severities: {'INFO': 20, 'WARNING': 3}
```

---

### Final Report (JSON)

```json
{
  "analysis_duration_seconds": 300,
  "total_traces": 10,
  "aggregate_stats": {
    "total_logs": 224,
    "total_spans": 32,
    "avg_logs_per_invocation": 22.4,
    "avg_spans_per_invocation": 3.2,
    "duration_stats": {
      "min": 1.234,
      "max": 4.567,
      "avg": 2.345
    },
    "size_stats": {
      "min_bytes": 12340,
      "max_bytes": 78900,
      "avg_bytes": 45620
    }
  },
  "traces": [
    {
      "trace_id": "abc123...",
      "reasoning_engine_id": "6010661182900273152",
      "total_logs": 23,
      "unique_spans": 3,
      "duration_seconds": 2.345,
      "severity_distribution": {
        "INFO": 20,
        "WARNING": 3
      },
      "log_type_distribution": {
        "general": 12,
        "request": 3,
        "response": 3,
        "trace": 4,
        "error": 1
      },
      "timeline": [...]
    }
  ]
}
```

---

## Use Cases

### Use Case 1: Cost Estimation

**Goal:** Estimate Portal26 ingestion costs

**Process:**
1. Run analyzer for 1 hour
2. Capture 100 invocations
3. Calculate average log size: 45 KB
4. Estimate: 1000 invocations/day × 45 KB = 45 MB/day
5. Monthly: 45 MB × 30 = 1.35 GB/month

**Result:** Predictable cost estimation

---

### Use Case 2: Optimize Logging

**Goal:** Reduce log volume without losing visibility

**Process:**
1. Run analyzer
2. Identify large logs (e.g., full LLM responses)
3. Decide: Do we need full response in logs?
4. Modify agent to truncate or summarize
5. Re-run analyzer to verify reduction

**Result:** 30-50% log volume reduction

---

### Use Case 3: Debug Performance

**Goal:** Find why agent is slow

**Process:**
1. Run analyzer on slow queries
2. Review timeline in trace visualizer
3. Identify bottlenecks:
   - LLM call: 3.5s (too long)
   - Tool call: 0.1s (normal)
   - Overhead: 0.2s (normal)
4. Focus optimization on LLM calls

**Result:** Targeted performance improvement

---

### Use Case 4: Understand Errors

**Goal:** What happens when agent fails?

**Process:**
1. Trigger agent with invalid input
2. Analyzer captures error trace
3. Review error logs:
   - 5 normal logs
   - 3 error logs
   - Duration: 0.5s (failed fast)
4. Understand error pattern

**Result:** Better error handling

---

### Use Case 5: Multi-Destination Routing

**Goal:** Decide thresholds for routing

**Process:**
1. Run analyzer on various query types
2. Review size distribution:
   - Simple: 20 KB (→ Portal26)
   - Medium: 80 KB (→ Kinesis)
   - Complex: 200 KB (→ S3)
3. Set thresholds accordingly

**Result:** Optimal routing configuration

---

## Advanced Analysis

### Compare Different Query Types

**Run separate analyses:**

```bash
# Analyze simple queries (5 min)
python log_pattern_analyzer.py

# Trigger only simple queries
# Save report: simple_queries.json

# Analyze complex queries (5 min)
python log_pattern_analyzer.py

# Trigger only complex queries
# Save report: complex_queries.json

# Compare
python trace_visualizer.py simple_queries.json compare 0 1 2
python trace_visualizer.py complex_queries.json compare 0 1 2
```

**Insights:**
- Simple queries: 15 logs, 1.2s, 25 KB
- Complex queries: 45 logs, 4.5s, 120 KB
- Difference: 3x logs, 4x time, 5x size

---

### Analyze Error Patterns

**Filter for errors:**

Modify analyzer to track error-specific patterns:
```python
if log_entry.get('severity') in ['ERROR', 'CRITICAL']:
    # Special error tracking
    error_patterns.append(log_entry)
```

---

### Track Specific Operations

**Focus on specific log types:**

```python
# Track only LLM calls
if 'llm' in log_entry.get('textPayload', '').lower():
    llm_calls.append(log_entry)
```

---

## Troubleshooting

### No Traces Captured?

**Possible causes:**
1. No agent invocations during analysis
2. Wrong subscription ID
3. Logs not flowing to Pub/Sub

**Fix:**
- Verify subscription: `gcloud pubsub subscriptions pull SUBSCRIPTION --limit=1`
- Check agent is running
- Trigger test queries

---

### Analysis Too Slow?

**Possible causes:**
- Too many logs
- Analysis duration too long

**Fix:**
- Reduce `ANALYSIS_DURATION` to 60 seconds
- Filter for specific reasoning engine only

---

### Report File Too Large?

**Possible causes:**
- Many invocations captured
- Full timeline included

**Fix:**
- Reduce analysis duration
- Summarize timeline (don't include all logs)

---

## Sample Scenarios

### Scenario 1: New Agent Testing

**Goal:** Understand logging behavior of new agent

**Steps:**
1. Deploy new agent
2. Run analyzer for 10 minutes
3. Trigger 20 test queries
4. Review results:
   - Avg 18 logs/query
   - Avg 1.8s duration
   - Avg 32 KB size
5. Baseline established!

---

### Scenario 2: Production Monitoring

**Goal:** Monitor production agent patterns

**Steps:**
1. Run analyzer in background (continuous)
2. Capture 1000 invocations over 1 day
3. Analyze trends:
   - Peak hours: 50 logs/query (complex)
   - Off-hours: 20 logs/query (simple)
   - Error rate: 2% (4 errors per 200 queries)
4. Set alerts based on deviations

---

### Scenario 3: Cost Optimization

**Goal:** Reduce Portal26 costs

**Steps:**
1. Current state: 100 KB/invocation
2. Target: 50 KB/invocation
3. Run analyzer to identify large logs
4. Implement truncation
5. Re-run analyzer
6. Verify: Now 52 KB/invocation (48% reduction!)

---

## Summary

**Use these tools to:**

✅ Understand log generation patterns  
✅ Estimate costs accurately  
✅ Optimize log volume  
✅ Debug performance issues  
✅ Configure multi-destination routing  
✅ Monitor production behavior  

**Run analysis regularly to track changes over time!**

---

## Quick Reference

### Run analyzer:
```bash
python log_pattern_analyzer.py
```

### Visualize trace:
```bash
python trace_visualizer.py report.json 0
```

### Compare traces:
```bash
python trace_visualizer.py report.json compare 0 1 2
```

### Configure duration:
```bash
export ANALYSIS_DURATION=600  # 10 minutes
python log_pattern_analyzer.py
```

**Study your system - make data-driven decisions!**
