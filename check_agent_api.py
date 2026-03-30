#!/usr/bin/env python3
"""
Check what methods are available on ReasoningEngine
"""

import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Get an existing agent
resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/6317108267700977664"
agent = reasoning_engines.ReasoningEngine(resource_name)

print("ReasoningEngine object type:", type(agent))
print("\nAvailable methods and attributes:")
print("-" * 80)

for attr in dir(agent):
    if not attr.startswith("_"):
        print(f"  {attr}")

print("\n" + "=" * 80)
print("ReasoningEngine details:")
print("=" * 80)
print(f"Resource name: {agent.resource_name}")
print(f"Display name: {getattr(agent, 'display_name', 'N/A')}")

# Try to get more info
try:
    print(f"\nAgent API Resource: {agent.api_resource}")
except:
    pass

try:
    print(f"\nAgent state: {agent.state}")
except:
    pass
