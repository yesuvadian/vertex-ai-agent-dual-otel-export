#!/usr/bin/env python3
"""
Deploy AI Agent to Vertex AI Agent Engine (Official Method)
Based on: https://cloud.google.com/agent-builder/agent-engine/deploy
"""

import os
from google import genai

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
DISPLAY_NAME = "ai-agent-weather-time"
DESCRIPTION = "AI Agent providing weather and time information for cities worldwide"

print("=" * 80)
print("Deploying AI Agent to Vertex AI Agent Engine")
print("=" * 80)
print()
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"Display Name: {DISPLAY_NAME}")
print()

# Initialize Vertex AI GenAI client
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

print("Step 1: Loading local agent...")
print("-" * 80)

# Import the agent
try:
    from agent_manual import run_agent as local_agent
    print("[OK] Loaded agent_manual.run_agent")
    ENTRYPOINT_MODULE = "agent_manual"
    ENTRYPOINT_OBJECT = "run_agent"
except ImportError:
    try:
        from agent_vertexai import query as local_agent
        print("[OK] Loaded agent_vertexai.query")
        ENTRYPOINT_MODULE = "agent_vertexai"
        ENTRYPOINT_OBJECT = "query"
    except ImportError:
        print("[ERROR] Could not import agent")
        print("Make sure agent_manual.py or agent_vertexai.py exists")
        exit(1)

print()

# Step 2: Define requirements
print("Step 2: Defining package requirements...")
print("-" * 80)

requirements = [
    "google-cloud-aiplatform[agent_engines]>=1.70.0",
    "google-genai>=1.0.0",
    "requests>=2.31.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp-proto-http>=1.20.0",
]

print("Requirements:")
for req in requirements:
    print(f"  - {req}")
print()

# Step 3: Define environment variables
print("Step 3: Configuring environment variables...")
print("-" * 80)

# Read from .env file
from dotenv import load_dotenv
load_dotenv()

env_vars = {
    "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
    "GOOGLE_CLOUD_LOCATION": LOCATION,
    "OTEL_SERVICE_NAME": "ai-agent-engine",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://tabetha-unelemental-bibulously.ngrok-free.dev",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    "OTEL_TRACES_EXPORTER": "otlp",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_RESOURCE_ATTRIBUTES": "portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=agent-engine",
}

# Add secrets from Secret Manager (recommended)
api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
otel_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")

if api_key:
    env_vars["GOOGLE_CLOUD_API_KEY"] = api_key
    print("  [OK] GOOGLE_CLOUD_API_KEY configured")

if otel_headers:
    env_vars["OTEL_EXPORTER_OTLP_HEADERS"] = otel_headers
    print("  [OK] OTEL headers configured")

print(f"  Total environment variables: {len(env_vars)}")
print()

# Step 4: Configure resource limits
print("Step 4: Configuring resource limits...")
print("-" * 80)

config = {
    # Display information
    "display_name": DISPLAY_NAME,
    "description": DESCRIPTION,

    # Package requirements
    "requirements": requirements,

    # Environment variables
    "env_vars": env_vars,

    # Resource configuration
    "min_instances": 0,  # Scale to zero when idle
    "max_instances": 10,  # Max scaling
    "resource_limits": {
        "cpu": "1",  # 1, 2, 4, 6, or 8
        "memory": "2Gi"  # 1Gi to 32Gi
    },
    "container_concurrency": 3,  # 2*CPU + 1 = 3

    # Source configuration (from source files)
    "source_packages": ["."],  # Current directory
    "entrypoint_module": ENTRYPOINT_MODULE,
    "entrypoint_object": ENTRYPOINT_OBJECT,
}

print(f"  Min instances: {config['min_instances']}")
print(f"  Max instances: {config['max_instances']}")
print(f"  CPU: {config['resource_limits']['cpu']}")
print(f"  Memory: {config['resource_limits']['memory']}")
print(f"  Container concurrency: {config['container_concurrency']}")
print()

# Step 5: Deploy
print("Step 5: Deploying to Vertex AI Agent Engine...")
print("-" * 80)
print()
print("This may take 3-5 minutes (installing packages and building container)...")
print()

try:
    # Create the remote agent
    remote_agent = client.agent_engines.create(config=config)

    print()
    print("=" * 80)
    print("DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)
    print()

    # Get resource information
    resource_name = remote_agent.api_resource.name
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
    print("-" * 80)
    print(f"""
from google import genai

client = genai.Client(vertexai=True, project="{PROJECT_ID}", location="{LOCATION}")
remote_agent = client.agent_engines.get("{resource_id}")

response = remote_agent.query(input="What is the weather in Tokyo?")
print(response)
""")

    print()
    print("REST API:")
    print("-" * 80)
    print(f"""
curl -X POST \\
  "https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{resource_id}:query" \\
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \\
  -H "Content-Type: application/json" \\
  -d '{{"input": "What is the weather in Tokyo?"}}'
""")

    print()
    print("Google Cloud Console:")
    print("-" * 80)
    print(f"https://console.cloud.google.com/vertex-ai/agent-engines/{resource_id}?project={PROJECT_ID}")
    print()

    # Monitoring
    print("=" * 80)
    print("MONITORING & OBSERVABILITY")
    print("=" * 80)
    print()
    print("1. Cloud Logging:")
    print(f"   gcloud logging read 'resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND resource.labels.resource_id=\"{resource_id}\"' --limit=50")
    print()
    print("2. Portal26 Dashboard:")
    print("   URL: https://portal26.in")
    print("   Filter: service.name=ai-agent-engine, tenant_id=tenant1")
    print()
    print("3. Cloud Console:")
    print(f"   https://console.cloud.google.com/logs/query?project={PROJECT_ID}")
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
    print("Troubleshooting:")
    print("-" * 80)
    print("1. Verify Vertex AI API is enabled:")
    print("   gcloud services enable aiplatform.googleapis.com")
    print()
    print("2. Check IAM permissions:")
    print("   Your account needs 'Vertex AI User' role")
    print()
    print("3. Verify agent code:")
    print("   python agent_vertexai.py \"test query\"")
    print()
    print("4. Check quota limits in your project")
    print()

    exit(1)

print("=" * 80)
print()
