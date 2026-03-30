#!/usr/bin/env python3
"""
Send a test request to AI agent and generate a unique trace that can be verified in Portal26
"""

import requests
import time
import uuid

# Configuration
AI_AGENT_URL = "https://ai-agent-961756870884.us-central1.run.app"
TEST_ID = f"test-{int(time.time())}-{str(uuid.uuid4())[:8]}"

print("=" * 70)
print("Sending Test Request to AI Agent")
print("=" * 70)
print(f"\nTest ID: {TEST_ID}")
print(f"AI Agent URL: {AI_AGENT_URL}")
print(f"Portal26 OTLP Endpoint: https://otel-tenant1.portal26.in:4318")
print(f"Tenant: tenant1")
print(f"User: relusys")
print()

# Get auth token
import subprocess
try:
    token_result = subprocess.run(
        ["gcloud", "auth", "print-identity-token"],
        capture_output=True,
        text=True,
        timeout=10
    )
    token = token_result.stdout.strip()
    if not token:
        print("[ERROR] Failed to get auth token. Using public endpoint...")
        token = None
except Exception as e:
    print(f"[ERROR] Failed to get auth token: {e}")
    token = None

# Send test request
headers = {
    "Content-Type": "application/json"
}
if token:
    headers["Authorization"] = f"Bearer {token}"

test_message = f"TEST TRACE {TEST_ID}: What is the weather in Tokyo?"

payload = {
    "message": test_message
}

print(f"Sending request with message:")
print(f"  '{test_message}'")
print()

start_time = time.time()

try:
    response = requests.post(
        f"{AI_AGENT_URL}/chat",
        headers=headers,
        json=payload,
        timeout=30
    )

    elapsed = time.time() - start_time

    print(f"Response Status: {response.status_code}")
    print(f"Response Time: {elapsed:.2f}s")
    print(f"Response Body: {response.text[:500]}")
    print()

    if response.status_code == 200:
        print("[SUCCESS] Request completed successfully!")
        print()
        print("=" * 70)
        print("Trace Data Sent to Portal26")
        print("=" * 70)
        print()
        print("This request generated the following telemetry:")
        print("  - Traces: HTTP request span + agent execution span")
        print("  - Metrics: agent_requests_total, agent_response_time_seconds")
        print("  - Logs: Request received, agent processing, response sent")
        print()
        print("To verify in Portal26:")
        print(f"  1. Filter by service: 'ai-agent'")
        print(f"  2. Filter by tenant: 'tenant1'")
        print(f"  3. Search for message containing: '{TEST_ID}'")
        print(f"  4. Time range: Last 5 minutes")
        print()
        print("Expected trace attributes:")
        print(f"  - user.message: {test_message}")
        print(f"  - agent.success: true")
        print(f"  - agent_mode: manual")
        print(f"  - portal26.user.id: relusys")
        print(f"  - portal26.tenant_id: tenant1")
        print()
    else:
        print(f"[ERROR] Request failed with status {response.status_code}")

except Exception as e:
    print(f"[ERROR] Request failed: {e}")

print("=" * 70)
