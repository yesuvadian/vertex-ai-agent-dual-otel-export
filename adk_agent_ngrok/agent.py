import datetime
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
    name="portal26GCPLocal",
    model="gemini-2.0-flash-exp",
    description="City info agent - exports telemetry via ngrok to local collector",
    instruction=(
        "You are a helpful city assistant. Use the available tools to answer "
        "questions about the current weather or time in any city the user asks about. "
        "Always use a tool - never guess or make up data."
    ),
    tools=[get_weather, get_current_time],
)


# Agent Engine app with custom OTEL exporter
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from vertexai.agent_engines import AdkApp


def _add_custom_exporter():
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        print("[otel] OTEL_EXPORTER_OTLP_ENDPOINT not set - skipping")
        return
    if not endpoint.endswith("/v1/traces"):
        endpoint = endpoint.rstrip("/") + "/v1/traces"
    print(f"[otel] Adding custom OTLP exporter -> {endpoint}")
    try:
        provider = trace.get_tracer_provider()
        print(f"[otel] Provider type: {type(provider).__name__}")
        if hasattr(provider, "add_span_processor"):
            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
            )
            print(f"[otel] Exporter registered ✅")
        else:
            print(f"[otel] ERROR: no add_span_processor on {type(provider)}")
    except Exception as e:
        print(f"[otel] ERROR: {e}")


class CustomAdkApp(AdkApp):
    def set_up(self):
        super().set_up()
        _add_custom_exporter()


app = CustomAdkApp(agent=root_agent)
