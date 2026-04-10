# Client Project Setup Guide

## 📋 Overview

This guide explains what needs to be configured in **CLIENT PROJECT** to send telemetry to the central Portal26 system.

**Client Project:** `agentic-ai-integration-490716` (your Vertex AI project)  
**Telemetry Project:** `agentic-ai-integration-490716` (same project for now, can be separate)  
**Portal26 Endpoint:** `https://otel-tenant1.portal26.in:4318/v1/traces`

---

## ✅ Prerequisites

Before starting, ensure you have:
- [ ] Admin access to client project
- [ ] Vertex AI Reasoning Engine deployed and working
- [ ] Project number and ID noted down
- [ ] Service account email for telemetry worker

---

## 🔐 Required Permissions Summary

### **1. In CLIENT Project (GCP)**
Grant `roles/cloudtrace.user` to telemetry worker service account:
- **Who:** `telemetry-worker@<TELEMETRY_PROJECT>.iam.gserviceaccount.com`
- **Where:** Client project IAM
- **Why:** Allow worker to read traces from your project
- **Includes:**
  - `cloudtrace.traces.get` - Read individual traces
  - `cloudtrace.traces.list` - List traces
  - `cloudtrace.tasks.list` - List trace tasks

### **2. In TELEMETRY Project (GCP)**
Grant `roles/pubsub.publisher` to Cloud Logging service account:
- **Who:** `service-<CLIENT_PROJECT_NUMBER>@gcp-sa-logging.iam.gserviceaccount.com`
- **Where:** Pub/Sub topic IAM
- **Why:** Allow your logs to be exported to central Pub/Sub
- **Includes:**
  - `pubsub.topics.publish` - Publish messages to topic

### **3. AWS IAM for Kinesis (Portal26 Data Pull)**
If pulling telemetry data from Portal26's Kinesis stream:

**Required IAM Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:GetRecords",
        "kinesis:GetShardIterator",
        "kinesis:DescribeStream",
        "kinesis:ListShards"
      ],
      "Resource": "arn:aws:kinesis:us-east-2:473550159910:stream/stg_otel_source_data_stream"
    }
  ]
}
```

**IAM User:** Your AWS user needs to be attached to a policy with above permissions
- **Stream:** `stg_otel_source_data_stream`
- **Region:** `us-east-2`
- **Account:** `473550159910`

### **4. Vertex AI Permissions**
For deploying and managing agents:
- **Role:** `roles/aiplatform.user` or `roles/aiplatform.admin`
- **Includes:**
  - `aiplatform.reasoningEngines.create`
  - `aiplatform.reasoningEngines.delete`
  - `aiplatform.reasoningEngines.get`
  - `aiplatform.reasoningEngines.list`
  - `aiplatform.reasoningEngines.query`

### **5. Storage Permissions (for Agent Deployment)**
For storing agent packages:
- **Role:** `roles/storage.objectAdmin`
- **Bucket:** `<PROJECT_ID>-adk-staging`
- **Includes:**
  - `storage.objects.create` - Upload agent packages
  - `storage.objects.get` - Read agent packages
  - `storage.objects.delete` - Clean up old packages

---

## 📝 Step-by-Step Setup

### Step 1: Get Your Project Information

```bash
# Get project ID (already known)
PROJECT_ID="agentic-ai-integration-490716"

# Get project NUMBER (needed for service account)
gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
# Example output: 961756870884

# Set variables
PROJECT_NUMBER="961756870884"
TELEMETRY_PROJECT="agentic-ai-integration-490716"  # Can be different
```

---

### Step 2: Enable Required APIs

```bash
# Enable Cloud Trace API (for reading traces)
gcloud services enable cloudtrace.googleapis.com \
  --project=$PROJECT_ID

# Enable Cloud Logging API (already enabled with Vertex AI)
gcloud services enable logging.googleapis.com \
  --project=$PROJECT_ID
```

**Expected output:**
```
Operation "operations/..." finished successfully.
```

---

### Step 3: Create Log Sink

**Purpose:** Export Vertex AI logs to central Pub/Sub

```bash
# Create log sink
gcloud logging sinks create telemetry-sink \
  pubsub.googleapis.com/projects/$TELEMETRY_PROJECT/topics/telemetry-logs \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="8081657304514035712"' \
  --project=$PROJECT_ID
