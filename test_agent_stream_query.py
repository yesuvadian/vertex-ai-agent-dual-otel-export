#!/usr/bin/env python3
"""
Test querying a ReasoningEngine agent with stream_query
"""

import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print("=" * 80)
print("Testing ReasoningEngine with stream_query")
print("=" * 80)
print()

# Get an existing agent
resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/6317108267700977664"
agent = reasoning_engines.ReasoningEngine(resource_name)

print(f"Agent: {agent.display_name}")
print()

# Test query
user_id = "test-user-123"
message = "What is the weather in Tokyo?"

print(f"User ID: {user_id}")
print(f"Message: {message}")
print()
print("Streaming response...")
print("-" * 80)

try:
    # Stream query
    response_stream = agent.stream_query(message=message, user_id=user_id)

    # Collect all events
    events = []
    for event in response_stream:
        events.append(event)
        print(f"Event: {event}")

    print()
    print("=" * 80)
    print("QUERY SUCCESSFUL!")
    print("=" * 80)
    print()
    print(f"Total events received: {len(events)}")
    print()

    # Show final answer if available
    for event in reversed(events):
        if isinstance(event, dict) and 'content' in event:
            print(f"Final response: {event['content']}")
            break
        elif isinstance(event, str):
            print(f"Final response: {event}")
            break

except Exception as e:
    print()
    print("=" * 80)
    print("ERROR")
    print("=" * 80)
    print()
    print(f"Error: {e}")
    print()
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
