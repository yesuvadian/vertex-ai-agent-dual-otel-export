#!/usr/bin/env python3
"""
Deploy agent to Vertex AI Agent Engine using SDK directly
"""

import vertexai
from vertexai import reasoning_engines
import os

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
DISPLAY_NAME = "ai-agent-portal26-otel"

print("=" * 80)
print("Deploying Agent to Vertex AI Agent Engine (SDK)")
print("=" * 80)
print()
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"Display Name: {DISPLAY_NAME}")
print()

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Read environment variables from adk_agent/.env
print("Loading environment variables from adk_agent/.env...")
env_vars = {}
with open("adk_agent/.env", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip()

print(f"Loaded {len(env_vars)} environment variables")
print()

# Read requirements
print("Loading requirements...")
with open("adk_agent/requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

print(f"Requirements: {requirements}")
print()

# Deploy
print("Deploying to Agent Engine...")
print("-" * 80)
print()
print("This will take 3-5 minutes (installing packages and building container)...")
print()

try:
    # Create configuration
    config = {
        "display_name": DISPLAY_NAME,
        "description": "AI Agent with OTEL traces to Portal26",
        "source_packages": ["adk_agent"],
        "entrypoint_module": "adk_agent.agent",
        "entrypoint_object": "query",
        "requirements": requirements,
        "env_vars": env_vars,
        "min_instances": 0,
        "max_instances": 10,
        "resource_limits": {
            "cpu": "1",
            "memory": "2Gi"
        },
    }

    # Deploy using reasoning engines
    print("Creating reasoning engine...")
    remote_agent = reasoning_engines.ReasoningEngine.create(
        **config
    )

    print()
    print("=" * 80)
    print("DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)
    print()

    # Get resource information
    resource_name = remote_agent.resource_name
    print(f"Resource Name: {resource_name}")
    print(f"Display Name: {DISPLAY_NAME}")
    print()

    # Extract resource ID
    resource_id = resource_name.split("/")[-1]
    print(f"Resource ID: {resource_id}")
    print()

    # Test the agent
    print("Testing deployed agent...")
    print("-" * 80)

    test_query = "What is the weather in Tokyo?"
    print(f"Query: {test_query}")

    response = remote_agent.query(input=test_query)
    print(f"Response: {response}")
    print()

    # Usage instructions
    print("=" * 80)
    print("HOW TO USE THE DEPLOYED AGENT")
    print("=" * 80)
    print()
    print("Python SDK:")
    print(f"""
import vertexai
from vertexai import reasoning_engines

vertexai.init(project="{PROJECT_ID}", location="{LOCATION}")
agent = reasoning_engines.ReasoningEngine("{resource_name}")

response = agent.query(input="What is the weather in Tokyo?")
print(response)
""")

    print()
    print("View in Portal26:")
    print("-" * 80)
    print("URL: https://portal26.in")
    print("Login: titaniam / helloworld")
    print("Filter: service=ai-agent-engine, tenant=tenant1")
    print()

except Exception as e:
    print()
    print("=" * 80)
    print("DEPLOYMENT FAILED")
    print("=" * 80)
    print()
    print(f"Error: {str(e)}")
    print()

    import traceback
    traceback.print_exc()

    print()
    print("This might be because:")
    print("1. Agent Engine API might not support direct SDK deployment")
    print("2. ADK CLI is required for ADK agents")
    print()
    print("Alternative: Deploy to Cloud Run instead (already working)")
    print("Your Cloud Run deployment is already functional and sending")
    print("traces to Portal26!")
    print()

print("=" * 80)