```

**What this does:**
- Filters logs from your specific Reasoning Engine
- Routes them to Pub/Sub topic in telemetry project
- Creates a service account for the sink automatically

**Expected output:**
```
Created [https://logging.googleapis.com/v2/projects/agentic-ai-integration-490716/sinks/telemetry-sink].
```

**Note the service account created:**
```
serviceAccount:service-961756870884@gcp-sa-logging.iam.gserviceaccount.com
```

---

### Step 4: Grant Pub/Sub Publisher Permission

**Purpose:** Allow log sink to publish to Pub/Sub topic

**Run in TELEMETRY PROJECT:**

```bash
# Grant roles/pubsub.publisher to log sink service account
gcloud pubsub topics add-iam-policy-binding telemetry-logs \
  --project=$TELEMETRY_PROJECT \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-logging.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

**Expected output:**
```
Updated IAM policy for topic [telemetry-logs].
bindings:
- members:
  - serviceAccount:service-961756870884@gcp-sa-logging.iam.gserviceaccount.com
  role: roles/pubsub.publisher
```

---

### Step 5: Grant Cloud Trace Read Permission

**Purpose:** Allow telemetry worker to read traces from your project

**Run in CLIENT PROJECT:**

```bash
# Get telemetry worker service account email
WORKER_SA="telemetry-worker@${TELEMETRY_PROJECT}.iam.gserviceaccount.com"

# Grant roles/cloudtrace.user to telemetry worker
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${WORKER_SA}" \
  --role="roles/cloudtrace.user" \
  --condition=None
```

**Expected output:**
```
Updated IAM policy for project [agentic-ai-integration-490716].
bindings:
- members:
  - serviceAccount:telemetry-worker@agentic-ai-integration-490716.iam.gserviceaccount.com
  role: roles/cloudtrace.user
```

**Permissions granted:**
- `cloudtrace.traces.get` - Read individual traces
- `cloudtrace.traces.list` - List traces (optional)
- `cloudtrace.tasks.list` - List trace tasks (optional)

---

### Step 6: Add Tenant ID Label (Optional but Recommended)

**Purpose:** Tag logs with tenant identifier for multi-tenant isolation

**Option A: Add to Log Sink (Automatic)**

```bash
# Update log sink with tenant label
gcloud logging sinks update telemetry-sink \
  --add-exclusion='name=exclude-non-agent,filter="NOT resource.type=\"aiplatform.googleapis.com/ReasoningEngine\""' \
  --project=$PROJECT_ID
```

**Option B: Add in Agent Configuration**

Add to your agent's environment variables or code:
```python
# In agent code
import os
os.environ['TENANT_ID'] = 'tenant1'

# Or in agent deployment
labels = {
    'tenant_id': 'tenant1'
}
```

**Option C: Add via Log Entry Labels**

Logs will automatically include tenant_id if present in agent metadata.

---

### Step 7: Verify Log Sink

**Check if log sink is working:**

```bash
# Describe log sink
gcloud logging sinks describe telemetry-sink \
  --project=$PROJECT_ID

# Check for errors
gcloud logging sinks describe telemetry-sink \
  --project=$PROJECT_ID \
  --format="value(errors)"
```

**Expected output:**
```
createTime: '2026-04-03T10:00:00.000Z'
destination: pubsub.googleapis.com/projects/agentic-ai-integration-490716/topics/telemetry-logs
filter: resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="8081657304514035712"
name: telemetry-sink
writerIdentity: serviceAccount:service-961756870884@gcp-sa-logging.iam.gserviceaccount.com
```

---

### Step 8: Test End-to-End

**1. Trigger agent execution:**
```bash
# Via Vertex AI Console
https://console.cloud.google.com/vertex-ai/agents/agent-engines/8081657304514035712

# Or via API/SDK
```

**2. Check Cloud Logging:**
```bash
# View recent logs
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --project=$PROJECT_ID \
  --limit=5 \
  --format=json
```

**3. Check Pub/Sub:**
```bash
# Check if messages are being published
gcloud pubsub topics describe telemetry-logs \
  --project=$TELEMETRY_PROJECT

# Check subscription metrics
gcloud pubsub subscriptions describe telemetry-processor \
  --project=$TELEMETRY_PROJECT
```

**4. Check Telemetry Worker Logs:**
```bash
# If using Cloud Run
gcloud run logs read telemetry-worker \
  --project=$TELEMETRY_PROJECT \
  --limit=50

# If using local ngrok
tail -f flask_fixed_8082.log
```

**5. Check Portal26:**
- Login to Portal26 UI
- Search for traces from your tenant
- Verify resource attributes match

---

## 📊 IAM Permissions Table

### GCP Permissions

| Permission | Resource | Principal | Purpose | Required |
|------------|----------|-----------|---------|----------|
| **roles/pubsub.publisher** | Pub/Sub topic | Log Sink SA | Export logs to Pub/Sub | ✅ Yes |
| **roles/cloudtrace.user** | Client project | Worker SA | Read traces from client | ✅ Yes |
| **roles/pubsub.subscriber** | Pub/Sub sub | Worker SA | Pull messages | ✅ Yes (internal) |
| **roles/run.invoker** | Cloud Run | Pub/Sub | Push to Cloud Run | ⚠️ Prod only |
| **roles/aiplatform.user** | Project | Developer/Admin | Deploy agents | ✅ Yes |
| **roles/storage.objectAdmin** | GCS Bucket | Developer/Service SA | Store agent packages | ✅ Yes |
| **roles/logging.admin** | Project | Developer/Admin | Create log sinks | ✅ Yes |

### AWS Permissions (for Kinesis Data Pull)

| Permission | Resource | Principal | Purpose | Required |
|------------|----------|-----------|---------|----------|
| **kinesis:GetRecords** | Kinesis Stream | IAM User | Read records from stream | ✅ Yes |
| **kinesis:GetShardIterator** | Kinesis Stream | IAM User | Get iterator for reading | ✅ Yes |
| **kinesis:DescribeStream** | Kinesis Stream | IAM User | Get stream metadata | ✅ Yes |
| **kinesis:ListShards** | Kinesis Stream | IAM User | List stream shards | ⚠️ Optional |

---

## 🔍 Verification Commands

### Check Log Sink Permissions
```bash
gcloud pubsub topics get-iam-policy telemetry-logs \
  --project=$TELEMETRY_PROJECT \
  --format=json
```

**Expected:**
```json
{
  "bindings": [
    {
      "members": [
        "serviceAccount:service-961756870884@gcp-sa-logging.iam.gserviceaccount.com"
      ],
      "role": "roles/pubsub.publisher"
    }
  ]
}
```

### Check Cloud Trace Permissions
```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:telemetry-worker@"
```

**Expected:**
```
ROLE
roles/cloudtrace.user
```

### Test Log Export
```bash
# Generate a test log
gcloud logging write test-log "Test message" \
  --resource=aiplatform.googleapis.com/ReasoningEngine \
  --severity=INFO \
  --project=$PROJECT_ID

# Wait a few seconds, then check Pub/Sub
gcloud pubsub subscriptions pull telemetry-processor \
  --project=$TELEMETRY_PROJECT \
  --limit=1 \
  --auto-ack
```

---

## 🐛 Troubleshooting

### Issue 1: Logs not appearing in Pub/Sub

**Check:**
```bash
# 1. Is log sink created?
gcloud logging sinks list --project=$PROJECT_ID

# 2. Does it have errors?
gcloud logging sinks describe telemetry-sink \
  --project=$PROJECT_ID \
  --format="value(errors)"

# 3. Does Logging SA have pubsub.publisher?
gcloud pubsub topics get-iam-policy telemetry-logs \
  --project=$TELEMETRY_PROJECT | grep "service-${PROJECT_NUMBER}"
```

**Fix:**
- Re-run Step 4 to grant publisher permission
- Check log filter matches your Reasoning Engine ID

---

### Issue 2: Worker can't fetch traces (403 Forbidden)

**Check:**
```bash
# Does worker SA have cloudtrace.user?
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:telemetry-worker@" \
  --format="value(bindings.role)"
```

**Fix:**
- Re-run Step 5 to grant cloudtrace.user
- Verify worker service account email is correct

---

### Issue 3: AWS Kinesis Access Denied

**Error:**
```
botocore.errorfactory.AccessDeniedException: User: arn:aws:iam::473550159910:user/yesuvadian 
is not authorized to perform: kinesis:GetShardIterator on resource: 
arn:aws:kinesis:us-east-2:473550159910:stream/stg_otel_source_data_stream
```

**Check:**
```bash
# Verify AWS credentials are configured
aws sts get-caller-identity

# Check which IAM policies are attached to your user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
aws iam list-user-policies --user-name YOUR_USERNAME
```

**Fix:**
1. **Option A: Use AWS CLI Configuration** (Recommended)
   ```bash
   aws configure
   # Enter Access Key, Secret Key, Region (us-east-2)
   ```

2. **Option B: Add IAM Policy to User**
   - Contact AWS admin to attach Kinesis read policy
   - Required policy document (see section 3 above)

3. **Option C: Request Access**
   - Contact Portal26 support for proper IAM user permissions
   - Provide your IAM user ARN

---

### Issue 4: Environment Variables Not Loaded

**Error:** Scripts can't find OTEL endpoint or AWS credentials

**Check:**
```bash
# Is .env file present?
ls -la .env

# Is it being loaded?
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'))"
```

**Fix:**
- Ensure `.env` file exists (not `.env.DISABLED`)
- Check file has correct variable names
- Verify `python-dotenv` is installed: `pip install python-dotenv`

---

### Issue 5: Traces found but not processed

**Check:**
```bash
# Check worker logs for errors
gcloud run logs read telemetry-worker \
  --project=$TELEMETRY_PROJECT \
  --limit=100 | grep ERROR
```

**Common issues:**
- Span ID conversion (fixed in otel_transformer.py)
- Portal26 authentication (check .env file)
- Network connectivity to Portal26

---

## 📋 Configuration Checklist

**Before production, verify:**

- [ ] Log sink created and active
- [ ] Log sink service account has pubsub.publisher on topic
- [ ] Worker service account has cloudtrace.user on client project
- [ ] Reasoning Engine ID in log filter is correct
- [ ] Tenant ID is set (label or attribute)
- [ ] Test trace successfully processed end-to-end
- [ ] Traces appear in Portal26 UI
- [ ] Resource attributes are correct (tenant_id, project_id)
- [ ] No error logs in Cloud Logging
- [ ] Pub/Sub has no undelivered messages

---

## 🔄 Multi-Tenant Setup (Multiple Clients)

**For each additional client project:**

1. Repeat Steps 1-5 with new project ID/number
2. Use same Pub/Sub topic (central buffer)
3. Grant cloudtrace.user to same worker SA
4. Use different tenant_id for isolation

**No restart needed!** Worker picks up new tenants automatically.

---

## 🔧 AWS Configuration for Kinesis Data Pull

If you need to pull telemetry data from Portal26's Kinesis stream for verification:

### Prerequisites
- AWS IAM user with Kinesis read permissions
- Access to Portal26's Kinesis stream: `stg_otel_source_data_stream`
- Region: `us-east-2`

### Option 1: AWS CLI Configuration (Recommended)
```bash
# Configure AWS credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: us-east-2
# Default output format: json
```

**Security Note:** This stores credentials in `~/.aws/credentials` which is more secure than hardcoding in `.env` files.

### Option 2: Environment Variables (For Scripts)
If using scripts that require AWS credentials:

```bash
# Add to .env (NOT recommended for production)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-2
```

**⚠️ Warning:** Never commit `.env` files with credentials to git!

### Option 3: IAM Role (Production)
For production deployments, use IAM roles:

```bash
# Attach role to EC2/Cloud Run service
# No credentials needed in code
```

### Testing Kinesis Access
```bash
# Test if you can access the stream
aws kinesis describe-stream \
  --stream-name stg_otel_source_data_stream \
  --region us-east-2

# Pull recent data
python pull_agent_logs.py
```

### Required IAM Policy
Your AWS IAM user/role must have this policy attached:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "KinesisReadAccess",
      "Effect": "Allow",
      "Action": [
        "kinesis:GetRecords",
        "kinesis:GetShardIterator",
        "kinesis:DescribeStream",
        "kinesis:ListShards",
        "kinesis:DescribeStreamSummary"
      ],
      "Resource": "arn:aws:kinesis:us-east-2:473550159910:stream/stg_otel_source_data_stream"
    }
  ]
}
```

**To request access:** Contact Portal26 support with your AWS IAM user ARN.

---

## 📞 Support

**If issues persist:**

1. Check all commands in this guide
2. Review worker logs: `tail -f flask_fixed_8082.log`
3. Check ARCHITECTURE_EXPLAINED.md for detailed flow
4. Verify TESTING_GUIDE.md scenarios

**Key files:**
- `ARCHITECTURE_FINAL.md` - Complete design with IAM
- `CLIENT_SETUP_GUIDE.md` - This file
- `TESTING_GUIDE.md` - Test scenarios
- `SUCCESS_SUMMARY.md` - Current working status

---

## ✅ Summary

**What you configured:**

1. ✅ **Log Sink** - Routes Vertex AI logs to Pub/Sub
2. ✅ **Pub/Sub Publisher** - Logging SA can publish messages
3. ✅ **Cloud Trace Reader** - Worker SA can read traces
4. ✅ **Tenant Labeling** - Logs tagged with tenant_id

**What happens now:**

```
Vertex AI Agent → Log → Cloud Logging → Log Sink → Pub/Sub 
    → Telemetry Worker → Cloud Trace API → OTEL Transform 
    → Portal26 Export ✅
```

**Next steps:**
- Test with real agent queries
- Verify traces in Portal26
- Monitor for errors
- Scale to production
