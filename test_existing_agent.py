#!/usr/bin/env python3
"""
Test existing Vertex AI Agent Engine with local OTEL collector
"""

import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"

# Your agent resource IDs from the console
AGENTS = {
    "ai-agent-portal26": "6317108267700977664",
    "ai-agent-portal26-otel-latest": "8818294910751866880",
    "ai-agent-portal26-otel-2": "8206368311382900736",
    "ai-agent-portal26-otel-3": "5441158140177416192",
    "ai-agent-portal26-otel-4": "4812905992159232000",
    "city-info-agent": "2818625545594470400",
}

print("=" * 80)
print("Testing Existing Vertex AI Agent Engines")
print("=" * 80)
print()
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print()

# Initialize Vertex AI
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print("Available Agents:")
print("-" * 80)
for name, resource_id in AGENTS.items():
    print(f"  {name}: {resource_id}")
print()

# Test the latest agent
print("Testing: ai-agent-portal26 (latest)")
print("-" * 80)

try:
    # Get the agent
    resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENTS['ai-agent-portal26']}"
    print(f"Resource: {resource_name}")
    print()

    agent = reasoning_engines.ReasoningEngine(resource_name)

    # Test queries
    test_queries = [
        "What is the weather in Tokyo?",
        "What is the weather in Paris?",
        "Check order ORDER-123"
    ]

    for query in test_queries:
        print(f"Query: {query}")
        try:
            response = agent.query(input={"input": query})
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        print()

    print("=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print()
    print("Your agent is working!")
    print()
    print("Console URL:")
    print(f"https://console.cloud.google.com/vertex-ai/reasoning-engines/{AGENTS['ai-agent-portal26']}?project={PROJECT_ID}")
    print()
    print("To see OTEL data:")
    print("  - ngrok: http://localhost:4040")
    print("  - Local files: otel-data/")
    print("  - Portal26: https://portal26.in")
    print()

except Exception as e:
    print()
    print("=" * 80)
    print("ERROR")
    print("=" * 80)
    print()
    print(f"Error: {str(e)}")
    print()

    import traceback
    traceback.print_exc()

    print()
    print("Troubleshooting:")
    print("  1. Check agent exists in console")
    print("  2. Verify resource ID is correct")
    print("  3. Check IAM permissions")
    print()

print("=" * 80)
