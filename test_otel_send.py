#!/usr/bin/env python3
"""Test script to manually send OTLP data to Portal26 and verify acceptance"""

import requests
import json
import time

# Portal26 configuration
ENDPOINT = "https://otel-tenant1.portal26.in:4318"
AUTH_HEADER = "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="

# Parse auth header
headers = {}
for header in AUTH_HEADER.split(","):
    if "=" in header:
        key, value = header.split("=", 1)
        headers[key.strip()] = value.strip()

headers["Content-Type"] = "application/json"

# Test 1: Send a trace
print("=" * 60)
print("Testing Portal26 OTLP Endpoints")
print("=" * 60)

trace_data = {
    "resourceSpans": [{
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": "ai-agent-test"}},
                {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
                {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}},
            ]
        },
        "scopeSpans": [{
            "spans": [{
                "traceId": "0123456789abcdef0123456789abcdef",
                "spanId": "0123456789abcdef",
                "name": "test_trace",
                "kind": 1,
                "startTimeUnixNano": int(time.time() * 1e9),
                "endTimeUnixNano": int(time.time() * 1e9) + 1000000,
                "attributes": [
                    {"key": "test.attribute", "value": {"stringValue": "manual_test"}}
                ]
            }]
        }]
    }]
}

print("\n1. Testing Traces Endpoint...")
print(f"   URL: {ENDPOINT}/v1/traces")
try:
    response = requests.post(
        f"{ENDPOINT}/v1/traces",
        headers=headers,
        json=trace_data,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200] if response.text else 'Empty (success)'}")
    if response.status_code in [200, 201, 202, 204]:
        print("   [OK] Traces endpoint accepting data!")
    else:
        print(f"   [ERROR] Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 2: Send a metric
print("\n2. Testing Metrics Endpoint...")
print(f"   URL: {ENDPOINT}/v1/metrics")

metric_data = {
    "resourceMetrics": [{
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": "ai-agent-test"}},
                {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
                {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}},
            ]
        },
        "scopeMetrics": [{
            "metrics": [{
                "name": "test_metric",
                "sum": {
                    "dataPoints": [{
                        "timeUnixNano": int(time.time() * 1e9),
                        "asInt": 42
                    }]
                }
            }]
        }]
    }]
}

try:
    response = requests.post(
        f"{ENDPOINT}/v1/metrics",
        headers=headers,
        json=metric_data,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200] if response.text else 'Empty (success)'}")
    if response.status_code in [200, 201, 202, 204]:
        print("   [OK] Metrics endpoint accepting data!")
    else:
        print(f"   [ERROR] Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 3: Send a log
print("\n3. Testing Logs Endpoint...")
print(f"   URL: {ENDPOINT}/v1/logs")

log_data = {
    "resourceLogs": [{
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": "ai-agent-test"}},
                {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
                {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}},
            ]
        },
        "scopeLogs": [{
            "logRecords": [{
                "timeUnixNano": int(time.time() * 1e9),
                "severityText": "INFO",
                "body": {"stringValue": "Test log message from manual test"}
            }]
        }]
    }]
}

try:
    response = requests.post(
        f"{ENDPOINT}/v1/logs",
        headers=headers,
        json=log_data,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200] if response.text else 'Empty (success)'}")
    if response.status_code in [200, 201, 202, 204]:
        print("   [OK] Logs endpoint accepting data!")
    else:
        print(f"   [ERROR] Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("\n[TIP] To view this data, check your Portal26 dashboard:")
print("   - Service: ai-agent-test")
print("   - Tenant: tenant1")
print("   - User: relusys")
print()
