# GCP Log Sink - Deep Dive Study Guide

## 📚 **What is a Log Sink?**

A **Log Sink** (also called Logging Sink) is a GCP service that routes log entries from Cloud Logging to supported destinations outside of Cloud Logging.

**Official Name:** `google.logging.v2.LogSink`

**Purpose:** Export logs from Cloud Logging to:
- Pub/Sub topics
- Cloud Storage buckets
- BigQuery datasets
- Other Google Cloud projects

---

## 🏗️ **Architecture & Components**

### Log Sink Structure

```
┌─────────────────────────────────────────────────────────┐
│                    CLOUD LOGGING                         │
│  (Centralized log repository - ALL logs go here first)  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Continuous monitoring
                     ↓
        ┌────────────────────────────┐
        │       LOG SINK             │
        │                            │
        │  ┌──────────────────────┐  │
        │  │  Filter Expression   │  │  "Which logs to export?"
        │  │  (Query language)    │  │
        │  └──────────────────────┘  │
        │            ↓                │
        │  ┌──────────────────────┐  │
        │  │  Destination         │  │  "Where to send them?"
        │  │  (Pub/Sub, GCS, etc) │  │
        │  └──────────────────────┘  │
        │            ↓                │
        │  ┌──────────────────────┐  │
        │  │  Writer Identity     │  │  "Who is sending?"
        │  │  (Service Account)   │  │
        │  └──────────────────────┘  │
        └────────────┬───────────────┘
                     │
                     │ Forwards matching logs
                     ↓
        ┌────────────────────────────┐
        │      DESTINATION           │
        │  (Pub/Sub / GCS / BigQuery)│
        └────────────────────────────┘
```

### Key Components

1. **Name**: Unique identifier for the sink
2. **Filter**: Query that determines which logs to export
3. **Destination**: Where logs are sent
4. **Writer Identity**: Service account that writes to destination

---

## 🔍 **Log Filters (The Heart of Log Sink)**

### Filter Language

Log Sinks use **Logging Query Language** (similar to SQL WHERE clause)

**Basic Syntax:**
```
field_name operator value
```

### Common Filter Fields

| Field | Description | Example |
|-------|-------------|---------|
| `resource.type` | Type of resource that generated the log | `"gce_instance"`, `"aiplatform.googleapis.com/ReasoningEngine"` |
| `resource.labels.*` | Labels attached to the resource | `resource.labels.project_id="my-project"` |
| `logName` | Full log name | `logName="projects/my-project/logs/syslog"` |
| `severity` | Log severity level | `severity="ERROR"` or `severity>="WARNING"` |
| `timestamp` | When the log was created | `timestamp>="2024-04-20T00:00:00Z"` |
| `textPayload` | Text content of the log | `textPayload=~"error.*"` (regex) |
| `jsonPayload.*` | JSON fields in structured logs | `jsonPayload.user_id="12345"` |
| `protoPayload.*` | Protocol buffer payload | `protoPayload.status.code=5` |

### Filter Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equals | `severity="ERROR"` |
| `!=` | Not equals | `severity!="INFO"` |
| `>`, `>=`, `<`, `<=` | Comparison | `timestamp>="2024-01-01"` |
| `=~` | Regex match | `textPayload=~"user.*logged in"` |
| `!~` | Regex not match | `textPayload!~"debug"` |
| `:` | Has substring | `textPayload:"error"` |
| `AND` | Logical AND | `severity="ERROR" AND resource.type="gce_instance"` |
| `OR` | Logical OR | `severity="ERROR" OR severity="CRITICAL"` |
| `NOT` | Logical NOT | `NOT severity="INFO"` |

### Filter Examples

#### Example 1: Filter by Resource Type
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
```
**Matches:** All logs from Vertex AI Reasoning Engines

#### Example 2: Filter by Specific Agent
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND resource.labels.reasoning_engine_id="8213677864684355584"
```
**Matches:** Logs only from specific Reasoning Engine

#### Example 3: Multiple Agents (Our Current Setup)
```
resource.type="aiplatform.googleapis.com/ReasoningEngine" 
AND (
  resource.labels.reasoning_engine_id="6010661182900273152" OR 
  resource.labels.reasoning_engine_id="8019460130754002944" OR 
  resource.labels.reasoning_engine_id="8213677864684355584"
)
```
**Matches:** Logs from 3 specific agents

