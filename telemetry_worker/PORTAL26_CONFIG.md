# Portal26 Configuration Guide

**Date:** 2026-04-03  
**Telemetry Worker:** v1.0

---

## Overview

The telemetry worker exports traces to Portal26 using OTLP/HTTP protocol with protobuf format.

**Your Portal26 Configuration:**
```
Endpoint: https://otel-tenant1.portal26.in:4318/v1/traces
Username: titaniam
Password: helloworld
Tenant: tenant1
User: relusys
```

---

## Environment Variables

### Required Variables

```bash
# Portal26 Endpoint (OTLP HTTP with port 4318)
PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318/v1/traces

# Basic Authentication
PORTAL26_USERNAME=titaniam
PORTAL26_PASSWORD=helloworld
```

### Optional Variables (OTEL Standard)

```bash
# Resource attributes added to all traces
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1

# Enable logging of user prompts
OTEL_LOG_USER_PROMPTS=1

# Protocol (http/protobuf is default)
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Export intervals (not used by worker, but standard)
OTEL_METRIC_EXPORT_INTERVAL=1000
OTEL_LOGS_EXPORT_INTERVAL=500

# Timeout for Portal26 requests
PORTAL26_TIMEOUT=30
```

---

## Configuration Files

### Option 1: Use `.env.portal26` (Already Created)

```bash
# Copy Portal26 config
cp .env.portal26 .env

# Run locally
python main.py
```

### Option 2: Set in Cloud Run Deployment

```bash
# Deploy with Portal26 config
gcloud run deploy telemetry-worker \
  --source . \
  --project=portal26-telemetry-prod \
  --region=us-central1 \
  --service-account=telemetry-worker@portal26-telemetry-prod.iam.gserviceaccount.com \
  --set-env-vars="PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318/v1/traces" \
  --set-env-vars="PORTAL26_USERNAME=titaniam" \
  --set-env-vars="PORTAL26_PASSWORD=helloworld" \
  --set-env-vars="OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1" \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=100
```

### Option 3: Use Secret Manager (Recommended for Production)

```bash
# Create secrets
echo -n "titaniam" | gcloud secrets create portal26-user --data-file=-
echo -n "helloworld" | gcloud secrets create portal26-pass --data-file=-

# Deploy with secrets
gcloud run deploy telemetry-worker \
  --source . \
  --project=portal26-telemetry-prod \
  --region=us-central1 \
  --service-account=telemetry-worker@portal26-telemetry-prod.iam.gserviceaccount.com \
  --set-env-vars="PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318/v1/traces" \
  --set-secrets="PORTAL26_USERNAME=portal26-user:latest,PORTAL26_PASSWORD=portal26-pass:latest" \
  --set-env-vars="OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1" \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=100
```

---

## How Resource Attributes Work

### OTEL_RESOURCE_ATTRIBUTES Variable

**Format:** `key1=value1,key2=value2`

**Your Configuration:**
```bash
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1
```

**Parsed as:**
- `portal26.user.id` = `relusys`
- `portal26.tenant_id` = `tenant1`

### Applied to Traces

These attributes are added to **every trace** sent to Portal26:

```protobuf
ResourceSpans {
  resource: {
    attributes: [
      {key: "service.name", value: "vertex-ai-agent"},
      {key: "cloud.provider", value: "gcp"},
      {key: "cloud.platform", value: "gcp_vertex_ai"},
      {key: "tenant.id", value: "tenant_abc"},           # From log entry
      {key: "project.id", value: "client-project-123"},  # From trace
      {key: "portal26.user.id", value: "relusys"},       # From OTEL_RESOURCE_ATTRIBUTES
      {key: "portal26.tenant_id", value: "tenant1"}      # From OTEL_RESOURCE_ATTRIBUTES
    ]
  }
  ...
}
```

### Portal26 Usage

In Portal26, you can:
- **Filter traces** by `portal26.user.id=relusys`
- **Group by tenant** using `portal26.tenant_id`
- **Create dashboards** per user or tenant
- **Set up alerts** for specific users/tenants

---

## OTLP Export Format

### Request Details

**Method:** `POST`  
**URL:** `https://otel-tenant1.portal26.in:4318/v1/traces`  
**Content-Type:** `application/x-protobuf`  
**Authorization:** `Basic dGl0YW5pYW06aGVsbG93b3JsZA==` (base64 of `titaniam:helloworld`)  
**Custom Header:** `X-Tenant-ID: <dynamic_tenant_id>`

### Request Body

OTLP `ExportTraceServiceRequest` protobuf:
```protobuf
ExportTraceServiceRequest {
  resource_spans: [
    {
      resource: {...},
      scope_spans: [
        {
          scope: {name: "vertex-ai-telemetry", version: "1.0"},
          spans: [...]
        }
      ]
    }
  ]
}
```

---

## Dynamic vs Static Attributes

### Static Attributes (Same for All Traces)

Set via `OTEL_RESOURCE_ATTRIBUTES`:
- `portal26.user.id=relusys` (Portal26 user)
- `portal26.tenant_id=tenant1` (Portal26 tenant)

### Dynamic Attributes (Per Client/Trace)

Extracted from log entry:
- `tenant.id` - Client's tenant ID (from log labels)
- `project.id` - Client's GCP project
- `reasoning_engine.id` - Vertex AI agent ID

