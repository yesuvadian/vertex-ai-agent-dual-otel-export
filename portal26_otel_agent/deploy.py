"""
Deploy portal26_otel_agent with full telemetry (traces, metrics, logs + content capture)
"""
import os
from dotenv import load_dotenv
import vertexai
from vertexai.preview import reasoning_engines

# Load environment variables
load_dotenv()

# Initialize Vertex AI
project = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("GOOGLE_CLOUD_LOCATION")

vertexai.init(
    project=project,
    location=location,
    staging_bucket=f"gs://{project}-staging"
)

# Import the agent from agent.py
from agent import root_agent

# Wrapper to provide query() method for Reasoning Engine
class AgentWrapper:
    def __init__(self, agent):
        self.agent = agent

    def query(self, *, user_input: str):
        """Query method required by ReasoningEngine"""
        return self.agent.run_live(user_input=user_input)

print("=" * 80)
print("DEPLOYING PORTAL26_OTEL_AGENT")
print("=" * 80)
print()

print("Configuration:")
print(f"  Agent Name: {root_agent.name}")
print(f"  Service Name: {os.environ.get('OTEL_SERVICE_NAME')}")
print(f"  Tenant ID: {os.environ.get('PORTAL26_TENANT_ID')}")
print(f"  User ID: {os.environ.get('PORTAL26_USER_ID')}")
print(f"  Portal26 Endpoint: {os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')}")
print(f"  Content Capture: {os.environ.get('OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT')}")
print()

print("Deploying agent to Vertex AI Reasoning Engine...")
print()

# Deploy the agent using Vertex AI
try:
    wrapped_agent = AgentWrapper(root_agent)

    reasoning_engine = reasoning_engines.ReasoningEngine.create(
        wrapped_agent,
        requirements=[
            "google-cloud-aiplatform[reasoningengine,langchain]",
            "opentelemetry-api",
            "opentelemetry-sdk",
            "opentelemetry-instrumentation",
            "opentelemetry-exporter-otlp-proto-http",
        ],
    )

    print()
    print("=" * 80)
    print("DEPLOYMENT SUCCESSFUL")
    print("=" * 80)
    print(f"Agent Name: {root_agent.name}")
    print(f"Agent ID: {reasoning_engine.resource_name}")
    print()
    print("Test in Console Playground:")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    agent_id = reasoning_engine.resource_name.split('/')[-1]
    print(f"  https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/{location}/agent-engines/{agent_id}/playground?project={project}")
    print()
    print("Query endpoint:")
    print(f"  {reasoning_engine.resource_name}:query")
    print()

except Exception as e:
    print()
    print("=" * 80)
    print("DEPLOYMENT FAILED")
    print("=" * 80)
    print(f"Error: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
