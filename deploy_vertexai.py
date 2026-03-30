#!/usr/bin/env python3
"""
Deploy AI Agent to Vertex AI Reasoning Engine
"""

import os
import sys
from google.cloud import aiplatform

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"
DISPLAY_NAME = "ai-agent-reasoning-engine"

print("=" * 70)
print("Deploying AI Agent to Vertex AI Reasoning Engine")
print("=" * 70)
print()

# Initialize Vertex AI
print(f"Initializing Vertex AI...")
print(f"  Project: {PROJECT_ID}")
print(f"  Location: {LOCATION}")
print(f"  Staging Bucket: {STAGING_BUCKET}")
print()

aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

# Check if staging bucket exists
from google.cloud import storage
storage_client = storage.Client(project=PROJECT_ID)

bucket_name = f"{PROJECT_ID}-reasoning-engine"
try:
    bucket = storage_client.get_bucket(bucket_name)
    print(f"[OK] Staging bucket exists: {bucket_name}")
except:
    print(f"Creating staging bucket: {bucket_name}...")
    bucket = storage_client.create_bucket(bucket_name, location=LOCATION)
    print(f"[OK] Bucket created")

print()

# Create requirements for Reasoning Engine
requirements = [
    "google-cloud-aiplatform",
    "google-genai",
    "python-dotenv",
]

print("Dependencies:")
for req in requirements:
    print(f"  - {req}")
print()

# Deploy the agent
print("Deploying agent to Reasoning Engine...")
print()

try:
    from vertexai.preview import reasoning_engines

    # Create reasoning engine with the agent
    reasoning_engine = reasoning_engines.ReasoningEngine.create(
        reasoning_engines.LangchainAgent(
            model="gemini-1.5-flash",
            tools=[],  # Tools are defined in the agent code
            agent_executor_kwargs={"return_intermediate_steps": True},
        ),
        requirements=requirements,
        display_name=DISPLAY_NAME,
        description="AI Agent with weather and time tools",
        # Environment variables
        extra_packages=[],
    )

    print(f"[SUCCESS] Reasoning Engine deployed!")
    print()
    print(f"Resource Name: {reasoning_engine.resource_name}")
    print(f"Display Name: {reasoning_engine.display_name}")
    print()
    print("To query the agent:")
    print(f'  reasoning_engine.query(input="What is the weather in Tokyo?")')
    print()

except Exception as e:
    print(f"[ERROR] Deployment failed: {e}")
    print()
    print("Note: Vertex AI Reasoning Engine requires the preview API.")
    print("Alternative: Deploy using the agent file directly")
    print()
    import traceback
    traceback.print_exc()

print("=" * 70)
print()
print("Alternative: Use agent_vertexai.py as a Cloud Function or Cloud Run")
print("The agent code can run anywhere with Vertex AI SDK access")
print()
