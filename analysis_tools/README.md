# Log and Trace Pattern Analysis Tools

## Purpose

Study your Reasoning Engine's logging and tracing behavior to answer:
- **How many logs** per agent invocation?
- **What types of logs** are generated?
- **How are traces structured?**
- **What's the size distribution?**
- **Where are the performance bottlenecks?**

**Use these insights to:**
- Estimate costs accurately
- Optimize logging
- Configure multi-destination routing
- Debug performance issues
- Monitor production behavior

---

## Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `log_pattern_analyzer.py` | Capture and analyze logs in real-time | `python log_pattern_analyzer.py` |
| `trace_visualizer.py` | Visualize trace timelines | `python trace_visualizer.py report.json 0` |
| `test_agent_invocations.py` | Generate test data | `python test_agent_invocations.py --engine ID --count 10` |

---

## Quick Start (5 Minutes)

### Step 1: Start the Analyzer

```bash
cd analysis_tools
python log_pattern_analyzer.py
```

**The analyzer will:**
- Connect to your Pub/Sub subscription
- Capture logs for 5 minutes
- Display statistics every 30 seconds
- Generate detailed JSON report at end

### Step 2: Generate Test Data

**In another terminal:**

```bash
cd analysis_tools
python test_agent_invocations.py \
  --engine projects/961756870884/locations/us-central1/reasoningEngines/6010661182900273152 \
  --count 10 \
  --delay 5
```

**This will:**
- Trigger 10 agent invocations
- Mix simple, medium, and complex queries
- Space them 5 seconds apart
- Generate logs that the analyzer captures

### Step 3: View Results

After 5 minutes (or Ctrl+C), the analyzer shows:

```
========================================
FINAL ANALYSIS REPORT
========================================
Analysis Duration: 300s
Total Traces: 10

AGGREGATE STATISTICS:
  Total Invocations (Traces): 10
  Total Logs: 224
  Total Unique Spans: 32
  Avg Logs per Invocation: 22.4
  Avg Spans per Invocation: 3.2

DURATION STATISTICS:
  Min: 1.23s
  Max: 4.56s
  Avg: 2.35s

SIZE STATISTICS:
  Min: 12340 bytes (12.1 KB)
  Max: 78900 bytes (77.1 KB)
  Avg: 45620 bytes (44.6 KB)
```

**Plus:** Detailed JSON report saved!

### Step 4: Visualize a Trace

```bash
python trace_visualizer.py log_analysis_report_20260420_143000.json 0
```

**Shows:**
```
TRACE VISUALIZATION
===================
Trace ID: abc123def456...
Duration: 2.345s
Total Logs: 23
Unique Spans: 3

TIMELINE (chronological order)
   # |         Time |    Delta | Severity   | Type         | Span ID
--------------------------------------------------------------------------------
   1 |      0.000s |  +0.000s | ℹ INFO     | general      | span-main-001
   2 |      0.150s |  +0.150s | ℹ INFO     | request      | span-llm-002
   3 |      1.850s |  +1.850s | ℹ INFO     | response     | span-llm-002
  ...
```

---

## What You'll Discover

### 1. Logs Per Invocation Pattern

**Example Results:**
```
Simple query:   15-20 logs
Medium query:   20-30 logs
Complex query:  30-50 logs
Error case:     +5-10 error logs
```

**Insight:** Budget 25 logs/invocation on average

---

### 2. Trace Structure

**Example:**
```
Trace abc123:
  └─ Span 1 (main): 10 logs
      ├─ Span 2 (llm_call): 8 logs
      └─ Span 3 (tool_use): 5 logs

Total: 3 spans, 23 logs
```

**Insight:** Nested spans for LLM calls and tools

---

### 3. Log Size Distribution

**Example:**
```
Small logs (<1 KB):     Progress updates (60%)
Medium logs (1-5 KB):   Requests/metadata (30%)
Large logs (>5 KB):     Full responses (10%)

Average: 2.4 KB per log
Per invocation: 55 KB total
```

**Insight:** 
- Portal26 threshold: <100 KB (most invocations)
- Kinesis threshold: 100KB-1MB (complex queries)
- S3 threshold: >1MB (rare, multi-step traces)

---

### 4. Timing Patterns

**Example Timeline:**
```
0.000s: Request received
0.150s: LLM call started
1.850s: LLM response (1.7s - bottleneck!)
2.100s: Tool invocation (0.25s)
2.345s: Final response
```

**Insight:** 
- Total: 2.35s
- LLM time: 1.7s (72%)
- Tool time: 0.25s (11%)
- Overhead: 0.4s (17%)

---

### 5. Severity Distribution

**Example:**
```
INFO:      85%  (Normal operations)
WARNING:   10%  (Non-critical issues)
DEBUG:     4%   (Detailed tracing)
ERROR:     1%   (Failures)
```

**Insight:** Mostly informational, low error rate

---

## Use Cases

### Use Case 1: Cost Estimation

**Steps:**
1. Run analyzer for 1 hour
2. Capture 100 invocations
3. Calculate: 100 invocations × 55 KB = 5.5 MB/hour
4. Daily: 5.5 MB × 24 = 132 MB/day
5. Monthly: 132 MB × 30 = 3.96 GB/month

**Result:** Accurate Portal26 ingestion estimate

---

### Use Case 2: Routing Configuration

**Steps:**
1. Analyze log sizes
2. Results:
   - 80% under 60 KB → Portal26
   - 15% between 60-200 KB → Kinesis
   - 5% over 200 KB → S3
3. Set thresholds accordingly

**Configuration:**
```bash
SMALL_LOG_THRESHOLD=61440    # 60 KB
LARGE_LOG_THRESHOLD=204800   # 200 KB
```

