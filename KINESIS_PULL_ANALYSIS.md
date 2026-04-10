# Kinesis Pull Script Analysis

## Overview
**File:** `kenis_pull.sh` (should be `kinesis_pull.sh`)  
**Purpose:** Pull OTEL logs from AWS Kinesis stream between two timestamps  
**Use Case:** Retrieve telemetry data that was sent to Kinesis for analysis

---

## Script Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CONFIGURATION                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Get Shard Iterator at START_TIMESTAMP             │
│  ├─ AWS API: get-shard-iterator                            │
│  ├─ Type: AT_TIMESTAMP                                     │
│  └─ Returns: Iterator pointing to timestamp position       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Pull Records Loop                                  │
│  ├─ AWS API: get-records with iterator                     │
│  ├─ Decode base64 data                                     │
│  ├─ Check ApproximateArrivalTimestamp                      │
│  ├─ Filter: Only records <= END_TIMESTAMP                  │
│  ├─ Save to NDJSON file                                    │
│  └─ Move to NextShardIterator                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Output Summary & Grep Commands                     │
│  ├─ Show total records saved                               │
│  └─ Provide helper grep commands                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration Details

### AWS Credentials
```bash
AWS_ACCESS_KEY_ID="[YOUR_AWS_ACCESS_KEY]"
AWS_SECRET_ACCESS_KEY="[YOUR_AWS_SECRET_KEY]"
AWS_DEFAULT_REGION="us-east-2"
```

⚠️ **Security Issue:** Credentials are hardcoded in script!

### Kinesis Stream Details
```bash
STREAM_ARN="arn:aws:kinesis:us-east-2:427028034291:stream/stg_otel_source_data_stream"
SHARD_ID="shardId-000000000006"
```

**Stream Name:** `stg_otel_source_data_stream`  
**Purpose:** Staging environment OTEL source data  
**Shard:** `shardId-000000000006` (specific shard)

### Time Range
```bash
START_TIMESTAMP="2026-04-01T08:45:00Z"   # 14:15 IST
END_TIMESTAMP="2026-04-01T08:47:00Z"     # 14:17 IST
```

**Duration:** 2 minutes  
**Purpose:** Pull logs from specific time window

### Output Settings
```bash
OUTPUT_FILE="kinesis_records_$(date +%Y%m%d_%H%M%S).ndjson"
BATCH_LIMIT=500   # Records per API call
SLEEP_MS=0.2      # Delay between calls (throttle protection)
```

**Output Format:** NDJSON (Newline Delimited JSON)  
**Batch Size:** 500 records per request  
**Throttle Protection:** 200ms delay (5 calls/sec limit)

---

## Step-by-Step Breakdown

### Step 1: Get Initial Shard Iterator

```bash
ITERATOR=$(aws kinesis get-shard-iterator \
  --stream-arn "$STREAM_ARN" \
  --shard-id "$SHARD_ID" \
  --shard-iterator-type AT_TIMESTAMP \
  --timestamp "$START_TIMESTAMP" \
  --query 'ShardIterator' \
  --output text 2>&1)
```

**What it does:**
1. Calls AWS Kinesis API
2. Requests iterator for specific shard
3. Iterator type: `AT_TIMESTAMP` (start reading from timestamp)
4. Returns: Opaque token pointing to position in shard

**Iterator:** A pointer to a specific position in the Kinesis shard stream

---

### Step 2: Pull Records Loop

#### 2.1 Get Records
```bash
RESPONSE=$(aws kinesis get-records \
  --shard-iterator "$ITERATOR" \
  --limit "$BATCH_LIMIT" \
  --output json 2>&1)
```

**Returns JSON:**
```json
{
  "Records": [
    {
      "SequenceNumber": "...",
      "ApproximateArrivalTimestamp": 1711964700.0,
      "Data": "base64encodeddata",
      "PartitionKey": "..."
    }
  ],
  "NextShardIterator": "...",
  "MillisBehindLatest": 0
}
```

#### 2.2 Parse Response
```bash
BATCH_RECORDS=$(echo "$RESPONSE" | jq '.Records | length')
MILLIS_BEHIND=$(echo "$RESPONSE" | jq '.MillisBehindLatest')
NEXT_ITERATOR=$(echo "$RESPONSE" | jq -r '.NextShardIterator // empty')
```

**Extracts:**
- `BATCH_RECORDS`: Count of records in this batch
- `MILLIS_BEHIND`: How far behind real-time (0 = caught up)
- `NEXT_ITERATOR`: Token for next batch