#### Example 4: Error Logs Only
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND severity>="ERROR"
```
**Matches:** Only ERROR, CRITICAL, ALERT, EMERGENCY logs from agents

#### Example 5: Text Search
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND textPayload=~".*failed.*"
```
**Matches:** Logs containing the word "failed"

#### Example 6: Time-Based Filter
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND timestamp>="2024-04-20T00:00:00Z"
```
**Matches:** Logs from April 20, 2024 onwards

#### Example 7: Exclude Info Logs
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND NOT severity="INFO"
```
**Matches:** All logs except INFO level

#### Example 8: Multiple Conditions
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND resource.labels.reasoning_engine_id="8213677864684355584"
AND severity>="WARNING"
AND timestamp>="2024-04-01T00:00:00Z"
```
**Matches:** Warning+ logs from specific agent after April 1st

---

## 🎯 **Destinations**

### Supported Destinations

#### 1. **Pub/Sub Topic**
```
pubsub.googleapis.com/projects/PROJECT_ID/topics/TOPIC_NAME
```

**Use Cases:**
- Real-time log streaming
- Cross-cloud integration (like our GCP → AWS setup)
- Event-driven processing

**Pros:**
- Real-time delivery
- Reliable message queuing
- Retry mechanism
- Integration with other systems

**Cons:**
- Messages expire after 7 days
- Requires subscription to consume

#### 2. **Cloud Storage Bucket**
```
storage.googleapis.com/BUCKET_NAME
```

**Use Cases:**
- Long-term archival
- Compliance and audit requirements
- Batch processing

**Pros:**
- Unlimited retention
- Very cheap storage
- Can export to other systems later

**Cons:**
- Not real-time (batched hourly)
- Harder to query
- JSON format files

#### 3. **BigQuery Dataset**
```
bigquery.googleapis.com/projects/PROJECT_ID/datasets/DATASET_NAME
```

**Use Cases:**
- Log analytics
- Complex queries on logs
- Dashboards and reporting

**Pros:**
- SQL query interface
- Fast analytics
- Integration with BI tools

**Cons:**
- Cost (storage + queries)
- Slightly delayed (not real-time)

#### 4. **Another Project**
```
logging.googleapis.com/projects/OTHER_PROJECT_ID
```

**Use Cases:**
- Centralized logging
- Multi-project organizations

---

## 🔧 **Creating and Managing Log Sinks**

### Method 1: gcloud CLI

#### Create Sink
```bash
gcloud logging sinks create SINK_NAME \
  DESTINATION \
  --log-filter='FILTER_EXPRESSION' \
  --project=PROJECT_ID
```

**Example: Pub/Sub Sink**
```bash
gcloud logging sinks create reasoning-engine-to-pubsub \
  pubsub.googleapis.com/projects/agentic-ai-integration-490716/topics/reasoning-engine-logs-topic \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --project=agentic-ai-integration-490716
```

#### Update Sink
```bash
gcloud logging sinks update SINK_NAME \
  --log-filter='NEW_FILTER' \
  --project=PROJECT_ID
```

#### Delete Sink
```bash
gcloud logging sinks delete SINK_NAME \
  --project=PROJECT_ID
```

#### List Sinks
```bash
gcloud logging sinks list \
  --project=PROJECT_ID
```

#### Describe Sink
```bash
gcloud logging sinks describe SINK_NAME \
  --project=PROJECT_ID
```

### Method 2: Console UI

**Steps:**
1. Go to Cloud Console: https://console.cloud.google.com
2. Navigate to **Logging** → **Logs Router**
3. Click **Create Sink**
4. Fill in:
   - Sink name
   - Sink destination (select service)
   - Filter (use Query Builder or write manually)
5. Click **Create Sink**

**Console URL:**
```
https://console.cloud.google.com/logs/router?project=PROJECT_ID
```

### Method 3: Python API (Programmatic)

See our `setup_log_sink_programmatic.py` script for detailed example.

**Quick snippet:**
```python
from google.cloud.logging_v2 import ConfigServiceV2Client
from google.cloud.logging_v2.types import LogSink

client = ConfigServiceV2Client()
parent = f"projects/{project_id}"

