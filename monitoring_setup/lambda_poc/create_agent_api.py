"""
Create Agent Builder agent via API
This will have Playground UI access
"""
from google.auth import default
from google.auth.transport.requests import Request
import requests
import json

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
PARENT = f"projects/{PROJECT_ID}/locations/{LOCATION}"

print("=" * 60)
print("Creating Agent Builder Agent via API")
print("=" * 60)
print(f"Project: {PROJECT_ID}")
print()

# Get credentials
print("[1/3] Getting credentials...")
credentials, project = default()
credentials.refresh(Request())

print(f"Authenticated as: {credentials.service_account_email if hasattr(credentials, 'service_account_email') else 'user'}")
print()

# Agent configuration
agent_config = {
    "displayName": "pubsub-lambda-monitoring-agent",
    "description": "Monitoring agent that analyzes Pub/Sub messages and forwards to AWS Lambda",
    "agentConfig": {
        "model": "gemini-2.0-flash-001",
        "instructions": """You are a GCP monitoring agent that processes Pub/Sub messages and forwards them to AWS Lambda with AI analysis.

When you receive a message:
1. Decode the base64 data if provided
2. Analyze the message for:
   - Severity level (HIGH, MEDIUM, LOW, INFO)
   - Category (error, warning, metric, performance)
   - Anomaly detection (true/false)
   - Insights and recommendations
3. Forward the enriched message to AWS Lambda
4. Report the results

Analysis Rules:
- ERROR/EXCEPTION/FAILED/CRITICAL → HIGH severity, anomaly detected
- WARNING/WARN → MEDIUM severity
- SLOW/TIMEOUT/LATENCY → MEDIUM severity, performance category
- CPU/MEMORY/DISK/METRIC → INFO severity, metric category
"""
    }
}

print("[2/3] Creating agent...")
print()

# API endpoint
url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/{PARENT}/agents"

headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers, json=agent_config, timeout=60)

    if response.status_code in [200, 201]:
        agent = response.json()
        agent_name = agent.get("name", "unknown")
        agent_id = agent_name.split("/")[-1]

        print("[OK] Agent created successfully!")
        print()
        print("=" * 60)
        print("Agent Details")
        print("=" * 60)
        print(f"Name: {agent.get('displayName')}")
        print(f"ID: {agent_id}")
        print(f"Resource: {agent_name}")
        print()
        print("Access Playground:")
        print(f"https://console.cloud.google.com/vertex-ai/agent-builder/agents/{agent_id}/playground?project={PROJECT_ID}")
        print()
        print("Test Message:")
        print('  "Analyze this: ERROR in database connection"')
        print()
        print("[3/3] Logs automatically flow to:")
        print("  Agent -> Cloud Logging -> Pub/Sub -> AWS Lambda -> Portal26")
        print()

    elif response.status_code == 404:
        print("[ERROR] Agent Builder API not available in this region")
        print()
        print("Alternative: Create manually in console")
        print(f"https://console.cloud.google.com/vertex-ai/agent-builder/agents?project={PROJECT_ID}")
        print()

    else:
        print(f"[ERROR] Failed to create agent: {response.status_code}")
        print(f"Response: {response.text}")
        print()
        print("Try creating manually in console:")
        print(f"https://console.cloud.google.com/vertex-ai/agent-builder/agents?project={PROJECT_ID}")
        print()

except Exception as e:
    print(f"[ERROR] Exception: {str(e)}")
    print()
    print("Create manually in console instead:")
    print(f"https://console.cloud.google.com/vertex-ai/agent-builder/agents?project={PROJECT_ID}")
    print()
    print("Instructions in: migrate_to_agent_builder.md")
