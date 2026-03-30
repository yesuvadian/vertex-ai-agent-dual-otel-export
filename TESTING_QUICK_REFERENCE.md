# OTEL Testing - Quick Reference Card

## 🚀 Quick Start (5 Minutes)

### 1. Send Test Request
```bash
TEST_ID="TEST-$(date +%s)"
TOKEN=$(gcloud auth print-identity-token)

curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"$TEST_ID: What is the weather in Tokyo?\"}"

echo "Test ID: $TEST_ID"
```
**Save the Test ID!**

### 2. Verify Export
```bash
python test_otel_send.py
```
**Expected**: All endpoints return `200 OK`

### 3. Check Portal26
- URL: https://portal26.in
- Login: `titaniam` / `helloworld`
- Filter: Service=`ai-agent`, Tenant=`tenant1`
- Search for your Test ID

---

## 📋 Test Scripts

| Script | Purpose | Expected Output |
|--------|---------|-----------------|
| `test_otel_send.py` | Test all 3 OTLP endpoints | All return 200 OK |
| `verify_otel_export.py` | End-to-end verification | All checks pass |
| `capture_otel_export.py` | Real-time export proof | HTTP 200 + trace ID |
| `send_test_trace.py` | Send tagged test request | 200 OK + test ID |

---

## ✅ Validation Checklist

**Quick Checks:**
- [ ] Cloud Run service URL responds
- [ ] Status endpoint returns agent config
- [ ] Chat endpoint processes requests
- [ ] OTEL exporters in logs (3 "OK" messages)
- [ ] No export errors in logs
- [ ] Test endpoints return 200 OK
- [ ] Data visible in Portal26

---

## 🔍 Key Commands

### Check Service Status
```bash
gcloud run services describe ai-agent --region=us-central1
```

### Check OTEL Config
```bash
gcloud run services describe ai-agent --region=us-central1 \
  --format="yaml(spec.template.spec.containers[0].env)" | grep OTEL
```

### View Recent Logs
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent" \
  --limit=20 --format="value(textPayload)"
```

### Check for OTEL Initialization
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent" \
  --limit=50 --format="value(textPayload)" | grep telemetry
```

### Monitor Real-Time
```bash
gcloud logging tail "resource.labels.service_name=ai-agent"
```

---

## 🎯 Expected Results

### OTLP Endpoint Test
```
Status: 200
Response: {"partialSuccess":{}}
```

### Cloud Run Logs
```
[telemetry] OK OTLP trace exporter configured
[telemetry] OK OTLP metric exporter configured
[telemetry] OK OTLP log exporter configured
```

### AI Agent Response
```json
{
  "final_answer": "The weather in Tokyo is 28°C and sunny."
}
```

---

## 🔧 Quick Fixes

### Problem: 403 Forbidden
```bash
gcloud auth login
gcloud auth print-identity-token
```

### Problem: No OTEL in logs
```bash
# Redeploy
bash deploy.sh
```

### Problem: Can't see data in Portal26
- Expand time range to "Last 1 hour"
- Remove all filters
- Wait 2-3 minutes for propagation

---

## 📊 Portal26 Filters

| Field | Value |
|-------|-------|
| Service | `ai-agent` |
| Tenant | `tenant1` |
| User | `relusys` |
| Environment | `production` |

---

## 🔗 Service Information

**AI Agent URL:**
```
https://ai-agent-961756870884.us-central1.run.app
```

**Endpoints:**
- `GET /` - Service info
- `GET /status` - Agent status
- `POST /chat` - Chat with agent

**Portal26 OTLP:**
```
https://otel-tenant1.portal26.in:4318
  /v1/traces
  /v1/metrics
  /v1/logs
```

**Auth:**
```
Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==
```

---

## 📖 Full Documentation

For detailed step-by-step instructions, see:
- `USER_TESTING_MANUAL.md` - Complete testing guide
- `OTEL_ENDPOINT_DOCUMENTATION.md` - OTLP API reference
- `TESTING_GUIDE.md` - Original testing guide
