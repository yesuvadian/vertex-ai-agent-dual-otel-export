#!/usr/bin/env python3
"""
Test the dual-export agent via REST API
"""

import subprocess
import json

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
RESOURCE_ID = "3691509684943978496"

print("=" * 80)
print("Testing Dual Export Agent via REST API")
print("=" * 80)
print()

# Get auth token
print("Getting auth token...")
result = subprocess.run(
    ["gcloud", "auth", "print-access-token"],
    capture_output=True,
    text=True,
    check=True
)
token = result.stdout.strip()
print("[OK] Token obtained")
print()

# Query the agent
url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{RESOURCE_ID}:streamQuery"

payload = {
    "input": {
        "message": "What is the weather in Tokyo?",
        "user_id": "test-user-rest-api"
    }
}

print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()
print("Sending request...")
print("-" * 80)

curl_cmd = [
    "curl", "-X", "POST",
    url,
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json",
    "-d", json.dumps(payload)
]

result = subprocess.run(curl_cmd, capture_output=True, text=True)

print()
print("Response:")
print("-" * 80)
print(result.stdout)
print()

if result.returncode == 0:
    print("=" * 80)
    print("QUERY SUCCESSFUL!")
    print("=" * 80)
    print()
    print("Telemetry should now be visible at:")
    print("  - ngrok: http://localhost:4040")
    print("  - Local files: otel-data/")
    print("  - Portal26: https://portal26.in")
    print()
else:
    print("Error:")
    print(result.stderr)

print("=" * 80)
