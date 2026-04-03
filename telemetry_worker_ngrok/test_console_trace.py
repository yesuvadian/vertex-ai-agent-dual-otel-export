"""
Test processing trace from console prompts
"""
import requests
import json
import base64

# Trace from your Vertex AI console prompts
TRACE_ID = "7ecbf534209ff14f4ca314bda54e7da9"
PROJECT_ID = "agentic-ai-integration-490716"
ENDPOINT = "http://localhost:8082/process"

# Create log entry (simulating what Pub/Sub would send)
log_entry = {
    "insertId": "console-test-001",
    "timestamp": "2026-04-03T10:30:00.000Z",
    "severity": "INFO",
    "trace": f"projects/{PROJECT_ID}/traces/{TRACE_ID}",
    "labels": {
        "tenant_id": "console_test"
    },
    "resource": {
        "type": "aiplatform.googleapis.com/ReasoningEngine",
        "labels": {
            "project_id": PROJECT_ID,
            "reasoning_engine_id": "8081657304514035712",
            "location": "us-central1"
        }
    },
    "jsonPayload": {
        "message": "Trace from Vertex AI console prompt"
    }
}

# Encode as Pub/Sub would
data_encoded = base64.b64encode(json.dumps(log_entry).encode('utf-8')).decode('utf-8')

# Create Pub/Sub message format
pubsub_message = {
    "message": {
        "data": data_encoded,
        "messageId": "console-test-001",
        "publishTime": "2026-04-03T10:30:00.000Z",
        "attributes": {}
    },
    "subscription": "projects/test/subscriptions/test"
}

print("=" * 80)
print("Testing Trace Processing - Vertex AI Console Trace")
print("=" * 80)
print(f"Trace ID: {TRACE_ID}")
print(f"Endpoint: {ENDPOINT}")
print("=" * 80)

try:
    response = requests.post(ENDPOINT, json=pubsub_message, timeout=30)
    print(f"\n[Response Status] {response.status_code}")
    print(f"[Response Body]")
    print(json.dumps(response.json(), indent=2))

    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'success':
            print("\n" + "=" * 80)
            print("[OK] Trace processed successfully!")
            print(f"Trace ID: {result.get('trace_id')}")
            print(f"Tenant ID: {result.get('tenant_id')}")
            print("\nCheck:")
            print("1. Flask logs for processing details")
            print("2. Portal26 UI for exported trace")
            print("3. Resource attributes: portal26.user.id=relusys, portal26.tenant_id=tenant1")
            print("=" * 80)
        else:
            print("\n[ERROR] Processing failed:")
            print(result.get('error'))
    else:
        print(f"\n[ERROR] HTTP {response.status_code}")

except requests.exceptions.Timeout:
    print("\n[ERROR] Request timed out")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
