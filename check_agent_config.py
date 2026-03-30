#!/usr/bin/env python3
"""
Check if we can view/update agent configuration
"""

import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print("=" * 80)
print("Checking Agent Configuration")
print("=" * 80)
print()

# Get the latest agent
resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/6317108267700977664"
agent = reasoning_engines.ReasoningEngine(resource_name)

print(f"Agent: {agent.display_name}")
print(f"Resource ID: {agent.resource_name.split('/')[-1]}")
print()

# Check what's available
print("Agent attributes:")
print("-" * 80)
for attr in ['display_name', 'resource_name', 'create_time', 'update_time', 'gca_resource', 'to_dict']:
    if hasattr(agent, attr):
        try:
            value = getattr(agent, attr)
            if callable(value):
                print(f"  {attr}(): callable method")
            else:
                print(f"  {attr}: {value}")
        except:
            print(f"  {attr}: <error accessing>")

print()
print("GCA Resource (full configuration):")
print("-" * 80)
try:
    import json
    gca = agent.gca_resource
    print(json.dumps(str(gca), indent=2))
except Exception as e:
    print(f"Error: {e}")

print()
print("Update method:")
print("-" * 80)
if hasattr(agent, 'update'):
    print("agent.update() exists - checking signature...")
    import inspect
    try:
        sig = inspect.signature(agent.update)
        print(f"Signature: {sig}")
    except:
        print("Could not get signature")
else:
    print("No update method available")

print()
print("=" * 80)