### Why Both?

**Portal26 attributes** identify **your Portal26 account** (relusys @ tenant1)  
**Dynamic attributes** identify **which client/tenant** the trace came from

**Example:**
```
Portal26 Account: relusys @ tenant1
Client 1: tenant_customer_a (project: customer-a-project)
Client 2: tenant_customer_b (project: customer-b-project)

Trace from Client 1:
  portal26.user.id: relusys           # Your Portal26 account
  portal26.tenant_id: tenant1         # Your Portal26 tenant
  tenant.id: tenant_customer_a        # Client's tenant
  project.id: customer-a-project      # Client's project
```

---

## Testing Portal26 Configuration

### 1. Test Endpoint Connectivity

```bash
curl -X POST https://otel-tenant1.portal26.in:4318/v1/traces \
  -H "Content-Type: application/x-protobuf" \
  -H "Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  --data-binary "@test_trace.pb"

# Expected: 200 OK or OTLP response
```

### 2. Test Worker with Portal26 Config

```bash
# Set Portal26 config
cp .env.portal26 .env

# Run worker
python main.py

# In another terminal, test with sample message
python test_local.py \
  agentic-ai-integration-490716 \
  <trace_id> \
  test_tenant

# Check logs for export success
# Expected: "Successfully exported traces for tenant test_tenant"
```

### 3. Verify in Portal26 UI

1. Login to Portal26: `https://portal26.in`
2. Navigate to traces view
3. Filter by:
   - `portal26.user.id=relusys`
   - `portal26.tenant_id=tenant1`
4. Should see traces from Vertex AI agents

---

## Multi-Tenant Support

### Portal26 Side (Static)

All traces go to same Portal26 account:
- User: `relusys`
- Tenant: `tenant1`

### Client Side (Dynamic)

Each client has unique tenant ID in traces:
- Client A: `tenant.id=client_a`
- Client B: `tenant.id=client_b`

### Querying in Portal26

```sql
-- All traces for your Portal26 account
portal26.tenant_id=tenant1

-- Traces from specific client
portal26.tenant_id=tenant1 AND tenant.id=client_a

-- Traces from specific project
portal26.tenant_id=tenant1 AND project.id=customer-project-123
```

---

## Troubleshooting

### Error: Connection refused

**Problem:** Cannot reach Portal26 endpoint  
**Check:**
- Endpoint URL correct (https://otel-tenant1.portal26.in:4318)
- Port 4318 accessible
- No firewall blocking

### Error: 401 Unauthorized

**Problem:** Invalid credentials  
**Check:**
- Username: `titaniam`
- Password: `helloworld`
- Base64 encoding correct: `dGl0YW5pYW06aGVsbG93b3JsZA==`

### Error: 400 Bad Request

**Problem:** Invalid protobuf payload  
**Check:**
- OTEL transformation working correctly
- Trace IDs are valid hex strings
- Timestamps are in nanoseconds

### Traces not appearing in Portal26

**Check:**
1. Worker logs show "Successfully exported"
2. Portal26 endpoint responding 200
3. Correct tenant_id in Portal26 filters
4. Wait a few minutes for indexing

---

## Production Deployment with Portal26 Config

```bash
#!/bin/bash
# deploy_portal26.sh

PROJECT="portal26-telemetry-prod"
SERVICE="telemetry-worker"
REGION="us-central1"

# Create secrets
echo -n "titaniam" | gcloud secrets create portal26-user --project=$PROJECT --data-file=- || true
echo -n "helloworld" | gcloud secrets create portal26-pass --project=$PROJECT --data-file=- || true

# Deploy with Portal26 configuration
gcloud run deploy $SERVICE \
  --source . \
  --project=$PROJECT \
  --region=$REGION \
  --platform=managed \
  --service-account=telemetry-worker@${PROJECT}.iam.gserviceaccount.com \
  --set-env-vars="PORTAL26_ENDPOINT=https://otel-tenant1.portal26.in:4318/v1/traces" \
  --set-secrets="PORTAL26_USERNAME=portal26-user:latest,PORTAL26_PASSWORD=portal26-pass:latest" \
  --set-env-vars="OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1" \
  --set-env-vars="OTEL_LOG_USER_PROMPTS=1" \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=100 \
  --concurrency=80 \
  --cpu=2 \
  --memory=1Gi \
  --timeout=60s

echo "Deployed with Portal26 configuration"
echo "Endpoint: https://otel-tenant1.portal26.in:4318/v1/traces"
echo "User: relusys"
echo "Tenant: tenant1"
```

---

## Summary

✓ Portal26 configuration integrated into worker  
✓ OTEL_RESOURCE_ATTRIBUTES support added  
✓ Static Portal26 attributes + dynamic client attributes  
✓ Ready to deploy with Portal26 backend  

**Your Configuration:**
- Endpoint: `https://otel-tenant1.portal26.in:4318/v1/traces`
- Auth: `titaniam:helloworld`
- User: `relusys`
- Tenant: `tenant1`

**All traces will include:**
- `portal26.user.id=relusys` (your Portal26 user)
- `portal26.tenant_id=tenant1` (your Portal26 tenant)
- `tenant.id=<client_tenant>` (client's tenant)
- `project.id=<client_project>` (client's project)
