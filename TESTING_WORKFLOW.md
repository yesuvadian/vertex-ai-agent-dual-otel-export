# AI Agent OTEL Testing - Visual Workflow

## 🔄 Complete Testing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    START: Testing & Validation                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Choose Your Path                                       │
│                                                                  │
│  [ ] Path A: Quick Automated (2 min)                            │
│  [ ] Path B: Manual Testing (5 min)                             │
│  [ ] Path C: Comprehensive (15 min)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
         ┌───────────┐  ┌───────────┐  ┌──────────────┐
         │  Path A   │  │  Path B   │  │   Path C     │
         │ Automated │  │  Manual   │  │ Comprehensive│
         └───────────┘  └───────────┘  └──────────────┘
```

---

## 📊 Path A: Automated Testing (Recommended)

```
START
  │
  ├─> 1. Run: python run_validation.py
  │     │
  │     ├─> Checks authentication ✓
  │     ├─> Verifies deployment ✓
  │     ├─> Tests OTEL config ✓
  │     ├─> Sends test request ✓
  │     ├─> Tests OTLP endpoints ✓
  │     ├─> Checks logs ✓
  │     └─> Generates report ✓
  │
  ├─> 2. Review validation_report_*.json
  │     │
  │     └─> All tests passed?
  │           ├─ YES → Go to Portal26
  │           └─ NO  → Check troubleshooting
  │
  └─> 3. View data in Portal26
        │
        ├─> Login to https://portal26.in
        ├─> Filter by service: ai-agent
        ├─> Search for test ID from report
        └─> ✅ DONE!
```

**Time:** 2-3 minutes
**Difficulty:** Easy
**Best for:** Quick validation, daily checks

---

## 🔧 Path B: Manual Testing

```
START
  │
  ├─> 1. Test OTLP Endpoints
  │     │
  │     └─> python test_otel_send.py
  │           │
  │           ├─> Traces: 200 OK ✓
  │           ├─> Metrics: 200 OK ✓
  │           └─> Logs: 200 OK ✓
  │
  ├─> 2. Send Test Request
  │     │
  │     └─> Generate unique TEST_ID
  │           │
  │           ├─> Get auth token
  │           ├─> Send POST to /chat
  │           └─> Save TEST_ID
  │
  ├─> 3. Check Cloud Run Logs
  │     │
  │     └─> gcloud logging read ...
  │           │
  │           ├─> OTLP exporters OK? ✓
  │           └─> No export errors? ✓
  │
  └─> 4. Verify in Portal26
        │
        ├─> Login with credentials
        ├─> Apply filters
        ├─> Search for TEST_ID
        └─> ✅ DONE!
```

**Time:** 5-10 minutes
**Difficulty:** Medium
**Best for:** Learning, debugging

---

## 📚 Path C: Comprehensive Testing

```
START
  │
  ├─> PHASE 1: Deployment Verification
  │     │
  │     ├─> Check Cloud Run service status
  │     ├─> Verify environment variables
  │     ├─> Test /status endpoint
  │     └─> Test /chat endpoint
  │
  ├─> PHASE 2: OTEL Configuration
  │     │
  │     ├─> Check OTEL_TRACES_EXPORTER
  │     ├─> Check OTEL_METRICS_EXPORTER
  │     ├─> Check OTEL_LOGS_EXPORTER
  │     └─> Verify Portal26 endpoint
  │
  ├─> PHASE 3: Export Testing
  │     │
  │     ├─> Run test_otel_send.py
  │     ├─> Run verify_otel_export.py
  │     ├─> Run capture_otel_export.py
  │     └─> Verify all return 200 OK
  │
  ├─> PHASE 4: Log Analysis
  │     │
  │     ├─> Check for exporter initialization
  │     ├─> Check for export errors
  │     ├─> Verify trace creation
  │     └─> Check request/response logs
  │
  └─> PHASE 5: Portal26 Verification
        │
        ├─> Login to dashboard
        ├─> Apply resource filters
        ├─> Verify traces
        ├─> Verify metrics
        ├─> Verify logs
        └─> ✅ DONE!