sink = LogSink(
    name="my-sink",
    destination=f"pubsub.googleapis.com/projects/{project_id}/topics/{topic_name}",
    filter='resource.type="aiplatform.googleapis.com/ReasoningEngine"'
)

created_sink = client.create_sink(parent=parent, sink=sink)
print(f"Created sink: {created_sink.name}")
```

---

## 🔐 **Permissions & IAM**

### Required Permissions to Create/Manage Sinks

**To create sinks:**
- `logging.sinks.create`
- `logging.sinks.update`
- `logging.sinks.delete`

**Pre-defined roles:**
- `roles/logging.configWriter` - Can create/update/delete sinks
- `roles/logging.admin` - Full logging permissions

**Grant permission:**
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:EMAIL@example.com" \
  --role="roles/logging.configWriter"
```

### Writer Identity (Service Account)

When you create a sink, Cloud Logging automatically creates a **writer identity** (service account).

**Format:**
```
serviceAccount:o12345678901234567890@gcp-sa-logging.iam.gserviceaccount.com
```

**Purpose:** This service account writes logs to the destination.

**Important:** You must grant this service account permission to write to the destination!

#### For Pub/Sub Destination
```bash
gcloud pubsub topics add-iam-policy-binding TOPIC_NAME \
  --member='serviceAccount:WRITER_IDENTITY' \
  --role='roles/pubsub.publisher' \
  --project=PROJECT_ID
```

#### For Cloud Storage Destination
```bash
gsutil iam ch serviceAccount:WRITER_IDENTITY:objectCreator gs://BUCKET_NAME
```

#### For BigQuery Destination
```bash
bq add-iam-policy-binding \
  --member='serviceAccount:WRITER_IDENTITY' \
  --role='roles/bigquery.dataEditor' \
  PROJECT_ID:DATASET_NAME
```

---

## 📊 **Log Sink Behavior**

### Real-time Processing

**Latency:** ~1-2 seconds from log creation to sink delivery

**Flow:**
```
Log created → Cloud Logging → Sink evaluates filter → Sends to destination
     ↓            ↓                    ↓                      ↓
  00:00        00:01                00:01                  00:02
```

### What Gets Exported

**Included in exported logs:**
- All log entry fields (timestamp, severity, payload, etc.)
- Resource information
- Labels
- Metadata

**Format:** JSON structure

**Example exported log:**
```json
{
  "insertId": "abc123",
  "jsonPayload": {
    "message": "[AGENT] Query received"
  },
  "resource": {
    "type": "aiplatform.googleapis.com/ReasoningEngine",
    "labels": {
      "project_id": "agentic-ai-integration-490716",
      "reasoning_engine_id": "8213677864684355584",
      "location": "us-central1"
    }
  },
  "timestamp": "2024-04-22T10:30:45.123456Z",
  "severity": "INFO",
  "logName": "projects/agentic-ai-integration-490716/logs/aiplatform.googleapis.com%2Frequests"
}
```

### Exclusion vs. Sinks

**Important:** Log Sinks do NOT exclude logs from Cloud Logging!

```
Cloud Logging (stores ALL logs)
      ↓
Log Sink (copies matching logs to destination)
      ↓
Destination (receives copies)
```

**To exclude logs from Cloud Logging:**
Use **Exclusion Filters** (different from sinks)
```bash
gcloud logging exclusions create EXCLUSION_NAME \
  --log-filter='FILTER'
```

---

## 💰 **Costs**

### Log Sink Costs

**Good news:** Log Sinks themselves are **FREE**!

**What you pay for:**
1. **Cloud Logging ingestion:** First 50 GB/month free, then $0.50/GB
2. **Destination costs:**
   - Pub/Sub: $0.06/GB data + $0.40 per million messages
   - Cloud Storage: $0.020/GB/month (Standard)
   - BigQuery: $0.02/GB storage + $5/TB query

### Cost Optimization Tips

1. **Use specific filters** - Don't export everything
2. **Filter by severity** - Export only ERROR+ logs
3. **Sample logs** - Use `sample(insertId, 0.1)` to export 10% of logs
4. **Time-based filters** - Only export recent logs
5. **Multiple sinks** - Different sinks for different purposes

**Example: Sample 10% of logs**
```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND sample(insertId, 0.1)
```

---

## 🐛 **Troubleshooting**