---

### Use Case 3: Performance Optimization

**Steps:**
1. Identify slow invocations (>5s)
2. Review timeline
3. Find bottleneck: LLM calls taking 4s
4. Optimize: Use caching or smaller model
5. Re-analyze: Now 2s average!

**Result:** 60% performance improvement

---

### Use Case 4: Error Analysis

**Steps:**
1. Trigger errors intentionally
2. Analyzer captures error traces
3. Review pattern:
   - 5 normal logs
   - 3 error logs (stack traces)
   - Failed in 0.5s
4. Understand error behavior

**Result:** Better error handling

---

## Configuration

### Analysis Duration

```bash
# Default: 5 minutes (300s)
export ANALYSIS_DURATION=300
python log_pattern_analyzer.py

# 10 minutes for more data
export ANALYSIS_DURATION=600
python log_pattern_analyzer.py

# 1 minute for quick test
export ANALYSIS_DURATION=60
python log_pattern_analyzer.py
```

### Project/Subscription

Edit `.env` file:
```bash
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=all-customers-logs-sub
```

---

## Advanced Usage

### Compare Different Query Types

**Analyze simple queries:**
```bash
# Terminal 1: Analyzer
python log_pattern_analyzer.py

# Terminal 2: Trigger only simple queries
python test_agent_invocations.py --engine ID --count 10 --complexity simple
```

**Analyze complex queries:**
```bash
# Restart analyzer
python log_pattern_analyzer.py

# Trigger only complex queries
python test_agent_invocations.py --engine ID --count 10 --complexity complex
```

**Compare results:**
- Simple: 18 logs, 1.5s, 35 KB
- Complex: 42 logs, 4.2s, 110 KB
- Ratio: 2.3x logs, 2.8x time, 3.1x size

---

### Multiple Traces Side-by-Side

```bash
# Compare traces 0, 1, and 2
python trace_visualizer.py report.json compare 0 1 2
```

**Output:**
```
TRACE COMPARISON
=========================
Metric                   | Trace 1        | Trace 2        | Trace 3
---------------------------------------------------------------------------
Total Logs               |     18         |     23         |     42
Unique Spans             |      2         |      3         |      5
Duration (s)             |   1.234        |   2.345        |   4.567
Total Size (KB)          |   32.5         |   55.3         |  110.8
```

---

## Output Files

### JSON Report

**Location:** `log_analysis_report_YYYYMMDD_HHMMSS.json`

**Structure:**
```json
{
  "analysis_duration_seconds": 300,
  "total_traces": 10,
  "aggregate_stats": {
    "total_logs": 224,
    "avg_logs_per_invocation": 22.4,
    ...
  },
  "traces": [
    {
      "trace_id": "...",
      "total_logs": 23,
      "timeline": [...],
      ...
    }
  ]
}
```

**Use for:**
- Machine processing
- Long-term storage
- Trend analysis
- Custom visualization

---

## Troubleshooting

### No Traces Captured?

**Check:**
1. Is Pub/Sub subscription correct?
   ```bash
   gcloud pubsub subscriptions pull vertex-telemetry-subscription --limit=1
   ```

2. Are logs flowing?
   ```bash
   gcloud logging read "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\"" --limit=5
   ```

3. Did you trigger agent invocations?
   ```bash
   python test_agent_invocations.py --engine ID --count 5
   ```

---

### Analyzer Crashes?

**Possible causes:**
- Out of memory (too many logs)
- Network issues

**Fix:**
- Reduce ANALYSIS_DURATION
- Increase system memory
- Check internet connection

---

### Report File Too Large?

**Solution:**
- Reduce analysis duration
- Filter for specific reasoning engine
- Capture fewer invocations

---

## Requirements

```bash
pip install google-cloud-pubsub python-dotenv vertexai
```

Or use existing environment:
```bash
cd monitoring_setup
# (Already has all dependencies)
```

---

## Example Workflow

### Day 1: Baseline

```bash
# Capture baseline patterns
python log_pattern_analyzer.py
python test_agent_invocations.py --engine ID --count 20

# Results:
# - 22 logs/invocation
# - 2.3s average
# - 48 KB average
```

### Day 7: After Optimization

```bash
# Re-analyze after optimization
python log_pattern_analyzer.py
python test_agent_invocations.py --engine ID --count 20

# Results:
# - 15 logs/invocation (32% reduction!)
# - 1.8s average (22% faster!)
# - 32 KB average (33% smaller!)
```

**Compare reports to verify improvements!**

---

## Tips

### 1. Run During Different Times

**Morning (simple queries):**
- 18 logs/invocation
- 1.5s duration

**Afternoon (complex queries):**
- 35 logs/invocation
- 3.2s duration

**Insight:** Adjust routing based on time of day

---

### 2. Analyze Per Customer

**Filter by customer project:**
```python
# In log_pattern_analyzer.py, add filter:
if resource_labels.get('project_id') != 'customer-a-project':
    return  # Skip other customers
```

**Result:** Per-customer patterns

---

### 3. Focus on Errors

**Trigger errors:**
```python
# test_agent_invocations.py with invalid queries
TEST_QUERIES = {
    'error': [
        "",  # Empty query
        "x" * 10000,  # Too long
        "🔥" * 100,  # Special chars
    ]
}
```

**Result:** Understand error logging patterns

---

## Summary

**These tools help you:**

✅ **Understand** your system's logging behavior  
✅ **Estimate** costs accurately  
✅ **Optimize** log volume and routing  
✅ **Debug** performance issues  
✅ **Monitor** production patterns  
✅ **Make** data-driven decisions  

**Start analyzing now:**
```bash
python log_pattern_analyzer.py
```

**Study your system - optimize with confidence!**
