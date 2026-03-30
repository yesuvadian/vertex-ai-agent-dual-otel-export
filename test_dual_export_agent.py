#!/usr/bin/env python3
"""
Test the dual-export agent
"""

import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print("=" * 80)
print("Testing Dual Export Agent")
print("=" * 80)
print()

# Get the new agent
resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/3691509684943978496"
agent = reasoning_engines.ReasoningEngine(resource_name)

print(f"Agent: {agent.display_name}")
print(f"Resource ID: {resource_name.split('/')[-1]}")
print()

# Test with stream_query
user_id = "test-user-dual-export"
message = "What is the weather in Tokyo?"

print(f"User ID: {user_id}")
print(f"Query: {message}")
print()
print("Streaming response...")
print("-" * 80)

try:
    response_stream = agent.stream_query(message=message, user_id=user_id)

    events = []
    for event in response_stream:
        events.append(event)
        print(f"Event: {event}")

    print()
    print("=" * 80)
    print("QUERY SUCCESSFUL!")
    print("=" * 80)
    print()
    print(f"Total events: {len(events)}")
    print()

    print("Telemetry should be visible at:")
    print("  - ngrok: http://localhost:4040")
    print("  - Local files: otel-data/")
    print("  - Portal26: https://portal26.in")
    print()

except Exception as e:
    print()
    print("ERROR:", e)
    import traceback
    traceback.print_exc()

print("=" * 80)
