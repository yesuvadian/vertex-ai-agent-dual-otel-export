# AI Agent OTEL Integration - User Testing Manual

Complete step-by-step guide to validate that your AI Agent is successfully sending telemetry data to Portal26.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Test 1: Verify Cloud Run Deployment](#test-1-verify-cloud-run-deployment)
3. [Test 2: Send Test Requests to AI Agent](#test-2-send-test-requests-to-ai-agent)
4. [Test 3: Verify OTEL Export Configuration](#test-3-verify-otel-export-configuration)
5. [Test 4: Direct OTEL Endpoint Testing](#test-4-direct-otel-endpoint-testing)
6. [Test 5: View Data in Portal26 Dashboard](#test-5-view-data-in-portal26-dashboard)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- [ ] Google Cloud SDK (`gcloud`) installed and authenticated
- [ ] Python 3.7+ installed
- [ ] Access to Portal26 dashboard
- [ ] This repository cloned locally

**Authentication Setup:**
```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project agentic-ai-integration-490716
```

---

## Test 1: Verify Cloud Run Deployment

### Step 1.1: Check Service Status

```bash
gcloud run services describe ai-agent \
  --region=us-central1 \
  --format="value(status.url,status.conditions)"
```

**Expected Output:**
```
https://ai-agent-961756870884.us-central1.run.app
```

**Status:** ✅ If you see a URL, the service is deployed.

### Step 1.2: Check Service Configuration

```bash
gcloud run services describe ai-agent \
  --region=us-central1 \
  --format="yaml(spec.template.spec.containers[0].env)" | grep -E "(OTEL|Portal26)"
```

**Expected Output:**
```yaml
- name: OTEL_SERVICE_NAME
  value: ai-agent
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: https://otel-tenant1.portal26.in:4318
- name: OTEL_TRACES_EXPORTER
  value: otlp
- name: OTEL_METRICS_EXPORTER
  value: otlp
- name: OTEL_LOGS_EXPORTER
  value: otlp
```

**Status:** ✅ If you see all OTEL environment variables, configuration is correct.

---

## Test 2: Send Test Requests to AI Agent

### Step 2.1: Test Health Endpoint

```bash
# Get auth token
TOKEN=$(gcloud auth print-identity-token)

# Test status endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://ai-agent-961756870884.us-central1.run.app/status
```

**Expected Output:**
```json
{
  "agent_mode": "manual",
  "manual_agent_enabled": true,
  "adk_agent_enabled": false
}
```

**Status:** ✅ Service is responding.

### Step 2.2: Send Unique Test Request

```bash
# Generate unique test ID
TEST_ID="TEST-$(date +%s)"

# Send test request
curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"$TEST_ID: What is the weather in Tokyo?\"}"
```

**Expected Output:**
```json
{
  "final_answer": "The weather in Tokyo is 28°C and sunny."
}
```

**Important:** Save your `TEST_ID` - you'll use it to find this trace in Portal26!

**Status:** ✅ Request processed successfully.

### Step 2.3: Generate Multiple Test Requests

Run this to generate sample traffic:

```bash
TOKEN=$(gcloud auth print-identity-token)

for i in 1 2 3 4 5; do
  echo "Request $i of 5..."
  curl -s -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test request $i: What is the weather in Tokyo?\"}"
  echo ""
  sleep 2
done

echo "✅ Generated 5 test requests"
```

**Expected:** 5 successful responses.

---

## Test 3: Verify OTEL Export Configuration

### Step 3.1: Check Cloud Run Logs for OTEL Initialization

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent" \
  --limit=50 \
  --format="value(textPayload)" \
  --project=agentic-ai-integration-490716 | grep -i "telemetry\|otel"
```

**Expected Output:**
```
[telemetry] OK OTLP trace exporter configured: https://otel-tenant1.portal26.in:4318/v1/traces
[telemetry] OK OTLP metric exporter configured: https://otel-tenant1.portal26.in:4318/v1/metrics (interval: 1000ms)
[telemetry] OK OTLP log exporter configured: https://otel-tenant1.portal26.in:4318/v1/logs
```

**Status:** ✅ All three exporters configured successfully.

### Step 3.2: Check for Export Errors

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent" \
  --limit=100 \
  --format="value(textPayload)" \
  --project=agentic-ai-integration-490716 | grep -i "error\|failed\|exception" | grep -i "otel\|export"
```

**Expected Output:** (No output or no OTEL-related errors)

**Status:** ✅ No export errors found.

---

## Test 4: Direct OTEL Endpoint Testing

### Step 4.1: Run Automated Test Script

```bash
cd /path/to/ai_agent_projectgcp
python test_otel_send.py
```

**Expected Output:**
```
============================================================
Testing Portal26 OTLP Endpoints
============================================================

1. Testing Traces Endpoint...
   URL: https://otel-tenant1.portal26.in:4318/v1/traces
   Status: 200
   Response: {"partialSuccess":{}}
   [OK] Traces endpoint accepting data!

2. Testing Metrics Endpoint...
   URL: https://otel-tenant1.portal26.in:4318/v1/metrics
   Status: 200
   Response: {"partialSuccess":{}}
   [OK] Metrics endpoint accepting data!

3. Testing Logs Endpoint...
   URL: https://otel-tenant1.portal26.in:4318/v1/logs
   Status: 200
   Response: {"partialSuccess":{}}
   [OK] Logs endpoint accepting data!
```

**Status:** ✅ All endpoints returning 200 OK.

### Step 4.2: Run Export Verification

```bash
python verify_otel_export.py
```

**Expected Output:**
```
Step 1: Sending test request to AI agent...
Response: 200
[SUCCESS] Test request completed

Step 2: Checking Cloud Run logs for OTEL export confirmation...
[OK] Traces exporter: Configured
[OK] Metrics exporter: Configured
[OK] Logs exporter: Configured
[OK] No export errors found

PROOF OF EXPORT:
- HTTP 200 responses from Portal26 OTLP endpoints
- No export errors in Cloud Run logs
- Successful request completion with telemetry instrumentation

[CONCLUSION] Data is being successfully exported to Portal26!
```

**Status:** ✅ Export verification passed.

### Step 4.3: Capture Real-Time Export

```bash
python capture_otel_export.py
```

**Expected Output:**
```
SUCCESS - PROOF OF EXPORT
================================================================================

[VERIFIED] Portal26 is accepting OTLP traces!

Evidence:
  1. HTTP 200 response from Portal26
  2. Response: {"partialSuccess":{}}
  3. Trace data successfully sent
  4. Test ID for Portal26 lookup: CAPTURE-TEST-1774594391
```

**Save the Test ID** from the output!

**Status:** ✅ Direct export to Portal26 verified.

---

## Test 5: View Data in Portal26 Dashboard

### Step 5.1: Access Portal26 Dashboard

1. Open browser and go to: **https://portal26.in**
   - Or your specific Portal26 instance URL
   - Example: **https://otel-tenant1.portal26.in**

2. **Login Credentials:**
   - Username: `titaniam`
   - Password: `helloworld`

   *(These are decoded from the Base64 auth header: `dGl0YW5pYW06aGVsbG93b3JsZA==`)*

### Step 5.2: Navigate to Traces/Observability Section

Depending on your Portal26 version, look for:
- **"Traces"** tab or menu
- **"Observability"** section
- **"APM"** or **"Monitoring"** dashboard
- **"Telemetry"** viewer

### Step 5.3: Apply Filters

Apply these filters to find your AI agent data:

| Filter | Value | Description |
|--------|-------|-------------|
| **Service Name** | `ai-agent` | Your Cloud Run service |
| **Tenant ID** | `tenant1` | Portal26 tenant |
| **User ID** | `relusys` | Portal26 user |
| **Environment** | `production` | Deployment environment |
| **Time Range** | Last 15 minutes | Recent data |

### Step 5.4: Search for Test Traces

Use the Test ID from Step 2.2 or 4.3:

1. In the search/filter box, enter your test ID
   - Example: `TEST-1774594246`
   - Or: `CAPTURE-TEST-1774594391`

2. Look for traces with these attributes:
   - **Span Name**: `agent_chat` or `test_export_verification`
   - **Duration**: ~1-2 seconds
   - **Status**: Success

### Step 5.5: Verify Trace Details

Click on a trace to view details. You should see:

**Resource Attributes:**
```
service.name: ai-agent
portal26.user.id: relusys
portal26.tenant_id: tenant1
service.version: 1.0
deployment.environment: production
```

**Span Attributes:**
```
user.message: "What is the weather in Tokyo?"
agent.success: true
agent_mode: manual
```

**Status:** ✅ Trace data visible in Portal26!

### Step 5.6: Check Metrics

Navigate to Metrics section and look for:

**Metric Name** | **Type** | **Expected Values**
---|---|---
`agent_requests_total` | Counter | Increasing with each request
`agent_response_time_seconds` | Histogram | Distribution of response times (1-3s)

**Labels/Dimensions:**
- `status`: `success` or `error`
- `agent_mode`: `manual`

### Step 5.7: Check Logs

Navigate to Logs section and search for:

**Log Messages:**
```
Chat request received: What is the weather...
Chat request completed successfully in 1.23s
```

**Log Attributes:**
- `service.name`: ai-agent
- `severity`: INFO
- Linked to trace ID

**Status:** ✅ Logs visible in Portal26!

---

## Validation Checklist

Use this checklist to confirm everything is working:

### Deployment Validation
- [ ] Cloud Run service is deployed and running
- [ ] OTEL environment variables are configured
- [ ] No deployment errors in Cloud Console

### OTEL Configuration Validation
- [ ] Traces exporter configured (check logs)
- [ ] Metrics exporter configured (check logs)
- [ ] Logs exporter configured (check logs)
- [ ] No OTEL export errors in logs

### Endpoint Validation
- [ ] Traces endpoint returns 200 OK
- [ ] Metrics endpoint returns 200 OK
- [ ] Logs endpoint returns 200 OK
- [ ] Authentication working (no 401/403 errors)

### Data Validation in Portal26
- [ ] Can access Portal26 dashboard
- [ ] Can filter by service: ai-agent
- [ ] Can see traces for test requests
- [ ] Trace attributes are correct
- [ ] Metrics are being collected
- [ ] Logs are being ingested
- [ ] Can search by test ID

### End-to-End Validation
- [ ] Send request to AI agent
- [ ] Request succeeds (200 OK)
- [ ] Trace appears in Portal26 within 1-2 minutes
- [ ] Metrics update in Portal26
- [ ] Logs appear in Portal26

---

## Troubleshooting

### Issue 1: "Cannot access Cloud Run service"

**Symptom:** 403 Forbidden or authentication errors

**Solution:**
```bash
# Get fresh auth token
gcloud auth login
TOKEN=$(gcloud auth print-identity-token)

# Test with token
curl -H "Authorization: Bearer $TOKEN" \
  https://ai-agent-961756870884.us-central1.run.app/status
```

### Issue 2: "OTEL exporters not configured"

**Symptom:** No telemetry logs in Cloud Run

**Solution:**
```bash
# Check environment variables
gcloud run services describe ai-agent \
  --region=us-central1 \
  --format="yaml(spec.template.spec.containers[0].env)"

# Redeploy if variables are missing
cd /path/to/ai_agent_projectgcp
bash deploy.sh
```

### Issue 3: "Portal26 endpoint returns errors"

**Symptom:** 401, 403, or 500 errors from Portal26

**Solution:**
```bash
# Verify authentication
echo "dGl0YW5pYW06aGVsbG93b3JsZA==" | base64 -d
# Should output: titaniam:helloworld

# Test endpoint directly
curl -X POST https://otel-tenant1.portal26.in:4318/v1/traces \
  -H "Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}'
```

### Issue 4: "No data visible in Portal26"

**Symptom:** Portal26 dashboard is empty

**Possible Causes:**

1. **Time Range**: Expand time range to "Last 1 hour"
2. **Filters**: Remove all filters and search again
3. **Tenant/User**: Verify you're viewing the correct tenant (tenant1)
4. **Delay**: Wait 2-3 minutes for data to propagate
5. **Wrong Dashboard**: Check if there's a different dashboard/view for OTLP data

**Debug Steps:**
```bash
# Verify data is being sent
python capture_otel_export.py

# Check Cloud Run logs for export confirmation
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent" \
  --limit=20 \
  --format="value(textPayload)"
```

### Issue 5: "Python script errors"

**Symptom:** Test scripts fail to run

**Solution:**
```bash
# Install dependencies
pip install requests opentelemetry-sdk opentelemetry-exporter-otlp-proto-http

# Run with python3 explicitly
python3 test_otel_send.py
```

---

## Quick Test Commands

### One-Command Full Test

```bash
# Send request and check logs in one command
TEST_ID="QUICK-TEST-$(date +%s)" && \
TOKEN=$(gcloud auth print-identity-token) && \
curl -s -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"$TEST_ID: Weather check\"}" && \
echo "" && \
echo "Test ID: $TEST_ID" && \
echo "Check Portal26 dashboard for this trace!"
```

### Check Recent Logs

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent AND timestamp>=\`date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ\`" \
  --limit=20 \
  --format="value(timestamp,textPayload)"
```

### Monitor Real-Time Logs

```bash
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent" \
  --format="value(timestamp,textPayload)"
```

---

## Success Criteria

Your OTEL integration is successful when:

✅ **All endpoints return 200 OK**
✅ **No export errors in Cloud Run logs**
✅ **Traces visible in Portal26 within 2-3 minutes**
✅ **Metrics updating every 1 second**
✅ **Logs streaming every 500ms**
✅ **Can search and filter data in Portal26**
✅ **Test ID searches return correct traces**

---

## Reference Information

### Service Details
- **Service Name**: ai-agent
- **Project**: agentic-ai-integration-490716
- **Region**: us-central1
- **URL**: https://ai-agent-961756870884.us-central1.run.app

### Portal26 Configuration
- **OTLP Endpoint**: https://otel-tenant1.portal26.in:4318
- **Tenant ID**: tenant1
- **User ID**: relusys
- **Auth**: Basic dGl0YW5pYW06aGVsbG93b3JsZA==

### Telemetry Configuration
- **Traces Export**: OTLP HTTP
- **Metrics Interval**: 1000ms (1 second)
- **Logs Interval**: 500ms (0.5 seconds)
- **Protocol**: http/protobuf

---

## Support

If you encounter issues not covered in troubleshooting:

1. Check Cloud Run logs for detailed errors
2. Verify Portal26 service status
3. Test OTLP endpoints directly with `test_otel_send.py`
4. Review `OTEL_ENDPOINT_DOCUMENTATION.md` for protocol details

---

**Last Updated**: 2026-03-27
**Version**: 1.0