#### 2.3 Process Each Record
```bash
while IFS= read -r record; do
  APPROX_ARRIVAL=$(echo "$record" | jq -r '.ApproximateArrivalTimestamp')
  ARRIVAL_EPOCH=$(date -d "@${APPROX_ARRIVAL%.*}" +%s 2>/dev/null || echo "$END_EPOCH")

  # Stop if past end timestamp
  if [[ "$ARRIVAL_EPOCH" -gt "$END_EPOCH" ]]; then
    echo "⏹  Reached END_TIMESTAMP boundary. Stopping."
    ITERATOR=""
    break
  fi

  # Decode and write record data
  echo "$record" | jq -r '.Data | @base64d' >> "$OUTPUT_FILE"
  SAVED=$((SAVED + 1))
done < <(echo "$RESPONSE" | jq -c '.Records[]')
```

**What it does:**
1. Loop through each record in batch
2. Check `ApproximateArrivalTimestamp`
3. **Filter:** Stop if record is after `END_TIMESTAMP`
4. Decode base64 `Data` field
5. Write decoded data to output file

**Example Record Data (decoded):**
```json
{
  "resourceSpans": [{
    "resource": {
      "attributes": [{
        "key": "service.name",
        "value": {"stringValue": "portal26_otel_agent"}
      }]
    },
    "scopeSpans": [{
      "spans": [{
        "traceId": "abc123...",
        "spanId": "def456...",
        "name": "agent.query"
      }]
    }]
  }]
}
```

#### 2.4 Loop Control
```bash
[[ -z "$ITERATOR" ]] && break           # End timestamp hit
[[ -z "$NEXT_ITERATOR" ]] && break      # Shard ended
[[ "$MILLIS_BEHIND" -eq 0 ]] && break   # Caught up to tip of shard

ITERATOR="$NEXT_ITERATOR"
sleep "$SLEEP_MS"
```

**Loop exits when:**
1. Reached END_TIMESTAMP
2. No more data in shard
3. Caught up to real-time (MillisBehindLatest = 0)

---

### Step 3: Output Summary & Helpers

```bash
echo "============================================"
echo "[3/3] Done! Summary:"
echo "  Total records saved : $TOTAL_RECORDS"
echo "  Output file         : $OUTPUT_FILE"
echo "============================================"

echo "💡 Quick grep commands for your OTel logs:"
echo "  grep -i 'traceid\|spanid\|otel\|opentelemetry' $OUTPUT_FILE | head -20"
echo "  grep -i 'your-service' $OUTPUT_FILE | head -20"
echo "  grep -i 'your-service' $OUTPUT_FILE | head -1 | jq ."
echo "  grep -c 'traceid' $OUTPUT_FILE"
```

**Provides:**
- Summary of records pulled
- Helpful grep commands to search logs
- Examples for finding traces, services, etc.

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Agent (Vertex AI)                   │
│  ├─ Generates telemetry (traces, metrics, logs)            │
│  └─ Exports to OTEL Collector                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  OTEL Collector / Processor                  │
│  ├─ Receives OTLP data                                      │
│  ├─ Processes/transforms                                    │
│  └─ Exports to AWS Kinesis                                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│             AWS Kinesis Data Stream                          │
│  Stream: stg_otel_source_data_stream                        │
│  ├─ Shard 0                                                 │
│  ├─ Shard 1                                                 │
│  ├─ Shard 6 ← TARGET                                        │
│  └─ ...                                                      │
│  Records stored with timestamps                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  kenis_pull.sh Script                        │
│  ├─ Get shard iterator at START_TIMESTAMP                   │
│  ├─ Pull records in batches                                 │
│  ├─ Decode base64 data                                      │
│  ├─ Filter by timestamp                                     │
│  └─ Save to NDJSON file                                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│             kinesis_records_YYYYMMDD_HHMMSS.ndjson          │
│  ├─ Line 1: { "resourceSpans": [...] }                     │
│  ├─ Line 2: { "resourceSpans": [...] }                     │
│  ├─ Line 3: { "resourceSpans": [...] }                     │
│  └─ ...                                                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Analysis/Debugging                        │
│  ├─ grep for specific traces                                │
│  ├─ jq for JSON parsing                                     │
│  └─ Verify telemetry data structure                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Pattern

This script is part of a **staging/debugging architecture**:

### Normal Flow (Production)
```
Agent → Portal26 OTEL Collector → Portal26 Backend → Portal26 UI
```

### Staging Flow (with Kinesis)
```
Agent → OTEL Collector → Kinesis Stream → [Storage/Analysis]
                              ↓
                        kenis_pull.sh
                              ↓
                        Local NDJSON file
                              ↓
                        Manual analysis
```

**Why Kinesis?**
1. **Staging/Testing:** Capture telemetry before sending to production
2. **Replay:** Pull historical data for debugging
3. **Audit:** Keep immutable log of all telemetry
4. **Failover:** Backup if Portal26 is down

