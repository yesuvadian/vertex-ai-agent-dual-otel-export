# Real Data Validation Guide

## Let's Test with Your Actual Reasoning Engine

We'll capture real logs from your agent and analyze the actual patterns.

---

## Step-by-Step Validation

### Step 1: Prepare Environment (1 minute)

```bash
cd C:\Yesu\ai_agent_projectgcp\analysis_tools

# Check if dependencies are installed
python -c "import google.cloud.pubsub_v1; print('✓ Pub/Sub OK')"
python -c "import vertexai; print('✓ Vertex AI OK')"
python -c "from dotenv import load_dotenv; print('✓ dotenv OK')"
```

**If any fail:**
```bash
pip install google-cloud-pubsub vertexai python-dotenv
```

---

### Step 2: Configure (30 seconds)

**Create or edit `.env` file:**

```bash
# Create .env file
cat > .env << EOF
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription
ANALYSIS_DURATION=300
EOF
```

**Or copy from parent:**
```bash
cp ../monitoring_setup/.env .env
```

---

### Step 3: Start the Analyzer (Now!)

**Open Terminal 1:**

```bash
cd C:\Yesu\ai_agent_projectgcp\analysis_tools
python log_pattern_analyzer.py
```

**You should see:**
```
================================================================================
LOG AND TRACE PATTERN ANALYZER
================================================================================
GCP Project:     agentic-ai-integration-490716
Subscription:    vertex-telemetry-subscription
Analysis Duration: 300s

Starting analysis...
Trigger your Reasoning Engine agent to generate logs!

Press Ctrl+C to stop early and see results.
================================================================================
```

**Leave this running!**

---

### Step 4: Trigger Your Real Agent

**Option A: Using Test Script (Easiest)**

**Open Terminal 2:**

```bash
cd C:\Yesu\ai_agent_projectgcp\analysis_tools

# Use your actual Reasoning Engine ID
python test_agent_invocations.py \
  --engine projects/961756870884/locations/us-central1/reasoningEngines/6010661182900273152 \
  --count 5 \
  --delay 10 \
  --complexity mixed
```

**This will trigger 5 invocations with 10 seconds between each.**

---

**Option B: Manual Testing (More Control)**

**Create a test file `manual_test.py`:**

```python
from vertexai.preview import reasoning_engines
import vertexai
import time

# Initialize
vertexai.init(
    project="agentic-ai-integration-490716",
    location="us-central1"
)

# Your actual engine
reasoning_engine = reasoning_engines.ReasoningEngine(
    "projects/961756870884/locations/us-central1/reasoningEngines/6010661182900273152"
)

# Test queries
queries = [
    "Hello, how are you?",
    "What is the weather today?",
    "Explain what a Reasoning Engine is.",
    "Tell me about cloud computing.",
    "What are the benefits of AI?"
]

print("Starting manual tests...")
for i, query in enumerate(queries, 1):
    print(f"\n[{i}/{len(queries)}] Query: {query}")
    try:
        response = reasoning_engine.query(input=query)
        print(f"✓ Response: {str(response)[:100]}...")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    if i < len(queries):
        print("Waiting 10 seconds...")
        time.sleep(10)

print("\nDone! Check the analyzer output.")
```

**Run it:**
```bash
python manual_test.py
```

---

**Option C: Use Your Existing Agent Code**

If you have existing code that uses your agent, just run it!

---

### Step 5: Watch the Analyzer (Real-Time)

**Back in Terminal 1, you'll see updates every 30 seconds:**

```
================================================================================
CURRENT STATISTICS
================================================================================
Total traces captured: 3
Time elapsed: 90.5s

Total logs: 67
Average logs per trace: 22.3

Severity Distribution:
  INFO        :    58 (86.6%)
  WARNING     :     7 (10.4%)
  DEBUG       :     2 (3.0%)

Log Type Distribution:
  general     :    35 (52.2%)
  request     :     9 (13.4%)
  response    :     9 (13.4%)
  trace       :    12 (17.9%)
  error       :     2 (3.0%)

Recent Traces (last 3):

  1. Trace: a1b2c3d4e5f6...
     Engine: 6010661182900273152
     Logs: 23
     Spans: 3
     Duration: 2.45s
     Severities: {'INFO': 20, 'WARNING': 3}

  2. Trace: f6e5d4c3b2a1...
     Engine: 6010661182900273152
     Logs: 22
     Spans: 2
     Duration: 1.89s
     Severities: {'INFO': 19, 'WARNING': 2, 'DEBUG': 1}

  3. Trace: 1a2b3c4d5e6f...
     Engine: 6010661182900273152
     Logs: 22
     Spans: 3
     Duration: 2.67s
     Severities: {'INFO': 19, 'WARNING': 3}

================================================================================
```

