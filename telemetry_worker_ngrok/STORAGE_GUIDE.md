# Trace Storage Guide

## 📦 Overview

The telemetry worker now **automatically stores traces at each processing stage** for audit, debugging, and analysis purposes.

**What gets stored:**
1. ✅ **Raw GCP Trace** - Original trace from Cloud Trace API (before transformation)
2. ✅ **OTEL Transformed Trace** - After converting to OpenTelemetry format
3. ✅ **Export Confirmation** - Response from Portal26 after export
4. ✅ **Processing Logs** - Audit trail of each step

---

## 📁 Directory Structure

```
trace_archive/
├── raw_gcp/              # Raw GCP traces (before OTEL)
│   ├── tenant1_58c0122e..._20260403_160010_raw.json
│   ├── tenant1_7ecbf534..._20260403_160520_raw.json
│   └── ...
│
├── otel/                 # OTEL transformed traces
│   ├── tenant1_58c0122e..._20260403_160010_otel.json
│   ├── tenant1_7ecbf534..._20260403_160520_otel.json
│   └── ...
│
├── confirmations/        # Export confirmations from Portal26
│   ├── tenant1_58c0122e..._20260403_160011_confirm.json
│   ├── tenant1_7ecbf534..._20260403_160521_confirm.json
│   └── ...
│
└── metadata/             # Processing logs (audit trail)
    ├── processing_log_20260403.jsonl
    ├── processing_log_20260404.jsonl
    └── ...
```

---

## 🔧 Configuration

### Enable/Disable Storage

**In `.env` file:**
```bash
# Enable trace storage (default: true)
ENABLE_TRACE_STORAGE=true

# Storage directory (default: ./trace_archive)
TRACE_ARCHIVE_PATH=./trace_archive

# Retention period in days (default: 7)
TRACE_ARCHIVE_RETENTION_DAYS=7
```

### Disable Storage
```bash
ENABLE_TRACE_STORAGE=false
```

---

## 📄 File Formats

### 1. Raw GCP Trace (`raw_gcp/`)

**Filename:** `{tenant_id}_{trace_id}_{timestamp}_raw.json`

**Content:**
```json
{
  "storage_type": "raw_gcp_trace",
  "timestamp": "2026-04-03T10:00:10.123Z",
  "metadata": {
    "trace_id": "58c0122e87277c31e4ceb59ac5f69ae6",
    "project_id": "agentic-ai-integration-490716",
    "tenant_id": "tenant1",
    "reasoning_engine_id": "8081657304514035712",
    "location": "us-central1"
  },
  "trace": {
    "project_id": "agentic-ai-integration-490716",
    "trace_id": "58c0122e87277c31e4ceb59ac5f69ae6",
    "spans": [
      {
        "span_id": "7816615611132699434",
        "parent_span_id": null,
        "name": "invocation",
        "start_time": "2026-04-03T10:00:00.000Z",
        "end_time": "2026-04-03T10:00:05.530Z",
        "labels": {
          "tenant_id": "tenant1"
        },
        "status": {
          "code": 0,
          "message": null
        }
      },
      {
        "span_id": "2066728912749044068",
        "parent_span_id": "7816615611132699434",
        "name": "invoke_agent gcp_traces_agent",
        "start_time": "2026-04-03T10:00:00.100Z",
        "end_time": "2026-04-03T10:00:02.961Z",
        "labels": {}
      }
      // ... more spans
    ]
  }
}
```

**Use cases:**
- Verify original trace data from GCP
- Compare before/after transformation
- Debug transformation issues
- Audit original data

---

### 2. OTEL Transformed Trace (`otel/`)

**Filename:** `{tenant_id}_{trace_id}_{timestamp}_otel.json`

**Content:**
```json
{
  "storage_type": "otel_transformed",
  "timestamp": "2026-04-03T10:00:10.456Z",
  "metadata": {
    "trace_id": "58c0122e87277c31e4ceb59ac5f69ae6",
    "tenant_id": "tenant1",
    "project_id": "agentic-ai-integration-490716"
  },
  "otel_trace": {
    "resource": {
      "attributes": [
        {
          "key": "service.name",
          "value": {"stringValue": "vertex-ai-agent"}
        },
        {
          "key": "portal26.user.id",
          "value": {"stringValue": "relusys"}
        },
        {
          "key": "portal26.tenant_id",
          "value": {"stringValue": "tenant1"}
        },
        {
          "key": "tenant.id",
          "value": {"stringValue": "tenant1"}
        }
      ]
    },
    "scopeSpans": [
      {
        "scope": {
          "name": "vertex-ai-telemetry",
          "version": "1.0"
        },
        "spans": [
          {
            "traceId": "NThjMDEyMmU4NzI3N2MzMWU0Y2ViNTlhYzVmNjlhZTY=",
            "spanId": "bG1pIG5hcGk=",
            "parentSpanId": "",
            "name": "invocation",
            "startTimeUnixNano": "1709463600000000000",
            "endTimeUnixNano": "1709463605530000000",
            "attributes": [
              {
                "key": "tenant.id",
                "value": {"stringValue": "tenant1"}
              }
            ]
          }
          // ... more spans
        ]
      }
    ]
  }
}
```

