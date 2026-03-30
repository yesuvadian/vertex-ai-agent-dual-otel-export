#!/usr/bin/env python3
"""
Deploy ADK Agent to Vertex AI Agent Engine with Portal26 OTEL Integration
Based on working example: adk-agent-engine-otel-custom-collector.md
"""

import os
import subprocess

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
REGION = "us-central1"
DISPLAY_NAME = "ai-agent-portal26"
OTEL_ENDPOINT = "https://otel-tenant1.portal26.in:4318"
OTEL_HEADERS = "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="

print("=" * 80)
print("Deploying ADK Agent to Vertex AI Agent Engine")
print("=" * 80)
print()
print(f"Project: {PROJECT_ID}")
print(f"Region: {REGION}")
print(f"Portal26 OTEL Endpoint: {OTEL_ENDPOINT}")
print()

# Step 1: Create agent directory structure
print("Step 1: Setting up agent directory structure...")
print("-" * 80)

agent_dir = "adk_agent"
os.makedirs(agent_dir, exist_ok=True)

# Step 2: Create __init__.py with OTEL bootstrap
print("Step 2: Creating OTEL bootstrap in __init__.py...")

init_py_content = """# Custom OTEL exporter for Portal26
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def _add_custom_exporter():
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        print("[otel] OTEL_EXPORTER_OTLP_ENDPOINT not set - skipping")
        return

    if not endpoint.endswith("/v1/traces"):
        endpoint = endpoint.rstrip("/") + "/v1/traces"

    print("[otel] Adding custom OTLP exporter to: " + endpoint)

    try:
        provider = trace.get_tracer_provider()
        print("[otel] Provider type: " + type(provider).__name__)

        if hasattr(provider, "add_span_processor"):
            headers_str = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
            headers = {}
            if headers_str:
                for header in headers_str.split(","):
                    if "=" in header:
                        key, value = header.split("=", 1)
                        headers[key.strip()] = value.strip()

            exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers=headers
            )

            provider.add_span_processor(BatchSpanProcessor(exporter))
            print("[otel] Custom OTLP exporter registered successfully")
        else:
            print("[otel] WARNING: provider has no add_span_processor")

    except Exception as e:
        print("[otel] ERROR setting up exporter: " + str(e))
        import traceback
        traceback.print_exc()

_add_custom_exporter()

from . import agent
"""

with open(f"{agent_dir}/__init__.py", "w") as f:
    f.write(init_py_content)

print(f"[OK] Created {agent_dir}/__init__.py")

# Step 3: Copy agent.py
print("Step 3: Creating agent.py...")

agent_py_content = """import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent


def get_weather(city: str) -> dict:
    mock_data = {
        "bengaluru": "Partly cloudy, 28C. Humidity 70%.",
        "new york":  "Sunny, 22C. Light winds.",
        "london":    "Overcast, 15C. Rain expected.",
        "tokyo":     "Sunny, 28C. Clear skies.",
    }
    normalized = city.lower().strip()
    if normalized in mock_data:
        return {"status": "success", "report": mock_data[normalized]}
    return {
        "status": "error",
        "error_message": f"No weather data available for '{city}'.",
    }


def get_current_time(city: str) -> dict:
    timezone_map = {
        "bengaluru": "Asia/Kolkata",
        "new york":  "America/New_York",
        "london":    "Europe/London",
        "tokyo":     "Asia/Tokyo",
    }
    tz_name = timezone_map.get(city.lower().strip())
    if not tz_name:
        return {
            "status": "error",
            "error_message": f"Timezone not found for '{city}'.",
        }
    now = datetime.datetime.now(ZoneInfo(tz_name))
    return {
        "status": "success",
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


root_agent = Agent(
    name="city_info_agent",
    model="gemini-2.0-flash-exp",
    description="Provides weather and time information for cities worldwide.",
    instruction=(
        "You are a helpful city assistant. Use the available tools to answer "
        "questions about the current weather or time in any city the user asks about. "
        "Always use a tool - never guess or make up data."
    ),
    tools=[get_weather, get_current_time],
)
"""