**This is your real data!**

---

### Step 6: Wait for Final Report (5 minutes or Ctrl+C)

After 5 minutes (or when you press Ctrl+C), you'll see:

```
================================================================================
FINAL ANALYSIS REPORT
================================================================================
Analysis Duration: 300s
Total Traces: 5

AGGREGATE STATISTICS:
  Total Invocations (Traces): 5
  Total Logs: 112
  Total Unique Spans: 15
  Avg Logs per Invocation: 22.4
  Avg Spans per Invocation: 3.0

DURATION STATISTICS:
  Min: 1.89s
  Max: 3.45s
  Avg: 2.45s

SIZE STATISTICS:
  Min: 34567 bytes (33.8 KB)
  Max: 67890 bytes (66.3 KB)
  Avg: 48234 bytes (47.1 KB)

================================================================================
DETAILED TRACE EXAMPLES:
================================================================================

Example 1:
  Trace ID: a1b2c3d4e5f6789...
  Reasoning Engine: 6010661182900273152
  Customer Project: agentic-ai-integration-490716
  Total Logs: 23
  Unique Spans: 3
  Duration: 2.45s
  Total Size: 52341 bytes (51.1 KB)

  Severity Distribution:
    INFO: 20
    WARNING: 3

  Log Type Distribution:
    general: 12
    request: 3
    response: 3
    trace: 4
    error: 1

  Logs per Span:
    Span abc123...: 10 logs
    Span def456...: 8 logs
    Span ghi789...: 5 logs

  Timeline (first 5 logs):
    2026-04-20T14:30:00.000Z | INFO     | general
    2026-04-20T14:30:00.150Z | INFO     | request
    2026-04-20T14:30:01.850Z | INFO     | response
    2026-04-20T14:30:02.100Z | INFO     | general
    2026-04-20T14:30:02.450Z | INFO     | general


Detailed report saved to: log_analysis_report_20260420_143000.json
================================================================================
```

**This is your actual pattern!**

---

### Step 7: Visualize a Specific Trace

```bash
# Use the report file that was just created
python trace_visualizer.py log_analysis_report_20260420_143000.json 0
```

**You'll see:**

```
====================================================================================================
TRACE VISUALIZATION
====================================================================================================
Trace ID: a1b2c3d4e5f6789abcdef
Reasoning Engine: 6010661182900273152
Duration: 2.450s
Total Logs: 23
Unique Spans: 3

Severity Distribution:
  INFO         | ████████████████████████████████████████████████ 20
  WARNING      | ███████ 3

Log Type Distribution:
  general      | ████████████████████████████ 12
  request      | ███████ 3
  response     | ███████ 3
  trace        | █████████ 4
  error        | ██ 1

====================================================================================================
TIMELINE (chronological order)
====================================================================================================
   # |         Time |    Delta | Severity   | Type         | Span ID
----------------------------------------------------------------------------------------------------
   1 |      0.000s |  +0.000s | ℹ INFO     | general      | span-main-abc123
   2 |      0.150s |  +0.150s | ℹ INFO     | request      | span-llm-def456
   3 |      1.850s |  +1.850s | ℹ INFO     | response     | span-llm-def456
   4 |      2.100s |  +2.100s | ℹ INFO     | general      | span-tool-ghi789
   5 |      2.250s |  +2.250s | ℹ INFO     | general      | span-tool-ghi789
   ...
  23 |      2.450s |  +2.450s | ℹ INFO     | general      | span-main-abc123
====================================================================================================

SPAN BREAKDOWN:
----------------------------------------------------------------------------------------------------
                 Span ID                  |    Logs    |  Percentage
----------------------------------------------------------------------------------------------------
span-main-abc123...                       |     10     |  43.5% ██████████████████████
span-llm-def456...                        |      8     |  34.8% █████████████████
span-tool-ghi789...                       |      5     |  21.7% ███████████
====================================================================================================
```

**This is your actual trace structure!**

---

### Step 8: Compare Multiple Invocations

```bash
# Compare first 3 traces
python trace_visualizer.py log_analysis_report_20260420_143000.json compare 0 1 2
```

**You'll see side-by-side comparison of your real traces!**

---

## What You'll Learn from Real Data

### 1. Your Actual Log Volume

**Expected discovery:**
```
Your agent generates:
- Simple query: X logs
- Complex query: Y logs
- Average: Z logs per invocation

For 1000 invocations/day:
- Total logs: Z × 1000 = ??? logs/day
- Total size: ??? KB/day × 30 = ??? GB/month
```

### 2. Your Actual Trace Pattern

**Expected discovery:**
```
Your agent creates:
- X spans per trace
- Main span: Y logs
- LLM span: Z logs
- Tool span: W logs
```

