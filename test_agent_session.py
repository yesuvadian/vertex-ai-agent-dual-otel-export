#!/usr/bin/env python3
"""
Test ReasoningEngine with session-based API
"""

import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print("=" * 80)
print("Testing ReasoningEngine with Sessions")
print("=" * 80)
print()

# Get an existing agent
resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/6317108267700977664"
agent = reasoning_engines.ReasoningEngine(resource_name)

print(f"Agent: {agent.display_name}")
print(f"Resource: {resource_name}")
print()

# Try to create a session with user_id
print("Creating session...")
try:
    session = agent.create_session(user_id="test-user-123")
    print(f"Session created: {session}")
    print()

    # Check session methods
    print("Session methods:")
    for attr in dir(session):
        if not attr.startswith("_") and callable(getattr(session, attr)):
            print(f"  - {attr}")
    print()

except Exception as e:
    print(f"Session creation failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Try execution_api_client
print("Checking execution_api_client...")
try:
    exec_client = agent.execution_api_client
    print(f"Execution client type: {type(exec_client)}")
    print("Execution client methods:")
    for attr in dir(exec_client):
        if not attr.startswith("_") and not attr.startswith("common_"):
            print(f"  - {attr}")
    print()
except Exception as e:
    print(f"Error: {e}")
    print()

print("=" * 80)