---

## Key Concepts

### 1. Kinesis Shard Iterator
**What:** Opaque token pointing to position in stream  
**Types:**
- `TRIM_HORIZON`: Start from oldest record
- `LATEST`: Start from newest record
- `AT_TIMESTAMP`: Start from specific time
- `AT_SEQUENCE_NUMBER`: Start from sequence number
- `AFTER_SEQUENCE_NUMBER`: Start after sequence number

### 2. Base64 Encoding
Kinesis stores data as base64-encoded bytes:
```bash
# Encoded in Kinesis
Data: "eyJyZXNvdXJjZVNwYW5zIjpbXX0="

# Decoded by script
jq -r '.Data | @base64d'
# Result: {"resourceSpans":[]}
```

### 3. ApproximateArrivalTimestamp
**What:** When record arrived at Kinesis (not when created)  
**Format:** Unix timestamp with decimals (1711964700.123)  
**Use:** Filter records by time range

### 4. MillisBehindLatest
**What:** How far behind the stream tip you are  
**Values:**
- `0`: Caught up to real-time
- `> 0`: Still historical data to read

### 5. NDJSON Format
**Newline Delimited JSON:**
```
{"record":1}
{"record":2}
{"record":3}
```

**Benefits:**
- Stream-friendly (process line by line)
- grep-able
- Easy to parse with `jq`

---

## Usage Examples

### Pull logs from specific time range
```bash
# Edit timestamps in script
START_TIMESTAMP="2026-04-07T09:30:00Z"
END_TIMESTAMP="2026-04-07T09:35:00Z"

# Run
./kenis_pull.sh

# Output: kinesis_records_20260407_153000.ndjson
```

### Search for specific trace
```bash
# Find by trace ID
grep "00000000000000000bcfd499dbcfba74" kinesis_records_*.ndjson

# Find by service name
grep "portal26_otel_agent" kinesis_records_*.ndjson | jq .

# Count traces
grep -c "resourceSpans" kinesis_records_*.ndjson
```

### Analyze specific span
```bash
# Pretty print first trace
head -1 kinesis_records_*.ndjson | jq '.resourceSpans[0].scopeSpans[0].spans[0]'
```

---

## Comparison with Your Current Setup

### Your Agent (portal26_agent_v3)
```
Agent → Direct export to Portal26 OTEL endpoints
  ├─ /v1/traces (200 OK)
  ├─ /v1/metrics (404 Not Found)
  └─ /v1/logs (200 OK)
```

### Staging Setup (kenis_pull.sh suggests)
```
Agent → OTEL Collector → Kinesis → Analysis
```

**Question:** Is your current agent also sending to Kinesis?

If YES:
- This script helps pull and analyze that data
- Useful for debugging before data reaches Portal26

If NO:
- This script is for a different environment (staging)
- Your agent sends directly to Portal26 (simpler)

---

## Security Concerns

### Hardcoded Credentials
```bash
AWS_ACCESS_KEY_ID="[YOUR_AWS_ACCESS_KEY]"
AWS_SECRET_ACCESS_KEY="[YOUR_AWS_SECRET_KEY]"
```

**Risks:**
- ❌ Credentials visible in plaintext
- ❌ Committed to git (if tracked)
- ❌ Shared with anyone with file access

**Better approach:**
```bash
# Use AWS CLI credentials
# ~/.aws/credentials
[default]
aws_access_key_id = [YOUR_AWS_ACCESS_KEY]
aws_secret_access_key = [YOUR_AWS_SECRET_KEY]

# Script just needs:
aws kinesis get-shard-iterator ...  # Uses default credentials
```

---

## When to Use This Script

### Use Cases:
1. **Debugging:** Agent not showing data in Portal26? Pull from Kinesis to verify export
2. **Historical Analysis:** Analyze telemetry from past time periods
3. **Testing:** Verify telemetry structure before sending to production
4. **Replay:** Re-process telemetry data with different logic

### Not Needed When:
- Agent sends directly to Portal26 (your current setup)
- Portal26 UI provides sufficient analysis
- No intermediate Kinesis stream in architecture

---

## Summary

**Purpose:** Pull OTEL telemetry logs from AWS Kinesis between two timestamps

**How it works:**
1. Get iterator at start timestamp
2. Loop: fetch records → decode → filter by time → save
3. Output: NDJSON file with decoded telemetry

**Key Features:**
- Time-range filtering
- Base64 decoding
- Throttle protection
- Helpful grep commands

**Relation to your setup:**
- Your agent sends to Portal26 directly
- This script is for Kinesis-based staging/testing
- Useful if you add Kinesis to your architecture

**Security:** ⚠️ Credentials should be in `~/.aws/credentials`, not hardcoded!
