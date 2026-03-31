# JSON Telemetry Collection - Setup Complete ✅

**Date:** 2026-03-31  
**Status:** WORKING - JSON files are now being generated

---

## What Was the Problem?

Previously, the local OTEL receiver only saved `.log` files with raw protobuf data, not human-readable JSON files.

**Old behavior:**
- ✅ Received protobuf OTEL data
- ✅ Forwarded to Portal26
- ❌ Only saved raw binary logs
- ❌ No JSON files

---

## Solution Implemented

### Updated Local OTEL Receiver

**File:** `local_otel_receiver.py` (now generates JSON)

**New features:**
1. ✅ Decodes OTLP protobuf format
2. ✅ Converts to JSON using `MessageToDict`
3. ✅ Saves as `traces_YYYYMMDD_HHMMSS.json`
4. ✅ Still forwards to Portal26
5. ✅ Extracts and displays metadata (service name, tenant_id, span count)

**Dependencies:**
- `opentelemetry-proto` (✅ installed: v1.38.0)
- `protobuf` (✅ installed: v6.33.5)

---

## Current File Structure

```
otel-data/
├── traces_20260330.log           # Old log file (6.8 KB)
├── traces_20260331.log           # Today's log file (1.9 KB)
└── traces_20260331_102032.json   # NEW! JSON trace file (3.3 KB) ✅
```

**JSON file format:** `traces_YYYYMMDD_HHMMSS.json`
- Timestamp in filename for easy sorting
- One JSON file per OTEL request received
- Contains fully decoded trace data

---

## Sample JSON Content

**File:** `traces_20260331_102032.json`

```json
{
  "resource_spans": [
    {
      "resource": {
        "attributes": [
          {
            "key": "service.name",
            "value": {"string_value": "test_agent"}
          },
          {
            "key": "portal26.tenant_id",
            "value": {"string_value": "tenant1"}
          },
          {
            "key": "portal26.user.id",
            "value": {"string_value": "relusys"}
          },
          {
            "key": "agent.type",
            "value": {"string_value": "test"}
          }
        ]
      },
      "scope_spans": [
        {
          "spans": [
            {
              "name": "sub_operation",
              "attributes": [
                {
                  "key": "query",
                  "value": {"string_value": "What is 2+2?"}
                },
                {
                  "key": "response",
                  "value": {"string_value": "4"}
                }
              ],
              "events": [
                {
                  "name": "Processing query"
                },
                {
                  "name": "Query processed"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Contains:**
- Resource attributes (service name, tenant_id, user.id)
- Spans with names and attributes
- Events within spans
- Timing data (nanosecond precision)
- Trace IDs and span IDs

---

## How It Works Now

### When Agents Send Telemetry

```
┌─────────────────────────────────┐
│  portal26_ngrok_agent (GCP)     │
│  Query via Console or API       │
└──────────────┬──────────────────┘
               │ OTLP/HTTP
               │ Protobuf
               ▼
┌─────────────────────────────────┐
│  Ngrok Tunnel                   │
│  tabetha-unelemental-...        │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Local OTEL Receiver (Enhanced) │
│  Port: 4318                     │
│                                 │
│  Actions:                       │
│  1. Decode protobuf       ✅    │
│  2. Save JSON file        ✅    │
│  3. Log to .log file      ✅    │
│  4. Forward to Portal26   ✅    │
└─────────────────────────────────┘
               │
               │ Result
               ▼
