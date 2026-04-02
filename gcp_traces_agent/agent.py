import os
import datetime
from zoneinfo import ZoneInfo

# Initialize Google Cloud Trace exporter (native GCP support)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Use Google Cloud Trace exporter
try:
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentic-ai-integration-490716")

    print(f"[OTEL_INIT] Setting up Google Cloud Trace exporter for project: {project_id}")

    # Create resource with service name
    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "gcp_traces_agent"),
        "cloud.platform": "gcp_vertex_ai",
        "cloud.provider": "gcp"
    })

    # Create TracerProvider with resource
    provider = TracerProvider(resource=resource)

    # Add Google Cloud Trace exporter
    cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)
    span_processor = BatchSpanProcessor(cloud_trace_exporter)
    provider.add_span_processor(span_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    print(f"[OTEL_INIT] Google Cloud Trace exporter configured successfully!")

except ImportError:
    print("[OTEL_INIT] opentelemetry-exporter-gcp-trace not available, traces will not be exported")
    print("[OTEL_INIT] Install with: pip install opentelemetry-exporter-gcp-trace")

from google.adk.agents import Agent


def get_weather(city: str) -> dict:
    """Get weather information for a city"""
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
    """Get current time for a city"""
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
    name="gcp_traces_agent",
    model="gemini-2.5-flash",
    description="Agent using GCP Cloud Trace (default telemetry)",
    instruction=(
        "You are a helpful city assistant. Use the available tools to answer "
        "questions about the current weather or time in any city the user asks about. "
        "Always use a tool - never guess or make up data."
    ),
    tools=[get_weather, get_current_time],
)