### 3. Your Actual Performance

**Expected discovery:**
```
Average invocation time: X.XXs
- LLM time: Y.YYs (ZZ%)
- Tool time: W.WWs (ZZ%)
- Overhead: V.VVs (ZZ%)
```

### 4. Your Actual Size Distribution

**Expected discovery:**
```
Log sizes:
- Small (<1KB): XX%
- Medium (1-5KB): YY%
- Large (>5KB): ZZ%

Per invocation: XX KB average

Routing recommendation:
- Portal26 threshold: < XX KB
- Kinesis threshold: XX-YYY KB
- S3 threshold: > YYY KB
```

---

## Real-World Validation Checklist

### ✅ Before Starting:

- [ ] Pub/Sub subscription exists
- [ ] Reasoning Engine is deployed
- [ ] Can trigger the engine
- [ ] Python dependencies installed

### ✅ During Analysis:

- [ ] Analyzer is running
- [ ] Triggered at least 5 invocations
- [ ] Seeing traces captured in analyzer output
- [ ] No errors in analyzer

### ✅ After Analysis:

- [ ] Final report generated
- [ ] JSON file created
- [ ] Reviewed aggregate statistics
- [ ] Visualized at least one trace
- [ ] Compared multiple traces

---

## Troubleshooting Real Data

### Issue: "No traces captured"

**Check 1: Are logs flowing to Pub/Sub?**
```bash
gcloud pubsub subscriptions pull vertex-telemetry-subscription \
  --limit=1 \
  --project=agentic-ai-integration-490716
```

**Expected:** Should see a message

**If empty:**
```bash
# Seek back 7 days
gcloud pubsub subscriptions seek vertex-telemetry-subscription \
  --time=-P7D \
  --project=agentic-ai-integration-490716

# Try pull again
gcloud pubsub subscriptions pull vertex-telemetry-subscription \
  --limit=1 \
  --project=agentic-ai-integration-490716
```

---

**Check 2: Is log sink working?**
```bash
gcloud logging sinks describe vertex-telemetry-all \
  --project=agentic-ai-integration-490716
```

**Expected:** Should show destination and filter

---

**Check 3: Are logs being generated?**
```bash
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --limit=5 \
  --project=agentic-ai-integration-490716
```

**Expected:** Should see recent logs

**If not:** Trigger your agent first!

---

### Issue: "Analyzer crashes"

**Possible cause:** Memory issue

**Fix:**
```bash
# Reduce analysis duration
export ANALYSIS_DURATION=60
python log_pattern_analyzer.py
```

---

### Issue: "Cannot connect to Pub/Sub"

**Check authentication:**
```bash
gcloud auth application-default login
```

---

## Expected Real Results

Based on typical Reasoning Engine behavior:

### Typical Pattern:
```
Logs per invocation: 15-30
Spans per invocation: 2-4
Duration: 1-5 seconds
Size per invocation: 30-80 KB

Severity: 80-90% INFO, 5-15% WARNING, <5% ERROR
Log types: 50% general, 25% request/response, 25% trace
```

### Your Actual Results Will Show:
- Your specific numbers
- Your unique patterns
- Your actual bottlenecks
- Your real log sizes

**Use this to make decisions about:**
- Portal26 costs
- Routing thresholds
- Performance optimization
- Monitoring strategy

---

## Next Steps After Validation

### 1. Cost Estimation

```
Your average: XX KB per invocation
Expected invocations: 1000/day
Daily data: XX KB × 1000 = XX MB
Monthly: XX MB × 30 = X.X GB

Portal26 cost: Calculate based on X.X GB/month
```

### 2. Routing Configuration

```
Based on your size distribution:
SMALL_LOG_THRESHOLD=XXXXX   # Your 80th percentile
LARGE_LOG_THRESHOLD=XXXXXX  # Your 95th percentile
```

### 3. Performance Baseline

```
Current average: X.XXs
Target: Y.YYs
Gap: Z.ZZs

Focus on: [LLM calls / Tool calls / Other]
```

### 4. Monitoring Setup

```
Alert if:
- Logs per invocation > XX (your avg + 50%)
- Duration > X.Xs (your avg + 100%)
- Error rate > X% (your current + threshold)
```

---

## Ready to Validate?

**Start now:**

```bash
# Terminal 1
cd C:\Yesu\ai_agent_projectgcp\analysis_tools
python log_pattern_analyzer.py

# Terminal 2 (after analyzer starts)
python test_agent_invocations.py \
  --engine projects/961756870884/locations/us-central1/reasoningEngines/6010661182900273152 \
  --count 5 \
  --delay 10
```

**Let it run for 5 minutes and see YOUR real patterns!**
