#!/usr/bin/env python3
"""
Test querying a ReasoningEngine agent
"""

import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print("=" * 80)
print("Testing ReasoningEngine Query")
print("=" * 80)
print()

# Get an existing agent
resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/6317108267700977664"
agent = reasoning_engines.ReasoningEngine(resource_name)

print(f"Agent: {agent.display_name}")
print()

# Create a session
print("Creating session...")
session = agent.create_session(user_id="test-user-123")
print(f"Session ID: {session['id']}")
print()

# Try different methods to query
print("Attempting to query agent...")
print("-" * 80)

# Method 1: Try calling the agent directly with operation_schemas
try:
    print("\n1. Checking operation_schemas...")
    schemas = agent.operation_schemas()
    print(f"Operation schemas: {schemas}")

    if schemas:
        # Try to call the operation
        for schema_name in schemas:
            print(f"\nTrying operation: {schema_name}")
            try:
                # Call the operation
                result = getattr(agent, schema_name)(input="What is the weather in Tokyo?")
                print(f"Result: {result}")
                break
            except Exception as e:
                print(f"Error with {schema_name}: {e}")
except Exception as e:
    print(f"Error getting schemas: {e}")

# Method 2: Try execution_api_client.query_reasoning_engine directly
print("\n2. Using execution_api_client.query_reasoning_engine...")
try:
    from google.cloud.aiplatform_v1beta1.types import QueryReasoningEngineRequest

    request = QueryReasoningEngineRequest(
        name=resource_name,
        input={"input": "What is the weather in Tokyo?"}
    )

    response = agent.execution_api_client.query_reasoning_engine(request=request)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
