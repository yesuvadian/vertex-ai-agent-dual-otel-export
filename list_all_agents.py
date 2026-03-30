#!/usr/bin/env python3
"""
List all deployed Reasoning Engine agents
"""

import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print("=" * 80)
print("Listing All Reasoning Engine Agents")
print("=" * 80)
print()
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print()

try:
    # List all reasoning engines
    agents = reasoning_engines.ReasoningEngine.list()

    print(f"Total agents found: {len(agents)}")
    print()
    print("-" * 80)

    for i, agent in enumerate(agents, 1):
        print(f"\n[{i}] {agent.display_name}")
        print(f"    Resource ID: {agent.resource_name.split('/')[-1]}")
        print(f"    Created: {agent.create_time}")
        print(f"    Updated: {agent.update_time}")
        print(f"    Console URL: https://console.cloud.google.com/vertex-ai/reasoning-engines/{agent.resource_name.split('/')[-1]}?project={PROJECT_ID}")

    print()
    print("=" * 80)
    print()
    print("To view all agents in Console:")
    print(f"https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={PROJECT_ID}")
    print()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
