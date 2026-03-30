# AI Agent OTEL Testing - Getting Started

## 📚 Documentation Overview

This project includes complete testing documentation for validating the OpenTelemetry integration with Portal26.

### Quick Start Documents

1. **TESTING_QUICK_REFERENCE.md** ⚡
   - One-page cheat sheet
   - Essential commands
   - Quick validation steps
   - **Start here for fast testing**

2. **USER_TESTING_MANUAL.md** 📖
   - Complete step-by-step guide
   - Detailed validation procedures
   - Expected outputs for each test
   - Troubleshooting section
   - **Use for comprehensive testing**

3. **OTEL_ENDPOINT_DOCUMENTATION.md** 🔌
   - Portal26 OTLP API reference
   - Endpoint specifications
   - Data structure examples
   - **Use for API integration details**

---

## 🚀 Quick Validation (2 Minutes)

### Option 1: Automated Script

Run the automated validation script:

```bash
python run_validation.py
```

This will:
- Check all configurations
- Test all endpoints
- Send test requests
- Generate a validation report
- Provide next steps

### Option 2: Manual Quick Test

```bash
# 1. Send test request
TEST_ID="TEST-$(date +%s)"
TOKEN=$(gcloud auth print-identity-token)

curl -X POST https://ai-agent-961756870884.us-central1.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"$TEST_ID: What is the weather in Tokyo?\"}"

echo "Test ID: $TEST_ID"

# 2. Verify OTEL endpoints
python test_otel_send.py

# 3. Check Portal26 dashboard for your Test ID
```

---

## 📋 Testing Scripts

| Script | Purpose | Runtime | Output |
|--------|---------|---------|--------|
| **run_validation.py** | Full automated validation | 1-2 min | Comprehensive report |
| **test_otel_send.py** | Test OTLP endpoints | 10 sec | HTTP responses |
| **verify_otel_export.py** | End-to-end verification | 30 sec | Export confirmation |
| **capture_otel_export.py** | Real-time export proof | 15 sec | Trace ID for Portal26 |
| **send_test_trace.py** | Send tagged test request | 5 sec | Test ID |

---

## ✅ Validation Checklist

Use this for quick validation:

### Basic Checks
- [ ] Cloud Run service is running
- [ ] Can access `/status` endpoint
- [ ] Can send chat requests
- [ ] No deployment errors

### OTEL Configuration
- [ ] `OTEL_TRACES_EXPORTER=otlp` configured
- [ ] `OTEL_METRICS_EXPORTER=otlp` configured
- [ ] `OTEL_LOGS_EXPORTER=otlp` configured
- [ ] Portal26 endpoint configured
- [ ] Authentication header configured

### Export Validation
- [ ] Traces endpoint returns 200 OK
- [ ] Metrics endpoint returns 200 OK
- [ ] Logs endpoint returns 200 OK
- [ ] Cloud Run logs show "OK" for all exporters
- [ ] No export errors in logs

### Portal26 Validation
- [ ] Can access Portal26 dashboard
- [ ] Can filter by service: `ai-agent`
- [ ] Can see test traces
- [ ] Trace attributes are correct
- [ ] Metrics are updating
- [ ] Logs are streaming

---

## 🔍 Common Testing Scenarios

### Scenario 1: First-Time Validation

**Goal:** Verify everything is working after initial deployment

**Steps:**
1. Read: `TESTING_QUICK_REFERENCE.md`
2. Run: `python run_validation.py`
3. Check Portal26 dashboard
4. ✅ Done!

### Scenario 2: Troubleshooting Issues

**Goal:** Debug when something isn't working

**Steps:**
1. Read: `USER_TESTING_MANUAL.md` → Troubleshooting section
2. Check Cloud Run logs for errors
3. Run: `python test_otel_send.py` to isolate issue
4. Follow specific troubleshooting steps

### Scenario 3: Proving Export to Stakeholders

**Goal:** Demonstrate telemetry is being sent to Portal26

**Steps:**
1. Run: `python capture_otel_export.py`
2. Show HTTP 200 responses
3. Show test ID in Portal26 dashboard
4. Show trace details with attributes

### Scenario 4: Performance Testing

**Goal:** Generate load and verify telemetry under stress

**Steps:**
1. Run multiple concurrent requests:
   ```bash
   for i in {1..10}; do
     (curl -X POST ... &)
   done
   ```
2. Check Portal26 for all traces
3. Verify metrics show increased load
4. Check response time distribution

---

## 🎯 Success Criteria

Your integration is successful when:

✅ **All automated tests pass** (run_validation.py)
✅ **All OTLP endpoints return 200 OK**
✅ **No export errors in Cloud Run logs**
✅ **Test traces visible in Portal26 within 2-3 minutes**
✅ **Can search and filter by test ID**
✅ **Metrics updating every 1 second**
✅ **Logs streaming every 500ms**

---

## 📊 Key Metrics to Monitor

Once validated, monitor these in Portal26:

### Request Metrics
- **agent_requests_total**: Total requests (counter)
- **agent_response_time_seconds**: Response latency (histogram)

