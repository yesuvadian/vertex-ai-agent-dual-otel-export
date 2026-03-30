#!/usr/bin/env python3
"""
Live test to verify OTEL data is being exported to Portal26
This script sends real telemetry data and verifies Portal26 accepts it
"""

import requests
import json
import time
from datetime import datetime

# Portal26 OTEL Configuration
PORTAL26_ENDPOINT = "https://otel-tenant1.portal26.in:4318"
AUTH_HEADER = {"Authorization": "Basic dGl0YW5pYW06aGVsbG93b3JsZA=="}
headers = {**AUTH_HEADER, "Content-Type": "application/json"}

print("=" * 80)
print("LIVE OTEL EXPORT TEST TO PORTAL26")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Endpoint: {PORTAL26_ENDPOINT}")
print()

# Generate unique test ID
test_id = f"LIVE-OTEL-{int(time.time())}"
trace_id = f"{int(time.time()):032x}"
span_id = f"{int(time.time()) % 10000:016x}"

print(f"Test ID: {test_id}")
print(f"Trace ID: {trace_id}")
print(f"Span ID: {span_id}")
print()

# Test 1: Send Trace Data
print("=" * 80)
print("TEST 1: SENDING TRACE TO PORTAL26")
print("=" * 80)

trace_payload = {
    "resourceSpans": [{
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": "ai-agent"}},
                {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
                {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}},
                {"key": "service.version", "value": {"stringValue": "1.0"}},
                {"key": "deployment.environment", "value": {"stringValue": "production"}},
                {"key": "test.id", "value": {"stringValue": test_id}}
            ]
        },
        "scopeSpans": [{
            "scope": {"name": "ai-agent-test"},
            "spans": [{
                "traceId": trace_id,
                "spanId": span_id,
                "name": "test_agent_chat",
                "kind": 1,
                "startTimeUnixNano": int(time.time() * 1e9),
                "endTimeUnixNano": int((time.time() + 2) * 1e9),
                "attributes": [
                    {"key": "user.message", "value": {"stringValue": f"{test_id}: Test OTEL export"}},
                    {"key": "agent.success", "value": {"boolValue": True}},
                    {"key": "agent_mode", "value": {"stringValue": "manual"}},
                    {"key": "test.type", "value": {"stringValue": "live_export_verification"}}
                ],
                "status": {"code": 1}
            }]
        }]
    }]
}

print(f"Sending to: {PORTAL26_ENDPOINT}/v1/traces")
print(f"Payload size: {len(json.dumps(trace_payload))} bytes")
print()

try:
    response = requests.post(
        f"{PORTAL26_ENDPOINT}/v1/traces",
        headers=headers,
        json=trace_payload,
        timeout=15,
        verify=True
    )

    print(f"HTTP Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    print(f"Response Headers: {dict(response.headers)}")

    if response.status_code in [200, 201, 202, 204]:
        print()
        print("[SUCCESS] Trace data accepted by Portal26!")
        trace_success = True
    else:
        print()
        print(f"[ERROR] Unexpected status code: {response.status_code}")
        trace_success = False

except requests.exceptions.RequestException as e:
    print(f"[ERROR] Request failed: {e}")
    trace_success = False

print()

# Test 2: Send Metric Data
print("=" * 80)
print("TEST 2: SENDING METRICS TO PORTAL26")
print("=" * 80)

metric_payload = {
    "resourceMetrics": [{
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": "ai-agent"}},
                {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
                {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}},
                {"key": "test.id", "value": {"stringValue": test_id}}
            ]
        },
        "scopeMetrics": [{
            "scope": {"name": "ai-agent-test"},
            "metrics": [{
                "name": "agent_requests_total",
                "description": "Test metric for OTEL export verification",
                "sum": {
                    "dataPoints": [{
                        "timeUnixNano": int(time.time() * 1e9),
                        "asInt": 1,
                        "attributes": [
                            {"key": "test.id", "value": {"stringValue": test_id}}
                        ]
                    }],
                    "aggregationTemporality": 2,
                    "isMonotonic": True
                }
            }]
        }]
    }]
}

print(f"Sending to: {PORTAL26_ENDPOINT}/v1/metrics")
print(f"Payload size: {len(json.dumps(metric_payload))} bytes")
print()

try:
    response = requests.post(
        f"{PORTAL26_ENDPOINT}/v1/metrics",
        headers=headers,
        json=metric_payload,
        timeout=15
    )

    print(f"HTTP Status: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code in [200, 201, 202, 204]:
        print()
        print("[SUCCESS] Metric data accepted by Portal26!")
        metric_success = True
    else:
        print()
        print(f"[ERROR] Unexpected status code: {response.status_code}")
        metric_success = False

except requests.exceptions.RequestException as e:
    print(f"[ERROR] Request failed: {e}")
    metric_success = False

print()

# Test 3: Send Log Data
print("=" * 80)
print("TEST 3: SENDING LOGS TO PORTAL26")
print("=" * 80)

log_payload = {
    "resourceLogs": [{
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": "ai-agent"}},
                {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
                {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}},
                {"key": "test.id", "value": {"stringValue": test_id}}
            ]
        },
        "scopeLogs": [{
            "scope": {"name": "ai-agent-test"},
            "logRecords": [{
                "timeUnixNano": int(time.time() * 1e9),
                "severityNumber": 9,
                "severityText": "INFO",
                "body": {
                    "stringValue": f"Test log message - {test_id}: OTEL export verification test"
                },
                "attributes": [
                    {"key": "test.id", "value": {"stringValue": test_id}},
                    {"key": "test.type", "value": {"stringValue": "live_export_verification"}}
                ],
                "traceId": trace_id,
                "spanId": span_id
            }]
        }]
    }]
}

print(f"Sending to: {PORTAL26_ENDPOINT}/v1/logs")
print(f"Payload size: {len(json.dumps(log_payload))} bytes")
print()

try:
    response = requests.post(
        f"{PORTAL26_ENDPOINT}/v1/logs",
        headers=headers,
        json=log_payload,
        timeout=15
    )

    print(f"HTTP Status: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code in [200, 201, 202, 204]:
        print()
        print("[SUCCESS] Log data accepted by Portal26!")
        log_success = True
    else:
        print()
        print(f"[ERROR] Unexpected status code: {response.status_code}")
        log_success = False

except requests.exceptions.RequestException as e:
    print(f"[ERROR] Request failed: {e}")
    log_success = False

print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"Test ID: {test_id}")
print(f"Trace ID: {trace_id}")
print()
print(f"Traces Export:  {'[SUCCESS]' if trace_success else '[FAILED]'}")
print(f"Metrics Export: {'[SUCCESS]' if metric_success else '[FAILED]'}")
print(f"Logs Export:    {'[SUCCESS]' if log_success else '[FAILED]'}")
print()

if trace_success and metric_success and log_success:
    print("=" * 80)
    print("[VERIFIED] ALL OTEL DATA SUCCESSFULLY POSTED TO PORTAL26!")
    print("=" * 80)
    print()
    print("You can verify this data in Portal26 dashboard:")
    print(f"  - Search for test ID: {test_id}")
    print(f"  - Trace ID: {trace_id}")
    print(f"  - Service: ai-agent")
    print(f"  - Tenant: tenant1")
    print(f"  - User: relusys")
    print()
else:
    print("[WARNING] Some exports failed - check errors above")
    print()
