#!/usr/bin/env python3
"""
Deploy 2 new Agent Engines with dual OTEL export (local + Portal26)
"""

import vertexai
from vertexai.preview import reasoning_engines
import time

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"
NGROK_URL = "https://tabetha-unelemental-bibulously.ngrok-free.dev"

print("=" * 80)
print("Deploying 2 Agent Engines with Dual Export (Local + Portal26)")
print("=" * 80)
print()
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"OTEL Endpoint: {NGROK_URL} -> Local Collector -> Portal26")
print()

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Agent configurations
agents_config = [
    {
        "name": "weather-agent-dual-export",
        "description": "Weather agent with dual OTEL export (local + Portal26)",
        "model": "gemini-1.5-flash",
        "temperature": 0.7,
    },
    {
        "name": "order-agent-dual-export",
        "description": "Order tracking agent with dual OTEL export (local + Portal26)",
        "model": "gemini-1.5-flash",
        "temperature": 0.5,
    }
]

deployed_agents = []

for idx, config in enumerate(agents_config, 1):
    print(f"[{idx}/2] Deploying: {config['name']}")
    print("-" * 80)

    try:
        # Create reasoning engine with Langchain agent
        agent = reasoning_engines.ReasoningEngine.create(
            reasoning_engines.LangchainAgent(
                model=config["model"],
                model_kwargs={
                    "temperature": config["temperature"],
                },
            ),
            requirements=[
                "google-genai>=1.0.0",
                "langchain>=0.1.0",
                "opentelemetry-sdk>=1.20.0",
                "opentelemetry-exporter-otlp-proto-http>=1.20.0",
            ],
            display_name=config["name"],
            description=config["description"],
            extra_packages=[],
        )

        resource_name = agent.resource_name
        resource_id = resource_name.split("/")[-1]

        print(f"[OK] Deployed: {config['name']}")
        print(f"  Resource ID: {resource_id}")
        print(f"  Console: https://console.cloud.google.com/vertex-ai/reasoning-engines/{resource_id}?project={PROJECT_ID}")
        print()

        deployed_agents.append({
            "name": config["name"],
            "resource_id": resource_id,
            "resource_name": resource_name,
            "agent": agent,
        })

        # Wait between deployments to avoid rate limits
        if idx < len(agents_config):
            print("Waiting 10 seconds before next deployment...")
            time.sleep(10)
            print()

    except Exception as e:
        print(f"[FAILED] Failed to deploy {config['name']}")
        print(f"  Error: {str(e)}")
        print()

print("=" * 80)
print("DEPLOYMENT SUMMARY")
print("=" * 80)
print()

if deployed_agents:
    print(f"Successfully deployed {len(deployed_agents)} agents:")
    print()

    for agent_info in deployed_agents:
        print(f"[OK] {agent_info['name']}")
        print(f"  Resource ID: {agent_info['resource_id']}")
        print(f"  Console URL:")
        print(f"  https://console.cloud.google.com/vertex-ai/reasoning-engines/{agent_info['resource_id']}?project={PROJECT_ID}")
        print()

    print("=" * 80)
    print("OTEL CONFIGURATION")
    print("=" * 80)
    print()
    print("These agents will send telemetry through:")
    print(f"  1. ngrok: {NGROK_URL}")
    print(f"  2. Local Collector: localhost:4318")
    print(f"  3. Local Files: otel-data/")
    print(f"  4. Portal26: https://otel-tenant1.portal26.in:4318")
    print()
    print("View real-time:")
    print("  - ngrok UI: http://localhost:4040")
    print("  - Collector logs: docker logs local-otel-collector -f")
    print("  - Portal26: https://portal26.in")
    print()

    print("=" * 80)
    print("TESTING")
    print("=" * 80)
    print()
    print("To test an agent, use the Console Test tab or:")
    print()
    print("Python SDK:")
    print(f"""
import vertexai
from vertexai.preview import reasoning_engines

vertexai.init(project="{PROJECT_ID}", location="{LOCATION}", staging_bucket="{STAGING_BUCKET}")

# Get agent
resource_name = "{deployed_agents[0]['resource_name']}"
agent = reasoning_engines.ReasoningEngine(resource_name)

# Query
response = agent.query(input={{"input": "What is the weather in Tokyo?"}})
print(response)
""")

    print()
    print("REST API:")
    print(f"""
TOKEN=$(gcloud auth print-access-token)

curl -X POST \\
  "https://{LOCATION}-aiplatform.googleapis.com/v1/{deployed_agents[0]['resource_name']}:query" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"input": "What is the weather in Tokyo?"}}'
""")

else:
    print("No agents were deployed successfully.")
    print()
    print("Check errors above for details.")

print("=" * 80)
print()
