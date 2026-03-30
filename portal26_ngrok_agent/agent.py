import os
import datetime
from zoneinfo import ZoneInfo

# Initialize custom OTEL tracer provider BEFORE importing anything else
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Set up custom OTEL exporter at module load time
endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
if endpoint:
    if not endpoint.endswith("/v1/traces"):
        endpoint = endpoint.rstrip("/") + "/v1/traces"

    print(f"[OTEL_INIT] Setting custom tracer provider for endpoint: {endpoint}")

    # Create resource with service name
    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "portal26_ngrok_agent"),
        "portal26.tenant_id": "tenant1",
        "portal26.user.id": "relusys",
        "agent.type": "ngrok-local"
    })

    # Create TracerProvider with resource
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    print(f"[OTEL_INIT] Custom tracer provider set successfully!")
else:
    print("[OTEL_INIT] No OTEL_EXPORTER_OTLP_ENDPOINT set, skipping custom OTEL setup")

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
    name="portal26_ngrok_agent",
    model="gemini-2.5-flash",
    description="Agent sending telemetry to ngrok endpoint",
    instruction=(
        "You are a helpful city assistant. Use the available tools to answer "
        "questions about the current weather or time in any city the user asks about. "
        "Always use a tool - never guess or make up data."
    ),
    tools=[get_weather, get_current_time],
)
