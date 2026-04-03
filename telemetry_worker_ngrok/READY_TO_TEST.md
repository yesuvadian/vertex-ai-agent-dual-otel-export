# ✅ Ready to Test - Complete Setup

## 🎯 Current Status (All Running)

### 1. Flask Server ✅
- **Port:** 8082
- **Status:** Running with storage enabled
- **Health:** http://localhost:8082/health
- **Log:** flask_with_storage_8082.log
- **Storage:** `trace_archive/` directory created

### 2. ngrok Tunnel ✅
- **URL:** https://tabetha-unelemental-bibulously.ngrok-free.dev
- **Target:** localhost:8082
- **Dashboard:** http://127.0.0.1:4040

### 3. Pub/Sub ✅
- **Subscription:** telemetry-processor
- **Endpoint:** https://tabetha-unelemental-bibulously.ngrok-free.dev/process
- **Status:** Configured and ready

### 4. Storage Manager ✅
- **Enabled:** true
- **Path:** ./trace_archive
- **Structure:** Created 4 subdirectories

---

## 📦 Storage Feature - NEW!

**Automatically stores traces at each step:**

```
trace_archive/
├── raw_gcp/          # Raw GCP traces (before OTEL)
├── otel/             # OTEL transformed traces
├── confirmations/    # Export confirmations from Portal26
└── metadata/         # Processing logs (audit trail)
```

**What gets saved:**
1. ✅ Raw GCP trace (after fetching from Cloud Trace API)
2. ✅ OTEL transformed trace (after conversion)
3. ✅ Export confirmation (after sending to Portal26)
4. ✅ Processing logs (audit trail of each step)

**Files created per trace:**
- `{tenant_id}_{trace_id}_{timestamp}_raw.json`
- `{tenant_id}_{trace_id}_{timestamp}_otel.json`
- `{tenant_id}_{trace_id}_{timestamp}_confirm.json`
- Daily log: `processing_log_YYYYMMDD.jsonl`

---

## 🚀 How to Test

### Step 1: Open Vertex AI Console
```
https://console.cloud.google.com/vertex-ai/agents/agent-engines/8081657304514035712
```

### Step 2: Click "Playground" Tab

### Step 3: Send Test Queries

Try these queries:
1. "What is the weather in Tokyo?"
2. "What time is it in London?"
3. "Tell me about the weather in Bengaluru"

### Step 4: Monitor Processing

**Terminal 1: Flask Logs**
```bash
cd telemetry_worker_ngrok
tail -f flask_with_storage_8082.log
```

**Expected output:**
```
INFO - Processing message <id>, insertId: <id>
INFO - Fetching trace: projects/.../traces/<trace_id>
INFO - Fetched trace <trace_id> with 7 spans
INFO - Stored raw GCP trace: ./trace_archive/raw_gcp/...
INFO - Transformed 7 spans to OTEL format
INFO - Stored OTEL trace: ./trace_archive/otel/...
INFO - Exporting 7 spans for tenant <tenant_id>
INFO - Successfully exported traces for tenant <tenant_id>
INFO - Stored export confirmation: ./trace_archive/confirmations/...
INFO - Successfully processed trace <trace_id> for tenant <tenant_id>
```

**Terminal 2: Watch Storage**
```bash
watch -n 2 'tree trace_archive'
```

**Expected:**
```
trace_archive/
├── raw_gcp/
│   └── tenant1_<trace_id>_<timestamp>_raw.json
├── otel/
│   └── tenant1_<trace_id>_<timestamp>_otel.json
├── confirmations/
│   └── tenant1_<trace_id>_<timestamp>_confirm.json
└── metadata/
    └── processing_log_20260403.jsonl
```

### Step 5: Verify Stored Data

**Check raw GCP trace:**
```bash
cat trace_archive/raw_gcp/*.json | jq
```

**Check OTEL trace:**
```bash
cat trace_archive/otel/*.json | jq
```

**Check export confirmation:**
```bash
cat trace_archive/confirmations/*.json | jq
```

**Check processing log:**
```bash
cat trace_archive/metadata/processing_log_$(date +%Y%m%d).jsonl | jq
```

### Step 6: Verify in Portal26

- Login to Portal26 UI: https://otel-tenant1.portal26.in
- Search for recent traces
- Verify resource attributes:
  - `portal26.user.id: relusys`
  - `portal26.tenant_id: tenant1`
  - `service.name: vertex-ai-agent`

---

## 📊 What to Look For

### Success Indicators ✅

1. **Flask logs show:**
   - "Processing message..."
   - "Fetched trace... with X spans"
   - "Transformed X spans to OTEL format"
   - "Successfully exported traces"
   - "Stored raw GCP trace"
   - "Stored OTEL trace"
   - "Stored export confirmation"

2. **Files created:**
   - 3 JSON files per trace (raw, otel, confirm)
   - 1 processing log entry per stage (3 entries total)

3. **Portal26:**
   - Trace appears with correct resource attributes
   - All spans visible
   - Timing information correct

### Failure Indicators ⚠️

1. **Flask logs show:**
   - "Failed to fetch trace"
   - "Failed to transform"
   - "Export failed"

2. **No files created in trace_archive/**

3. **ngrok dashboard shows 500 errors**

---

## 🔍 Debugging Commands

### Check Flask Status
```bash
curl http://localhost:8082/health
```

### Check ngrok Status
```bash
curl https://tabetha-unelemental-bibulously.ngrok-free.dev/health
```

### Check Storage Stats
```bash
python -c "
from storage_manager import StorageManager
storage = StorageManager()
import json
print(json.dumps(storage.get_statistics(), indent=2))
"
```

### Get Trace History
```bash
python -c "
from storage_manager import StorageManager
storage = StorageManager()
history = storage.get_trace_history('TRACE_ID_HERE')
import json
print(json.dumps(history, indent=2))
"
```

### Count Stored Traces
```bash
echo "Raw GCP traces: $(ls trace_archive/raw_gcp/*.json 2>/dev/null | wc -l)"
echo "OTEL traces: $(ls trace_archive/otel/*.json 2>/dev/null | wc -l)"
echo "Confirmations: $(ls trace_archive/confirmations/*.json 2>/dev/null | wc -l)"
```

---

## 📝 Test Checklist

Before sending prompts, verify:

- [ ] Flask is running (curl localhost:8082/health returns 200)
- [ ] ngrok is active (tunnel URL accessible)
- [ ] Pub/Sub points to ngrok (check subscription)
- [ ] Storage directories exist (ls trace_archive/)
- [ ] .env has ENABLE_TRACE_STORAGE=true
- [ ] No other processes on port 8082

During testing, verify:

- [ ] Flask logs show processing messages
- [ ] Files appear in trace_archive/
- [ ] No ERROR logs in Flask
- [ ] ngrok dashboard shows requests
- [ ] Traces appear in Portal26

After testing, check:

- [ ] All 3 file types created per trace
- [ ] Processing log has 3 entries per trace (fetch, transform, export)
- [ ] Export confirmations show success: true
- [ ] Portal26 has traces with correct attributes

---

## 🎉 Ready to Test!

**Everything is configured and running.**

**Send your prompts from Google Cloud Console!**

**Monitor logs:**
```bash
tail -f flask_with_storage_8082.log
```

**Watch storage:**
```bash
watch -n 2 'tree trace_archive'
```

**All systems GO!** 🚀