### Common Issues

#### Issue 1: No logs appearing in destination

**Check:**
1. Filter matches logs
   ```bash
   # Test filter in Logs Explorer
   gcloud logging read 'YOUR_FILTER' --limit=10 --project=PROJECT_ID
   ```

2. Writer identity has permissions
   ```bash
   # Check Pub/Sub topic IAM
   gcloud pubsub topics get-iam-policy TOPIC_NAME --project=PROJECT_ID
   ```

3. Sink is active
   ```bash
   gcloud logging sinks describe SINK_NAME --project=PROJECT_ID
   ```

#### Issue 2: Too many logs exported

**Solution:** Refine filter to be more specific

#### Issue 3: Permission denied errors

**Solution:** Grant writer identity proper role on destination

#### Issue 4: Sink filter not updating

**Solution:** 
```bash
# Update sink explicitly
gcloud logging sinks update SINK_NAME \
  --log-filter='NEW_FILTER' \
  --project=PROJECT_ID
```

---

## 📖 **Testing Filters**

### Logs Explorer (Console)

1. Go to **Logging** → **Logs Explorer**
2. Enter your filter in the query box
3. Click **Run Query**
4. See matching logs

**Console URL:**
```
https://console.cloud.google.com/logs/query?project=PROJECT_ID
```

### CLI Testing

```bash
# Test filter and see results
gcloud logging read 'YOUR_FILTER' \
  --limit=10 \
  --format=json \
  --project=PROJECT_ID
```

**Example:**
```bash
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="8213677864684355584"' \
  --limit=5 \
  --project=agentic-ai-integration-490716
```

---

## 📚 **Best Practices**

### 1. **Use Descriptive Names**
```bash
# Good
reasoning-engine-to-pubsub
error-logs-to-bigquery
security-logs-to-storage

# Bad
sink1
my-sink
test
```

### 2. **Start with Specific Filters**
```bash
# Too broad - expensive!
severity>="INFO"

# Better - specific resource
resource.type="aiplatform.googleapis.com/ReasoningEngine"

# Best - specific resource + identifier
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND resource.labels.reasoning_engine_id="8213677864684355584"
```

### 3. **Test Filters Before Creating Sink**
Always test in Logs Explorer first!

### 4. **Monitor Sink Health**
Check metrics in Cloud Console:
- Log entries exported
- Errors
- Latency

### 5. **Document Your Sinks**
Keep track of:
- Why the sink exists
- What filter is used
- Where logs go
- Who needs access

### 6. **Use Multiple Sinks for Different Purposes**
```bash
# Sink 1: Real-time processing
reasoning-engine-to-pubsub → Pub/Sub → AWS Lambda

# Sink 2: Long-term archival
reasoning-engine-to-storage → Cloud Storage

# Sink 3: Analytics
reasoning-engine-to-bigquery → BigQuery
```

---

## 🔗 **Official Documentation**

**Google Cloud Docs:**
- Routing logs: https://cloud.google.com/logging/docs/routing/overview
- Filter syntax: https://cloud.google.com/logging/docs/view/logging-query-language
- Sink destinations: https://cloud.google.com/logging/docs/export/configure_export_v2

**API Reference:**
- LogSink API: https://cloud.google.com/logging/docs/reference/v2/rest/v2/projects.sinks

---

## 📝 **Quick Reference Card**

### Common Commands

```bash
# Create sink
gcloud logging sinks create SINK_NAME DESTINATION --log-filter='FILTER'

# List sinks
gcloud logging sinks list

# Describe sink
gcloud logging sinks describe SINK_NAME

# Update filter
gcloud logging sinks update SINK_NAME --log-filter='NEW_FILTER'

# Delete sink
gcloud logging sinks delete SINK_NAME

# Test filter
gcloud logging read 'FILTER' --limit=10
```

### Quick Filters

```bash
# All Reasoning Engines
resource.type="aiplatform.googleapis.com/ReasoningEngine"

# Specific agent
resource.labels.reasoning_engine_id="ID"

# Error logs only
severity>="ERROR"

# Text search
textPayload:"search term"

# Time range
timestamp>="2024-04-20T00:00:00Z"
```

---

This comprehensive guide covers everything about GCP Log Sinks. Refer to this document whenever you need to work with log routing!