┌─────────────────────────────────┐
│  otel-data/                     │
│  ├── traces_TIMESTAMP.json ✅   │
│  ├── traces_YYYYMMDD.log   ✅   │
│                                 │
│  AND                            │
│                                 │
│  Portal26 Endpoint              │
│  (receives forwarded data) ✅   │
└─────────────────────────────────┘
```

---

## Testing

### Test 1: Send Mock Trace (✅ Completed)

```bash
python send_test_trace.py
```

**Result:** `traces_20260331_102032.json` created successfully

**Console output:**
```
[2026-03-31 10:20:32] Received OTEL traces
From: 127.0.0.1
Content-Length: 573 bytes
Content-Type: application/x-protobuf
Service: test_agent
Tenant: tenant1
Spans: 2
[OK] Saved JSON: traces_20260331_102032.json
[OK] Forwarded to Portal26: 200
```

### Test 2: Real Agent Query (Next Step)

Query agents via Google Cloud Console:

1. Go to: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716
2. Click on **portal26_ngrok_agent**
3. Send any query (e.g., "What is the weather in Bengaluru?")
4. Check `otel-data/` for new JSON file

**Expected:** New JSON file with actual agent trace data

---

## Verification Commands

### Check for JSON files

```bash
ls -lht otel-data/*.json
# or
dir otel-data\*.json /O-D
```

### View latest JSON file

```bash
cat otel-data/traces_*.json | tail -100
# or
type otel-data\traces_*.json
```

### View receiver logs

```bash
tail -f otel-data/traces_*.log
```

### Check receiver status

```bash
curl http://localhost:4318
# Should return: OK - Local OTEL Receiver Running
```

---

## Files Modified/Created

### Modified Files

1. **local_otel_receiver.py** (replaced with JSON-enabled version)
   - Old version backed up to `local_otel_receiver_old.py`
   - New version decodes protobuf and saves JSON

### New Files

1. **local_otel_receiver_json.py** (original enhanced version)
2. **send_test_trace.py** (test script)
3. **JSON_TELEMETRY_SETUP.md** (this document)
4. **otel-data/traces_20260331_102032.json** (first JSON trace)

---

## Expected Behavior

### When portal26_ngrok_agent is Queried

✅ **JSON file created:** `otel-data/traces_YYYYMMDD_HHMMSS.json`  
✅ **Log entry created:** `otel-data/traces_YYYYMMDD.log`  
✅ **Data forwarded:** Portal26 endpoint receives data  

**JSON will contain:**
- `service.name`: "portal26_ngrok_agent"
- `portal26.tenant_id`: "tenant1"
- `portal26.user.id`: "relusys"
- `agent.type`: "ngrok-local"
- Spans with agent query/response data
- Tool calls (get_weather, get_current_time)
- LLM interactions

### When portal26_otel_agent is Queried

❌ **No local JSON:** (direct export to Portal26)  
❌ **No local log:** (bypasses local receiver)  
✅ **Data sent directly:** Portal26 endpoint receives data  

---

## Troubleshooting

### No JSON files appearing

**Check receiver is running:**
```bash
curl http://localhost:4318
```

**Check receiver process:**
```bash
netstat -ano | grep 4318
# or
ps aux | grep local_otel_receiver
```

**Restart receiver:**
```bash
# Stop old process
taskkill //F //PID <PID>

# Start new
python local_otel_receiver.py
```

### JSON files are empty or malformed

**Check protobuf library:**
```bash
pip list | grep opentelemetry-proto
# Should show: opentelemetry-proto 1.38.0
```

**Reinstall if needed:**
```bash
pip install --upgrade opentelemetry-proto
```

### Receiver not forwarding to Portal26

**Check logs:**
```bash
tail -20 otel-data/traces_*.log
```

**Look for:**
```
[OK] Forwarded to Portal26: 200
```

or

```
[ERROR] Failed to forward to Portal26: <error>
```

---

## Next Steps

### 1. Test with Real Agent (Recommended)

Query **portal26_ngrok_agent** via Google Cloud Console and verify JSON generation.

### 2. Monitor in Real-Time

```bash
# Terminal 1: Watch for new JSON files
watch -n 1 'ls -lht otel-data/*.json | head -5'

# Terminal 2: Watch receiver logs
tail -f otel-data/traces_*.log

# Terminal 3: Keep receiver running
python local_otel_receiver.py
```

### 3. Analyze Traces

```bash
# Pretty-print latest JSON
python -m json.tool otel-data/traces_*.json | less

# Count spans in a file
cat otel-data/traces_*.json | jq '.resource_spans[].scope_spans[].spans | length'

# Extract service names
cat otel-data/traces_*.json | jq '.resource_spans[].resource.attributes[] | select(.key=="service.name") | .value.string_value'
```

---

## Summary

✅ **Problem solved:** JSON files are now generated  
✅ **Test passed:** Mock trace created JSON successfully  
✅ **Ready for production:** Real agent queries will generate JSON  
✅ **Portal26 integration:** Data still forwarded correctly  

**When you query agents via Console:**
- portal26_ngrok_agent → ✅ Creates JSON file + forwards to Portal26
- portal26_otel_agent → ❌ No local JSON, direct to Portal26

---

## Quick Reference

| File Type | Location | Purpose |
|-----------|----------|---------|
| `traces_YYYYMMDD_HHMMSS.json` | `otel-data/` | Decoded OTEL trace (one per request) |
| `traces_YYYYMMDD.log` | `otel-data/` | Daily log with headers and metadata |
| `local_otel_receiver.py` | Root | Enhanced receiver with JSON support |
| `send_test_trace.py` | Root | Test script to generate sample traces |

| Command | Purpose |
|---------|---------|
| `python local_otel_receiver.py` | Start receiver |
| `python send_test_trace.py` | Send test trace |
| `ls -lht otel-data/*.json` | List JSON files (newest first) |
| `curl http://localhost:4318` | Check receiver status |

---

**Setup Complete!** 🎉

JSON telemetry collection is now working. Query your agents and watch the JSON files appear in `otel-data/`.
