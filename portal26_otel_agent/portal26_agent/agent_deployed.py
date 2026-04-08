"""
Agent with hardcoded OTEL initialization for Vertex AI Agent Engine deployment.
"""
import os
import datetime
from zoneinfo import ZoneInfo

# ============================================================================
# HARDCODED OTEL INITIALIZATION FOR DEPLOYMENT
# ============================================================================
# This MUST run before importing Agent for deployment scenarios
print("[OTEL] Starting hardcoded OTEL initialization...")

# Read OTEL endpoint from environment (set via env_vars in deployment)
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "portal26_otel_agent")
TENANT_ID = os.getenv("PORTAL26_TENANT_ID", "tenant1")
USER_ID = os.getenv("PORTAL26_USER_ID", "relusys")

if OTEL_ENDPOINT:
    print(f"[OTEL] Endpoint: {OTEL_ENDPOINT}")
    print(f"[OTEL] Service: {SERVICE_NAME}")
    print(f"[OTEL] Tenant: {TENANT_ID}, User: {USER_ID}")

    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk.resources import Resource
        import logging

        resource = Resource(attributes={
            "service.name": SERVICE_NAME,
            "portal26.tenant_id": TENANT_ID,
            "portal26.user.id": USER_ID,
            "agent.type": "agent-engine"
        })

        # Initialize Traces
        tracer_provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)
        print("[OTEL] ✓ Traces configured")

        # Initialize Metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=f"{OTEL_ENDPOINT}/v1/metrics")
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        print("[OTEL] ✓ Metrics configured")

        # Initialize Logs
        logger_provider = LoggerProvider(resource=resource)
        log_exporter = OTLPLogExporter(endpoint=f"{OTEL_ENDPOINT}/v1/logs")
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
        print("[OTEL] ✓ Logs configured")

        # Auto-instrument Vertex AI
        try:
            from opentelemetry.instrumentation.vertexai import VertexAIInstrumentor
            VertexAIInstrumentor().instrument()
            print("[OTEL] ✓ Vertex AI instrumentation enabled")
        except Exception as e:
            print(f"[OTEL] Warning: Vertex AI instrumentation failed: {e}")

        print("[OTEL] ✓ OTEL initialization complete!")

    except Exception as e:
        print(f"[OTEL] ✗ OTEL initialization failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[OTEL] No OTEL_EXPORTER_OTLP_ENDPOINT found, skipping OTEL initialization")

# ============================================================================
# Now import Agent (after OTEL is initialized)
# ============================================================================
from google.adk.agents import Agent


def get_weather(city: str) -> dict:
    """Returns a mock weather report for a given city.

    Args:
        city: Name of the city to get weather for.

    Returns:
        dict with status and report or error message.
    """
    mock_data = {
        "bengaluru": "Partly cloudy, 28°C. Humidity 70%.",
        "new york":  "Sunny, 22°C. Light winds.",
        "london":    "Overcast, 15°C. Rain expected.",
        "tokyo":     "Sunny, 28°C. Clear skies.",
    }
    normalized = city.lower().strip()
    if normalized in mock_data:
        return {"status": "success", "report": mock_data[normalized]}
    return {
        "status": "error",
        "error_message": f"No weather data available for '{city}'.",
    }


def get_current_time(city: str) -> dict:
    """Returns the current local time for a given city.

    Args:
        city: Name of the city.

    Returns:
        dict with status and current time string or error.
    """
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
    name="portal26_otel_agent",
    model="gemini-2.5-flash",
    description="City info agent with complete Portal26 OTEL telemetry + content capture",
    instruction=(
        "You are a helpful city assistant. Use the available tools to answer "
        "questions about the current weather or time in any city the user asks about. "
        "Always use a tool — never guess or make up data."
    ),
    tools=[get_weather, get_current_time],
)