**Use cases:**
- Verify OTEL transformation correctness
- Check span ID conversion (decimal → hex)
- Verify resource attributes
- Debug Portal26 export issues

---

### 3. Export Confirmation (`confirmations/`)

**Filename:** `{tenant_id}_{trace_id}_{timestamp}_confirm.json`

**Content (Success):**
```json
{
  "storage_type": "export_confirmation",
  "timestamp": "2026-04-03T10:00:11.234Z",
  "trace_id": "58c0122e87277c31e4ceb59ac5f69ae6",
  "tenant_id": "tenant1",
  "export_success": true,
  "status_code": 200,
  "response_body": "{\"partialSuccess\":{\"rejectedSpans\":0}}",
  "error": null,
  "metadata": {
    "endpoint": "https://otel-tenant1.portal26.in:4318/v1/traces",
    "export_time_ms": 456
  }
}
```

**Content (Failure):**
```json
{
  "storage_type": "export_confirmation",
  "timestamp": "2026-04-03T10:00:11.234Z",
  "trace_id": "58c0122e87277c31e4ceb59ac5f69ae6",
  "tenant_id": "tenant1",
  "export_success": false,
  "status_code": 400,
  "response_body": "{\"error\":\"Invalid span ID\"}",
  "error": "HTTP 400: Invalid span ID",
  "metadata": {}
}
```

**Use cases:**
- Confirm successful Portal26 delivery
- Debug export failures
- Track rejected spans
- Monitor success rates

---

### 4. Processing Log (`metadata/processing_log_{date}.jsonl`)

**Filename:** `processing_log_20260403.jsonl` (daily log)

**Format:** JSON Lines (one JSON per line)

**Content:**
```jsonl
{"storage_type":"processing_log","timestamp":"2026-04-03T10:00:10.123Z","trace_id":"58c0122e...","tenant_id":"tenant1","stage":"fetch","status":"success","details":{"span_count":7}}
{"storage_type":"processing_log","timestamp":"2026-04-03T10:00:10.456Z","trace_id":"58c0122e...","tenant_id":"tenant1","stage":"transform","status":"success","details":{"format":"otel_protobuf"}}
{"storage_type":"processing_log","timestamp":"2026-04-03T10:00:11.234Z","trace_id":"58c0122e...","tenant_id":"tenant1","stage":"export","status":"success","details":{"endpoint":"portal26","status_code":200}}
```

**Use cases:**
- Audit trail of all processing
- Track success/failure rates
- Debug pipeline issues
- Performance analysis

---

## 🔍 Querying Stored Traces

### Get Trace History
```python
from storage_manager import StorageManager

storage = StorageManager()
history = storage.get_trace_history("58c0122e87277c31e4ceb59ac5f69ae6")

print(history)
# {
#   'trace_id': '58c0122e87277c31e4ceb59ac5f69ae6',
#   'raw_gcp': ['./trace_archive/raw_gcp/tenant1_58c0122e..._raw.json'],
#   'otel': ['./trace_archive/otel/tenant1_58c0122e..._otel.json'],
#   'confirmations': ['./trace_archive/confirmations/tenant1_58c0122e..._confirm.json']
# }
```

### Get Storage Statistics
```python
stats = storage.get_statistics()

print(stats)
# {
#   'enabled': True,
#   'base_path': './trace_archive',
#   'directories': {
#     'raw_gcp': {
#       'file_count': 15,
#       'total_size_bytes': 245760,
#       'total_size_mb': 0.23
#     },
#     'otel': {
#       'file_count': 15,
#       'total_size_bytes': 512000,
#       'total_size_mb': 0.49
#     },
#     'confirmations': {
#       'file_count': 15,
#       'total_size_bytes': 7680,
#       'total_size_mb': 0.01
#     }
#   }
# }
```

### Cleanup Old Files
```python
# Clean up files older than 7 days
storage.cleanup_old_files(days=7)
```

---

## 🔄 Complete Flow Example

### 1. Trigger Agent
```bash
# Send query to Vertex AI agent
https://console.cloud.google.com/vertex-ai/agents/agent-engines/8081657304514035712
Query: "What is the weather in Tokyo?"
```

### 2. Files Created

**After fetching (Step 1):**
```
trace_archive/raw_gcp/tenant1_58c0122e..._20260403_160010_raw.json
trace_archive/metadata/processing_log_20260403.jsonl (appended)
```

**After transformation (Step 2):**
```
trace_archive/otel/tenant1_58c0122e..._20260403_160010_otel.json
trace_archive/metadata/processing_log_20260403.jsonl (appended)
```

**After export (Step 3):**
```
trace_archive/confirmations/tenant1_58c0122e..._20260403_160011_confirm.json
trace_archive/metadata/processing_log_20260403.jsonl (appended)
```

