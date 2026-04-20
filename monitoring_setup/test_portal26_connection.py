"""
Test Portal26 OTEL endpoint connectivity and authentication
"""
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests

load_dotenv()

ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "test-service")
HEADERS_STR = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")

print("=" * 80)
print("PORTAL26 OTEL CONNECTION TEST")
print("=" * 80)
print(f"Endpoint: {ENDPOINT}")
print(f"Service: {SERVICE_NAME}")
print("=" * 80)
print()

if not ENDPOINT:
    print("[ERROR] OTEL_EXPORTER_OTLP_ENDPOINT not set in .env")
    exit(1)

# Parse headers
headers = {"Content-Type": "application/json"}
if HEADERS_STR:
    for header in HEADERS_STR.split(','):
        if '=' in header:
            key, value = header.split('=', 1)
            headers[key.strip()] = value.strip()
            print(f"[AUTH] Using header: {key.strip()}")

print()
print("[1/3] Testing endpoint connectivity...")

try:
    # Test basic connectivity
    url = f"{ENDPOINT}/v1/logs"
    print(f"URL: {url}")

    # Create test log payload
    timestamp_ns = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000_000))

    payload = {
        "resourceLogs": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": SERVICE_NAME}},
                    {"key": "test", "value": {"stringValue": "connection_test"}}
                ]
            },
            "scopeLogs": [{
                "scope": {
                    "name": "test-script",
                    "version": "1.0.0"
                },
                "logRecords": [{
                    "timeUnixNano": timestamp_ns,
                    "severityText": "INFO",
                    "severityNumber": 9,
                    "body": {
                        "stringValue": "Portal26 connection test from GCP Pub/Sub monitor"
                    },
                    "attributes": [
                        {"key": "test.type", "value": {"stringValue": "connectivity"}},
                        {"key": "timestamp", "value": {"stringValue": datetime.now().isoformat()}}
                    ]
                }]
            }]
        }]
    }

    print()
    print("[2/3] Sending test log...")
    print(f"Payload size: {len(json.dumps(payload))} bytes")

    response = requests.post(url, json=payload, headers=headers, timeout=10)

    print()
    print("[3/3] Response received")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200] if response.text else '(empty)'}")
    print()

    if response.status_code in [200, 201, 202]:
        print("=" * 80)
        print("[SUCCESS] Portal26 connection working!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Check Portal26 dashboard for test log")
        print("2. Run: python monitor_pubsub_to_portal26.py")
        print("3. Verify Reasoning Engine logs appear in Portal26")
        print()
    else:
        print("=" * 80)
        print("[FAILED] Portal26 returned error")
        print("=" * 80)
        print()
        print("Troubleshooting:")
        print("1. Verify OTEL_EXPORTER_OTLP_ENDPOINT is correct")
        print("2. Check authentication credentials")
        print("3. Ensure endpoint is accessible from this network")
        print("4. Contact Portal26 support if issue persists")
        print()

except requests.exceptions.Timeout:
    print()
    print("=" * 80)
    print("[TIMEOUT] Could not reach Portal26 endpoint")
    print("=" * 80)
    print()
    print("Possible causes:")
    print("- Firewall blocking outbound HTTPS")
    print("- Wrong endpoint URL")
    print("- Portal26 service down")
    print()

except requests.exceptions.ConnectionError as e:
    print()
    print("=" * 80)
    print("[CONNECTION ERROR]")
    print("=" * 80)
    print(f"Error: {e}")
    print()
    print("Possible causes:")
    print("- Network connectivity issues")
    print("- Invalid endpoint URL")
    print("- DNS resolution failure")
    print()

except Exception as e:
    print()
    print("=" * 80)
    print("[ERROR]")
    print("=" * 80)
    print(f"Error: {e}")
    print()
    import traceback
    traceback.print_exc()