```

**Time:** 15-20 minutes
**Difficulty:** Advanced
**Best for:** First-time validation, troubleshooting

---

## 🔍 Data Flow Diagram

```
┌─────────────┐
│   User      │
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│     AI Agent (Cloud Run)                │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  FastAPI App                   │    │
│  │  - Receives request            │    │
│  │  - Creates span                │    │
│  │  - Records metrics             │    │
│  │  - Logs messages               │    │
│  └────────────┬───────────────────┘    │
│               │                         │
│  ┌────────────▼───────────────────┐    │
│  │  OpenTelemetry SDK             │    │
│  │  - Traces Provider             │    │
│  │  - Metrics Provider            │    │
│  │  - Logs Provider               │    │
│  └────────────┬───────────────────┘    │
│               │                         │
│  ┌────────────▼───────────────────┐    │
│  │  OTLP Exporters                │    │
│  │  - Batch Processor             │    │
│  │  - HTTP/Protobuf               │    │
│  │  - Auth Headers                │    │
│  └────────────┬───────────────────┘    │
└───────────────┼─────────────────────────┘
                │
                │ HTTP POST
                │ Authorization: Basic ...
                │
                ▼
┌──────────────────────────────────────────┐
│  Portal26 OTLP Endpoint                  │
│  https://otel-tenant1.portal26.in:4318  │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  /v1/traces                    │ ◄───┼─── Traces
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  /v1/metrics                   │ ◄───┼─── Metrics
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  /v1/logs                      │ ◄───┼─── Logs
│  └────────────────────────────────┘     │
│                                          │
│  Returns: 200 OK {"partialSuccess":{}}  │
└──────────────────┬───────────────────────┘
                   │
                   │ Data stored
                   │
                   ▼
┌──────────────────────────────────────────┐
│  Portal26 Storage & Processing           │
│  - Time-series database                  │
│  - Index traces by service/tenant        │
│  - Aggregate metrics                     │
│  - Store logs with context              │
└──────────────────┬───────────────────────┘
                   │
                   │ Query API
                   │
                   ▼
┌──────────────────────────────────────────┐
│  Portal26 Dashboard                      │
│  https://portal26.in                     │
│                                          │
│  - View traces                           │
│  - Analyze metrics                       │
│  - Search logs                           │
│  - Create dashboards                     │
│  - Set up alerts                         │
└──────────────────────────────────────────┘
```

---

## 🧪 Testing Decision Tree

```
Need to test OTEL integration?
  │
  ├─ First time testing?
  │    │
  │    └─ YES → Use Path C (Comprehensive)
  │         │
  │         └─ Follow USER_TESTING_MANUAL.md
  │
  ├─ Quick health check?
  │    │
  │    └─ YES → Use Path A (Automated)
  │         │
  │         └─ Run: python run_validation.py
  │
  ├─ Troubleshooting issue?
  │    │
  │    └─ YES → Use Path B (Manual)
  │         │
  │         ├─ Test endpoints individually
  │         ├─ Check logs for errors
  │         └─ Isolate the problem
  │
  ├─ Need proof for stakeholders?
  │    │
  │    └─ YES → Run capture_otel_export.py
  │         │
  │         ├─ Shows HTTP 200 responses
  │         ├─ Provides test ID
  │         └─ Demonstrates in Portal26
  │
  └─ Learning how it works?
       │
       └─ YES → Start with documentation
            │
            ├─ Read README_TESTING.md
            ├─ Try TESTING_QUICK_REFERENCE.md
            └─ Study OTEL_ENDPOINT_DOCUMENTATION.md
```

---

## 📋 Validation State Machine

```
┌──────────┐
│  START   │
└────┬─────┘
     │
     ▼
┌──────────────────┐
│ Authentication   │ ───FAIL──> ┌───────────────┐
│ Check            │            │ Run:          │
└────┬─────────────┘            │ gcloud auth   │
     │                          │ login         │
     ▼ PASS                     └───────┬───────┘
┌──────────────────┐                   │
│ Deployment       │ ───FAIL──> ┌─────┴─────────┐
│ Verification     │            │ Deploy service│
└────┬─────────────┘            │ Check logs    │
     │                          └───────┬───────┘
     ▼ PASS                             │
┌──────────────────┐                   │
│ OTEL Config      │ ───FAIL──> ┌─────┴─────────┐
│ Verification     │            │ Set env vars  │
└────┬─────────────┘            │ Redeploy      │
     │                          └───────┬───────┘
     ▼ PASS                             │
┌──────────────────┐                   │
│ Endpoint         │ ───FAIL──> ┌─────┴─────────┐
│ Testing          │            │ Check Portal26│
└────┬─────────────┘            │ credentials   │
     │                          └───────┬───────┘
     ▼ PASS                             │
┌──────────────────┐                   │
│ Data             │ ───FAIL──> ┌─────┴─────────┐
│ Verification     │            │ Wait 2-3 min  │
└────┬─────────────┘            │ Check filters │
     │                          └───────┬───────┘
     ▼ PASS                             │