### 3. Verify Files
```bash
# List all files for this trace
ls -lh trace_archive/*/tenant1_58c0122e*

# View raw GCP trace
cat trace_archive/raw_gcp/tenant1_58c0122e..._20260403_160010_raw.json | jq

# View OTEL trace
cat trace_archive/otel/tenant1_58c0122e..._20260403_160010_otel.json | jq

# View export confirmation
cat trace_archive/confirmations/tenant1_58c0122e..._20260403_160011_confirm.json | jq

# View processing log for today
cat trace_archive/metadata/processing_log_20260403.jsonl | jq
```

---

## 📊 Analysis Examples

### Count Successful Exports Today
```bash
grep '"stage":"export"' trace_archive/metadata/processing_log_$(date +%Y%m%d).jsonl | \
grep '"status":"success"' | wc -l
```

### Find Failed Transformations
```bash
grep '"stage":"transform"' trace_archive/metadata/processing_log_*.jsonl | \
grep '"status":"error"'
```

### Calculate Success Rate
```bash
# Total exports
total=$(grep '"stage":"export"' trace_archive/metadata/processing_log_$(date +%Y%m%d).jsonl | wc -l)

# Successful exports
success=$(grep '"stage":"export"' trace_archive/metadata/processing_log_$(date +%Y%m%d).jsonl | \
grep '"status":"success"' | wc -l)

# Success rate
echo "scale=2; $success * 100 / $total" | bc
```

### Get Traces by Tenant
```bash
ls trace_archive/raw_gcp/tenant1_* | wc -l  # Count for tenant1
ls trace_archive/raw_gcp/tenant2_* | wc -l  # Count for tenant2
```

---

## 🧹 Maintenance

### Manual Cleanup
```bash
# Delete files older than 7 days
find trace_archive -type f -mtime +7 -delete

# Delete files older than 30 days
find trace_archive -type f -mtime +30 -delete
```

### Automated Cleanup (Cron)
```bash
# Add to crontab
crontab -e

# Run cleanup daily at 2 AM
0 2 * * * python -c "from storage_manager import StorageManager; StorageManager().cleanup_old_files(7)"
```

### Archive to Cloud Storage
```bash
# Upload to GCS (for long-term storage)
gsutil -m cp -r trace_archive gs://your-bucket/trace_archive_$(date +%Y%m%d)/
```

---

## 💾 Storage Size Estimates

### Per Trace
- **Raw GCP:** ~1-5 KB per span → ~10-30 KB per trace
- **OTEL:** ~2-10 KB per span → ~20-60 KB per trace
- **Confirmation:** ~0.5 KB per trace
- **Processing Log:** ~0.2 KB per trace

**Total per trace:** ~30-90 KB

### For 1000 Traces/Day
- **Raw GCP:** ~30 MB/day
- **OTEL:** ~60 MB/day
- **Confirmations:** ~0.5 MB/day
- **Processing Logs:** ~0.2 MB/day

**Total:** ~90 MB/day = **2.7 GB/month**

### With 7-Day Retention
**Storage needed:** ~630 MB

---

## 🔐 Security Considerations

### Sensitive Data
- Traces may contain user prompts and responses
- Resource attributes include tenant IDs
- Store in secure location with proper access controls

### Access Control
```bash
# Set restrictive permissions
chmod 700 trace_archive
chmod 600 trace_archive/*/*.json

# Only worker process should access
chown telemetry-worker:telemetry-worker trace_archive -R
```

### Data Retention
- Configure retention based on compliance requirements
- GDPR: May need to delete on request
- Consider encryption at rest for production

---

## 🛠️ Troubleshooting

### Storage Not Working

**Check 1: Is storage enabled?**
```bash
grep ENABLE_TRACE_STORAGE .env
# Should show: ENABLE_TRACE_STORAGE=true
```

**Check 2: Does directory exist?**
```bash
ls -ld trace_archive
# Should exist with write permissions
```

**Check 3: Check logs**
```bash
grep "StorageManager" flask_fixed_8082.log
# Should show: StorageManager initialized with path: ./trace_archive
```

### Files Not Created

**Check permissions:**
```bash
ls -la trace_archive/
# Directories should be writable
```

**Check disk space:**
```bash
df -h .
```

---

## ✅ Benefits

1. **Audit Trail** - Complete history of all processing
2. **Debugging** - Compare before/after transformation
3. **Compliance** - Proof of delivery to Portal26
4. **Analysis** - Track success rates and performance
5. **Recovery** - Replay failed exports
6. **Validation** - Verify OTEL format correctness

---

## 📝 Summary

**Storage is automatic and requires zero configuration beyond .env!**

Each trace creates **4 artifacts**:
1. Raw GCP trace (JSON)
2. OTEL transformed trace (JSON)
3. Export confirmation (JSON)
4. Processing log entries (JSONL)

**All stored with:**
- Timestamp for ordering
- Tenant ID for isolation
- Trace ID for lookup
- Metadata for context

**Check your stored traces:**
```bash
tree trace_archive
```

Happy debugging! 🎉