with open(f"{agent_dir}/agent.py", "w") as f:
    f.write(agent_py_content)

print(f"[OK] Created {agent_dir}/agent.py")

# Step 4: Create .env file
print("Step 4: Creating .env file...")

env_content = f"""GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT={PROJECT_ID}
GOOGLE_CLOUD_LOCATION={REGION}
OTEL_EXPORTER_OTLP_ENDPOINT={OTEL_ENDPOINT}
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_HEADERS={OTEL_HEADERS}
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
OTEL_SERVICE_NAME=ai-agent-engine
OTEL_PROPAGATORS=tracecontext,baggage
OTEL_RESOURCE_ATTRIBUTES=portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=agent-engine
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
"""

with open(f"{agent_dir}/.env", "w") as f:
    f.write(env_content)

print(f"[OK] Created {agent_dir}/.env")

# Step 5: Create requirements.txt
print("Step 5: Creating requirements.txt...")

requirements_content = """google-adk
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-http
opentelemetry-instrumentation-httpx
opentelemetry-instrumentation-grpc
opentelemetry-instrumentation
opentelemetry-instrumentation-fastapi
opentelemetry-instrumentation-google-genai
python-dotenv
"""

with open(f"{agent_dir}/requirements.txt", "w") as f:
    f.write(requirements_content)

print(f"[OK] Created {agent_dir}/requirements.txt")

print()
print("=" * 80)
print("Agent files created successfully!")
print("=" * 80)
print()

# Step 6: Install ADK CLI if needed
print("Step 6: Checking ADK CLI installation...")
print("-" * 80)

try:
    result = subprocess.run(["adk", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK] ADK CLI installed: {result.stdout.strip()}")
    else:
        raise Exception("ADK not installed")
except:
    print("[WARNING] ADK CLI not found. Installing...")
    print()
    print("Run: pip install google-adk")
    print()
    print("After installation, run this deployment command:")
    print()
    print(f"adk deploy agent_engine \\")
    print(f"  --project={PROJECT_ID} \\")
    print(f"  --region={REGION} \\")
    print(f'  --display_name="{DISPLAY_NAME}" \\')
    print(f"  --otel_to_cloud \\")
    print(f"  {agent_dir}")
    print()
    exit(0)

print()

# Step 7: Deploy to Agent Engine
print("Step 7: Deploying to Vertex AI Agent Engine...")
print("-" * 80)
print()
print("This will take 3-5 minutes (building container and deploying)...")
print()

deploy_command = [
    "adk", "deploy", "agent_engine",
    f"--project={PROJECT_ID}",
    f"--region={REGION}",
    f"--display_name={DISPLAY_NAME}",
    "--otel_to_cloud",
    agent_dir
]

print(f"Running: {' '.join(deploy_command)}")
print()

try:
    result = subprocess.run(deploy_command, check=True, capture_output=False, text=True)

    print()
    print("=" * 80)
    print("DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)
    print()
    print("Your agent is now deployed to Vertex AI Agent Engine")
    print("Traces will be sent to Portal26:")
    print(f"  Endpoint: {OTEL_ENDPOINT}")
    print(f"  Service: ai-agent-engine")
    print(f"  Tenant: tenant1")
    print()
    print("To test the deployed agent:")
    print()
    print("  python test_agent_engine.py")
    print()
    print("View in Cloud Console:")
    print(f"  https://console.cloud.google.com/vertex-ai/agents?project={PROJECT_ID}")
    print()
    print("View traces in Portal26:")
    print("  https://portal26.in")
    print("  Filter: service.name=ai-agent-engine, tenant_id=tenant1")
    print()

except subprocess.CalledProcessError as e:
    print()
    print("=" * 80)
    print("DEPLOYMENT FAILED")
    print("=" * 80)
    print()
    print(f"Error: {e}")
    print()
    print("Troubleshooting:")
    print("1. Verify ADK CLI is installed: pip install google-adk")
    print("2. Authenticate: gcloud auth application-default login")
    print("3. Enable Vertex AI API: gcloud services enable aiplatform.googleapis.com")
    print()
    exit(1)

print("=" * 80)
