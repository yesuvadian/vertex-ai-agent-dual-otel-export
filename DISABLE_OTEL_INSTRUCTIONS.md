# How to Completely Disable OTEL (Without Portal26)

**Date**: 2026-04-10

If you want to prevent YOUR systems from sending telemetry WITHOUT contacting Portal26:

---

## Option 1: Use Invalid Endpoint (Recommended)

Change all OTEL_EXPORTER_OTLP_ENDPOINT to invalid/localhost:

```bash
# In all .env files, change:
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318

# To:
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:9999
# or
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:9999
```

**Effect**: Telemetry will fail to send (connection refused)

---

## Option 2: Use Empty Credentials

```bash
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic INVALID_CREDENTIALS
```

**Effect**: Portal26 will reject with 401 Unauthorized

---

## Option 3: Disable Exporters

```bash
OTEL_TRACES_EXPORTER=none
OTEL_LOGS_EXPORTER=none  
OTEL_METRICS_EXPORTER=none
```

**Effect**: OTEL SDK won't export anything

---

## Files to Update:

1. ✅ `C:\Yesu\ai_agent_projectgcp\portal26_otel_agent\.env.DISABLED` (already disabled)
2. ✅ `C:\Yesu\gcpai_agent_project\.env.DISABLED` (already disabled)
3. ✅ `C:\Yesu\gcpai_agent_project\.env.local.DISABLED` (already disabled)
4. ⚠️  `C:\Yesu\agentgov\.env` (STILL ACTIVE - needs update)

---

## Important:

❌ **This does NOT stop the mystery "relusys" source**  
❌ **Only stops YOUR future deployments**  
✅ **Provides extra safety layer**  
✅ **Works until you can rotate with Portal26**

The mystery source will continue until Portal26 rotates credentials server-side.
