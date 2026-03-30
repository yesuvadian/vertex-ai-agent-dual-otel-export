#!/usr/bin/env python3
"""
Test deployed ADK Agent on Vertex AI Agent Engine
"""

import vertexai
from vertexai import agent_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

print("=" * 70)
print("Testing Deployed Agent on Vertex AI Agent Engine")
print("=" * 70)
print()

# List all agents
print("Listing all deployed agents...")
print("-" * 70)

try:
    agents = agent_engines.list()
    print(f"Found {len(agents)} agent(s):")
    print()

    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent.display_name}")
        print(f"   Resource: {agent.resource_name}")
        print(f"   Created: {agent.create_time}")
        print()

    if not agents:
        print("[WARNING] No agents found. Deploy first:")
        print("  python deploy_adk_agent_engine.py")
        exit(1)

    # Use the most recent agent
    agent = agents[0]
    print(f"Testing agent: {agent.display_name}")
    print(f"Resource ID: {agent.resource_name.split('/')[-1]}")
    print()

except Exception as e:
    print(f"[ERROR] Failed to list agents: {e}")
    print()
    print("Make sure:")
    print("1. Vertex AI API is enabled")
    print("2. You have proper permissions")
    print("3. An agent is deployed")
    exit(1)

# Test queries
print("=" * 70)
print("Running Test Queries")
print("=" * 70)
print()

test_queries = [
    "What is the weather in Tokyo?",
    "What time is it in New York?",
    "Tell me about the weather in London",
]

for i, query in enumerate(test_queries, 1):
    print(f"Query {i}/{len(test_queries)}: {query}")
    print("-" * 70)

    try:
        # Query the agent
        response = agent.query(input=query)

        print(f"Response: {response}")
        print()

    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        print()

print("=" * 70)
print("Test Complete!")
print("=" * 70)
print()
print("Check Portal26 for traces:")
print("  URL: https://portal26.in")
print("  Login: titaniam / helloworld")
print("  Filter: service.name=ai-agent-engine, tenant_id=tenant1")
print()

# Check agent environment variables
print("=" * 70)
print("Agent Configuration")
print("=" * 70)
print()

try:
    # Get agent resource details
    agent_resource = agent.gca_resource

    print("Environment Variables:")
    if hasattr(agent_resource, 'environment_variables'):
        for key in sorted(agent_resource.environment_variables.keys()):
            value = agent_resource.environment_variables[key]
            # Hide sensitive values
            if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key or 'AUTH' in key:
                value = '***HIDDEN***'
            print(f"  {key}: {value}")
    print()

except Exception as e:
    print(f"Could not retrieve agent config: {e}")
    print()

print("=" * 70)
