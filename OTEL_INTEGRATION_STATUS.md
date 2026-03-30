# OTEL Integration Status - Agent Engine Deployment

**Date**: 2026-03-27
**Status**: ❌ **NOT WORKING**

---

## Issue Summary

**Agent Engine deployed successfully, but OTEL traces are NOT being sent to Portal26.**

---

## Root Cause

### ProxyTracerProvider Issue

Agent Engine initializes with a `ProxyTracerProvider` that doesn't support adding custom span processors.

**Evidence from logs:**
```
[otel] Adding custom OTLP exporter to: https://otel-tenant1.portal26.in:4318/v1/traces
[otel] Provider type: ProxyTracerProvider
[otel] WARNING: provider has no add_span_processor
```

**What this means:**
- The `__init__.py` bootstrap runs too early in the initialization process
- At that point, Agent Engine hasn't initialized its real TracerProvider yet
- ProxyTracerProvider is a placeholder that doesn't have the `add_span_processor` method
- Custom exporter cannot be registered
- NO traces are sent to Portal26

---

## Attempted Solutions

### Solution 1: Bootstrap in `__init__.py` (FAILED)
**Approach**: Add custom exporter in `adk_agent/__init__.py` module initialization
**Result**: ❌ Failed - ProxyTracerProvider doesn't support add_span_processor

### Solution 2: Environment Variables Only (FAILED)
**Approach**: Set OTEL_EXPORTER_OTLP_ENDPOINT in .env
**Result**: ❌ Failed - Agent Engine ignores env var for custom exporters

### Solution 3: ADK CLI `--otel_to_cloud` Flag (PARTIAL)
**Approach**: Use `--otel_to_cloud` flag to enable telemetry
**Result**: ⚠️ Sends traces to Google Cloud Trace, not Portal26

---

## Why Working Example Doesn't Apply

The working example from `adk-agent-engine-otel-custom-collector.md` suggested the bootstrap pattern would work, but:

1. **Timing Issue**: Bootstrap runs before real TracerProvider is initialized
2. **SDK Version Differences**: Agent Engine may have changed initialization order
3. **Environment Differences**: Different Python/OTEL SDK versions may behave differently

---

## Possible Solutions to Explore

### Option 1: Delayed Exporter Registration
Register the exporter after the TracerProvider is fully initialized.

**Approach:**
```python
import atexit
from opentelemetry import trace

def register_exporter_delayed():
    import time
    time.sleep(2)  # Wait for real TracerProvider
    provider = trace.get_tracer_provider()
    if hasattr(provider, 'add_span_processor'):
        # Add custom exporter
        pass

import threading
threading.Thread(target=register_exporter_delayed, daemon=True).start()
```

**Pros**: Might catch the real TracerProvider after initialization
**Cons**: Unreliable, hacky, may miss early traces

### Option 2: Instrument ADK Agent Directly
Add tracing directly in the agent code instead of relying on auto-instrumentation.

**Approach:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Create our own TracerProvider
provider = TracerProvider()
exporter = OTLPSpanExporter(
    endpoint="https://otel-tenant1.portal26.in:4318/v1/traces",
    headers={"Authorization": "Basic ..."}
)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# Use tracer in agent code
tracer = trace.get_tracer(__name__)

def query(input: str) -> str:
    with tracer.start_as_current_span("agent.query"):
        response = root_agent.send_message(input)
        return response
```

**Pros**: Full control, guaranteed to work
**Cons**: Manual instrumentation, more code

### Option 3: OTEL Collector Sidecar
Deploy an OTEL collector that receives from Agent Engine and forwards to Portal26.

**Architecture:**
```
Agent Engine → OTLP → OTEL Collector (Cloud Run) → Portal26
```

**Pros**: Clean separation, standard OTEL pattern
**Cons**: Additional infrastructure, cost

### Option 4: Keep Cloud Run Deployment
The Cloud Run deployment already works perfectly with Portal26 OTEL.

**Approach:** Use Cloud Run as the primary deployment, skip Agent Engine OTEL issues

**Pros**: Already working, full OTEL integration
**Cons**: Not using Agent Engine managed service

### Option 5: Use Agent Engine Built-in Telemetry
Use Agent Engine's native telemetry (sent to Cloud Trace) and export from there.

**Architecture:**
```
Agent Engine → Cloud Trace → Cloud Trace Export → Portal26
```

**Pros**: Uses supported path
**Cons**: Additional setup, may lose some trace details

---

## Recommended Approach

### Short Term: Use Cloud Run ✅
The Cloud Run deployment works perfectly with Portal26 OTEL integration. Continue using it for production.

### Long Term: Investigate Agent Engine Tracing
If Agent Engine is required, explore Option 2 (Manual Instrumentation) or Option 3 (OTEL Collector Sidecar).

---

## Current Status

### Working Deployments:
✅ **Cloud Run**: Full OTEL integration to Portal26 working
❌ **Agent Engine (ADK)**: Deployed but OTEL not working

### Agent Engine Issues:
1. ❌ OTEL traces not sent to Portal26 (ProxyTracerProvider)
2. ❌ Agent invocation failing (no query method, only session APIs)
3. ⚠️ ADK CLI creates AdkApp wrapper with different API

---

## Next Steps

1. **Verify Cloud Run deployment is still working**
2. **Document Cloud Run as primary deployment**
3. **Research Agent Engine TracerProvider initialization**
4. **Consider manual instrumentation approach**
5. **Or accept Agent Engine for non-OTEL use cases**

---

## Files Reference

- **Working Cloud Run**: `deploy_cloudrun.sh`, `cloud_run_agent_otel.py`
- **Agent Engine (not working)**: `deploy_adk_agent_engine.py`, `adk_agent/`
- **Logs showing issue**: Check with `gcloud logging read` for ProxyTracerProvider warning

---

**Conclusion**: Agent Engine deployment works but OTEL integration to Portal26 does NOT work due to ProxyTracerProvider limitations. Cloud Run deployment remains the recommended approach for full OTEL integration.