┌──────────────────┐                   │
│    SUCCESS!      │ <──────────────────┘
│  ✅ VALIDATED    │
└──────────────────┘
```

---

## 🎯 Quick Reference: What to Run When

### Scenario 1: Daily Health Check
```bash
python run_validation.py
```
✅ Fast, automated, comprehensive

### Scenario 2: After Deployment
```bash
# Test endpoints
python test_otel_send.py

# Verify export
python verify_otel_export.py

# Check Portal26
# (Use test ID from output)
```
✅ Confirms new deployment works

### Scenario 3: Debugging Issues
```bash
# 1. Check logs
gcloud logging read "resource.labels.service_name=ai-agent" --limit=50

# 2. Test endpoints individually
python test_otel_send.py

# 3. Send traced request
python capture_otel_export.py

# 4. Analyze results
```
✅ Isolates problems

### Scenario 4: Demo/Proof
```bash
# Generate unique test
python capture_otel_export.py

# Show:
# - HTTP 200 responses
# - Test ID
# - Portal26 dashboard with data
```
✅ Proves it works

---

## 🔗 Documentation Map

```
                    ┌─────────────────────────┐
                    │  VALIDATION_SUMMARY.md  │
                    │  (Overview & Results)   │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌──────────────────┐  ┌─────────────┐  ┌──────────────┐
    │ README_TESTING   │  │ USER_TESTING│  │   TESTING    │
    │ Quick Start      │  │   MANUAL    │  │ QUICK_REF    │
    └──────────────────┘  │ Complete    │  └──────────────┘
                          │ Guide       │
                          └──────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
            ┌─────────────┐  ┌────────┐  ┌─────────┐
            │ OTEL        │  │Testing │  │Scripts  │
            │ ENDPOINT    │  │Scripts │  │Usage    │
            │ DOCS        │  │        │  │         │
            └─────────────┘  └────────┘  └─────────┘
```

**Start with:** VALIDATION_SUMMARY.md or README_TESTING.md

---

## 📊 Success Indicators

### ✅ Green Light (All Systems Go)
- All tests pass in run_validation.py
- All endpoints return 200 OK
- No errors in Cloud Run logs
- Data visible in Portal26
- Can search by test ID

### ⚠️ Yellow Light (Needs Attention)
- Some tests pass, some fail
- Intermittent export errors
- Delayed data in Portal26
- Missing some metrics/logs

### 🔴 Red Light (Requires Action)
- Authentication failures
- Service not responding
- All endpoints returning errors
- No data in Portal26
- Export errors in logs

---

## 🎓 Learning Path Flowchart

```
┌──────────────┐
│ New to OTEL? │
└──────┬───────┘
       │
       ├─ YES ──> Read: README_TESTING.md
       │          Then: TESTING_QUICK_REFERENCE.md
       │          Run: python run_validation.py
       │
       └─ NO ───> Familiar with OTEL?
                  │
                  ├─ YES ──> Read: OTEL_ENDPOINT_DOCUMENTATION.md
                  │          Run: python test_otel_send.py
                  │          Build custom integrations
                  │
                  └─ NO ───> Read: USER_TESTING_MANUAL.md
                             Complete all 5 test phases
                             Understand architecture
```

---

## 💡 Pro Tips

### Tip 1: Save Test IDs
Every test generates a unique ID. Save them!
```bash
TEST_ID="DEMO-$(date +%s)"
# Send request with this ID
# Search Portal26 later
```

### Tip 2: Run Tests in Parallel
```bash
# Run multiple tests at once
python test_otel_send.py &
python verify_otel_export.py &
wait
```

### Tip 3: Monitor Real-Time
```bash
# Watch logs as they come in
gcloud logging tail "resource.labels.service_name=ai-agent"
```

### Tip 4: Automate in CI/CD
```yaml
# Add to your CI/CD pipeline
- name: Validate OTEL
  run: python run_validation.py
```

### Tip 5: Create Dashboards
Use the metrics in Portal26 to create:
- Request rate dashboard
- Response time distribution
- Error rate monitoring
- Agent performance tracking

---

## ✨ Summary

Follow this workflow to validate your OTEL integration:

1. **Choose a path** (A, B, or C)
2. **Run the tests**
3. **Check the results**
4. **Verify in Portal26**
5. **✅ Done!**

**All tools and documentation are ready to use!**

---

**Last Updated**: 2026-03-27
