"""
Test script to invoke Vertex AI Reasoning Engine and generate telemetry
This will trigger logs to flow into the GCP log sink and Pub/Sub topic
"""
import vertexai
from vertexai.preview import reasoning_engines
import requests
import google.auth
from google.auth.transport.requests import Request

# Configuration - use the correct project from the resource name
PROJECT_ID = "961756870884"  # From resource name: projects/961756870884/...
LOCATION = "us-central1"
REASONING_ENGINE_ID = "6010661182900273152"

print("=" * 80)
print("TESTING VERTEX AI REASONING ENGINE")
print("=" * 80)
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"Reasoning Engine ID: {REASONING_ENGINE_ID}")
print()

# Initialize Vertex AI
print("[1/4] Initializing Vertex AI...")
vertexai.init(project=PROJECT_ID, location=LOCATION)
print("[OK]")
print()

# Get authentication credentials
print("[2/4] Getting authentication credentials...")
try:
    credentials, project = google.auth.default()
    credentials.refresh(Request())
    access_token = credentials.token
    print("[OK]")
except Exception as e:
    print(f"[ERROR] Authentication failed: {e}")
    exit(1)

print()

# Construct API endpoint
# The Reasoning Engine is invoked via REST API
api_endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}:query"

print(f"[3/5] API Endpoint: {api_endpoint}")
print()

# Test queries
print("[4/5] Sending test queries...")
print("-" * 80)

# First, create a session
session_endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}:createSession"

print("\nStep 1: Creating session...")
try:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    session_payload = {
        "input": {}  # Empty input for session creation
    }

    session_response = requests.post(session_endpoint, json=session_payload, headers=headers)

    if session_response.status_code == 200:
        session_result = session_response.json()
        print(f"[SUCCESS] Session created")
        print(f"Session response: {session_result}")
        session_id = session_result.get("output", {}).get("session_id")
        print(f"Session ID: {session_id}")
    else:
        print(f"[ERROR] Status: {session_response.status_code}")
        print(f"Response: {session_response.text}")
        print("\nNote: The Reasoning Engine received the request (generating telemetry)")
except Exception as e:
    print(f"[ERROR] Session creation failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("\nStep 2: Listing sessions to generate more telemetry...")
try:
    list_endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}:listSessions"

    list_response = requests.post(list_endpoint, json={"input": {}}, headers=headers)

    if list_response.status_code == 200:
        list_result = list_response.json()
        print(f"[SUCCESS] Listed sessions")
        print(f"Response: {list_result}")
    else:
        print(f"[INFO] Status: {list_response.status_code}")
        print(f"Response: {list_response.text}")
        print("\nNote: The Reasoning Engine received the request (generating telemetry)")
except Exception as e:
    print(f"[ERROR] List sessions failed: {e}")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print()
print("Next steps:")
print("  1. Wait 1-2 minutes for logs to propagate to GCP")
print("  2. Run the Pub/Sub monitor:")
print("     cd portal26_otel_agent")
print("     python monitor_pubsub.py")
print()
print("  3. Or check Cloud Trace:")
print("     python gcp_traces_agent_client/view_traces.py --limit 10")
print()
print("  4. Or check combined logs:")
print("     cd portal26_otel_agent")
print("     export USE_GCP_TRACES=true")
print("     python pull_agent_logs.py")
print()
