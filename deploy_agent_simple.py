#!/usr/bin/env python3
"""
Simple deployment to Vertex AI Agent Engine with local OTEL collector
"""

import vertexai
from vertexai.preview import reasoning_engines
import os

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
DISPLAY_NAME = "ai-agent-local-otel"
NGROK_URL = "https://tabetha-unelemental-bibulously.ngrok-free.dev"

print("=" * 80)
print("Deploying to Vertex AI Agent Engine")
print("=" * 80)
print()
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"Display Name: {DISPLAY_NAME}")
print(f"OTEL Endpoint: {NGROK_URL} (local collector)")
print()

# Initialize Vertex AI
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Define the agent as a simple Python callable
def agent_query(user_input: str) -> str:
    """Simple agent that calls Gemini"""
    import os
    from google import genai

    # Initialize Gemini
    api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
        model = "models/gemini-2.5-flash"
    else:
        client = genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
        model = "gemini-1.5-flash"

    # Define tools
    def get_weather(city: str) -> str:
        return f"Weather in {city}: 28°C, sunny"

    def get_order_status(order_id: str) -> str:
        return f"Order {order_id} is shipped"

    # Process query
    prompt = f"""
You are an AI agent with two tools:
- get_weather(city): Get weather for a city
- get_order_status(order_id): Get order status

User query: {user_input}

If the query is about weather, use get_weather.
If about order, use get_order_status.

Return JSON: {{"action": "tool_name", "input": "value"}}
Or if no tool needed: {{"response": "your answer"}}
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    import json
    try:
        result = json.loads(response.text.strip().replace("```json", "").replace("```", ""))

        if "action" in result:
            if result["action"] == "get_weather":
                tool_result = get_weather(result["input"])
                final_prompt = f"User asked: {user_input}\nTool result: {tool_result}\nGive natural response:"
                final = client.models.generate_content(model=model, contents=final_prompt)
                return final.text
            elif result["action"] == "get_order_status":
                tool_result = get_order_status(result["input"])
                final_prompt = f"User asked: {user_input}\nTool result: {tool_result}\nGive natural response:"
                final = client.models.generate_content(model=model, contents=final_prompt)
                return final.text

        return result.get("response", response.text)
    except:
        return response.text

# Requirements
requirements = [
    "google-genai>=1.0.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp-proto-http>=1.20.0",
    "opentelemetry-instrumentation>=0.40b0",
]

# Environment variables
from dotenv import load_dotenv
load_dotenv()

env_vars = {
    "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
    "GOOGLE_CLOUD_LOCATION": LOCATION,
    "GOOGLE_CLOUD_API_KEY": os.getenv("GOOGLE_CLOUD_API_KEY"),
    "OTEL_SERVICE_NAME": "ai-agent-engine",
    "OTEL_EXPORTER_OTLP_ENDPOINT": NGROK_URL,
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    "OTEL_TRACES_EXPORTER": "otlp",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==",
    "OTEL_RESOURCE_ATTRIBUTES": "portal26.user.id=relusys,portal26.tenant_id=tenant1,service.version=1.0,deployment.environment=agent-engine",
}

print("Deploying...")
print("-" * 80)
print("This will take 3-5 minutes...")
print()

try:
    # Create the reasoning engine
    remote_agent = reasoning_engines.ReasoningEngine.create(
        reasoning_engines.LangchainAgent(
            model="gemini-1.5-flash",
            model_kwargs={"temperature": 0.7},
        ),
        requirements=requirements,
        display_name=DISPLAY_NAME,
        description="AI Agent with local OTEL collector via ngrok",
        extra_packages=[],
    )

    print()
    print("=" * 80)
    print("DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)
    print()

    resource_name = remote_agent.resource_name
    resource_id = resource_name.split("/")[-1]

    print(f"Resource Name: {resource_name}")
    print(f"Resource ID: {resource_id}")
    print()

    print("Console URL:")
    print(f"https://console.cloud.google.com/vertex-ai/reasoning-engines/{resource_id}?project={PROJECT_ID}")
    print()

    # Test
    print("Testing...")
    test_query = "What is the weather in Tokyo?"
    print(f"Query: {test_query}")

    response = remote_agent.query(input={"input": test_query})
    print(f"Response: {response}")
    print()

    print("=" * 80)
    print("TELEMETRY")
    print("=" * 80)
    print()
    print("Data will be sent to:")
    print(f"  ngrok: {NGROK_URL}")
    print(f"  Local collector: localhost:4318")
    print(f"  Local files: otel-data/")
    print(f"  Portal26: https://portal26.in")
    print()
    print("View ngrok requests: http://localhost:4040")
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
    print("Note: Vertex AI Reasoning Engine API might be in preview")
    print("Check: gcloud services list --enabled | grep aiplatform")
    print()

print("=" * 80)