### Trace Attributes
- `service.name`: ai-agent
- `agent_mode`: manual
- `agent.success`: true/false
- `user.message`: Request content

### Resource Attributes
- `portal26.tenant_id`: tenant1
- `portal26.user.id`: relusys
- `deployment.environment`: production
- `service.version`: 1.0

---

## 🔗 Quick Links

### Service URLs
- **AI Agent**: https://ai-agent-961756870884.us-central1.run.app
- **Portal26**: https://portal26.in
- **OTLP Endpoint**: https://otel-tenant1.portal26.in:4318

### Google Cloud Console
- **Cloud Run**: https://console.cloud.google.com/run?project=agentic-ai-integration-490716
- **Logs**: https://console.cloud.google.com/logs/query?project=agentic-ai-integration-490716
- **Monitoring**: https://console.cloud.google.com/monitoring?project=agentic-ai-integration-490716

### Documentation
- **OTLP Spec**: https://opentelemetry.io/docs/specs/otlp/
- **OpenTelemetry**: https://opentelemetry.io/docs/

---

## 🆘 Getting Help

### Issue: Scripts fail to run

**Check dependencies:**
```bash
pip install requests opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

### Issue: Authentication errors

**Re-authenticate:**
```bash
gcloud auth login
gcloud auth application-default login
```

### Issue: Can't see data in Portal26

**Troubleshooting steps:**
1. Verify OTLP endpoints return 200 OK
2. Check Cloud Run logs for export errors
3. Expand time range in Portal26 (Last 1 hour)
4. Remove all filters and search by service name only
5. Wait 2-3 minutes for data propagation

### Issue: Want detailed debugging

**Enable debug logging:**
```bash
# Check all recent logs
gcloud logging read \
  "resource.labels.service_name=ai-agent" \
  --limit=100 \
  --format="table(timestamp,textPayload)"

# Monitor in real-time
gcloud logging tail "resource.labels.service_name=ai-agent"
```

---

## 📝 Testing Workflow

### For Developers

1. **After code changes:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT/ai-agent
   bash deploy.sh
   python run_validation.py
   ```

2. **Before committing:**
   - Run all test scripts
   - Verify no errors in logs
   - Update documentation if needed

### For QA/Testing

1. **Daily validation:**
   ```bash
   python run_validation.py
   ```
   Save report for tracking

2. **Issue reproduction:**
   - Send test request with unique ID
   - Note timestamp
   - Check Portal26 for trace
   - Check logs for errors
   - Document findings

### For Operations

1. **Health monitoring:**
   - Check Portal26 dashboards daily
   - Alert on export errors
   - Monitor request latency
   - Track error rates

2. **Incident response:**
   - Check Cloud Run logs first
   - Verify OTLP endpoints are responding
   - Check Portal26 for data gaps
   - Review recent deployments

---

## 📦 Files in This Repository

### Documentation
- `README_TESTING.md` - This file
- `USER_TESTING_MANUAL.md` - Complete testing guide
- `TESTING_QUICK_REFERENCE.md` - One-page cheat sheet
- `OTEL_ENDPOINT_DOCUMENTATION.md` - OTLP API reference
- `TESTING_GUIDE.md` - Original testing guide
- `SECURITY.md` - Security best practices

### Test Scripts
- `run_validation.py` - Automated validation suite
- `test_otel_send.py` - Test OTLP endpoints
- `verify_otel_export.py` - End-to-end verification
- `capture_otel_export.py` - Real-time export proof
- `send_test_trace.py` - Send tagged test request

### Application Code
- `app.py` - FastAPI application
- `agent_manual.py` - Manual agent implementation
- `agent_router.py` - Agent routing logic
- `telemetry.py` - OpenTelemetry configuration

### Infrastructure
- `Dockerfile` - Container definition
- `deploy.sh` / `deploy.bat` - Deployment scripts
- `terraform/` - Infrastructure as Code
- `.env` - Environment configuration (local)

---

## 🎓 Learning Path

### Beginner
1. Read `TESTING_QUICK_REFERENCE.md`
2. Run `python run_validation.py`
3. Explore Portal26 dashboard

### Intermediate
1. Read `USER_TESTING_MANUAL.md`
2. Run each test script individually
3. Understand Cloud Run logs
4. Customize test scenarios

### Advanced
1. Read `OTEL_ENDPOINT_DOCUMENTATION.md`
2. Read OpenTelemetry specification
3. Create custom spans and metrics
4. Build custom dashboards in Portal26

---

## 📈 Next Steps

After successful validation:

1. **Set up monitoring alerts** in Portal26
2. **Create dashboards** for key metrics
3. **Document custom traces** for your use cases
4. **Integrate with CI/CD** pipeline
5. **Train team** on using Portal26
6. **Set up SLOs/SLIs** based on metrics

---

## 📞 Support

For issues or questions:

1. Check troubleshooting section in `USER_TESTING_MANUAL.md`
2. Review Cloud Run logs for errors
3. Verify OTLP endpoints with `test_otel_send.py`
4. Check Portal26 documentation
5. Contact Portal26 support if needed

---

**Version**: 1.0
**Last Updated**: 2026-03-27
**Maintained by**: AI Agent Team
