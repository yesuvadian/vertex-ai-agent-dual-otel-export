"""
Test OTEL configuration by sending a test span to Portal26
"""
import os
import sys
import time

print("=" * 70)
print("Testing OTEL Direct to Portal26")
print("=" * 70)
print()

# Load portal26_otel_agent .env file
print("Step 1: Loading environment")
print("-" * 70)

env_file = "portal26_otel_agent/.env"
with open(env_file, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')}")
print(f"OTEL_SERVICE_NAME: {os.environ.get('OTEL_SERVICE_NAME')}")
print(f"OTEL_EXPORTER_OTLP_HEADERS: {os.environ.get('OTEL_EXPORTER_OTLP_HEADERS')[:30]}...")
print("[OK] Environment loaded")
print()

# Initialize OTEL
print("Step 2: Initializing OTEL with Portal26 config")
print("-" * 70)

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
if not endpoint.endswith("/v1/traces"):
    endpoint = endpoint.rstrip("/") + "/v1/traces"

print(f"Endpoint: {endpoint}")

# Create resource with Portal26 attributes
resource = Resource.create({
    "service.name": os.environ.get("OTEL_SERVICE_NAME", "portal26_otel_agent"),
    "portal26.tenant_id": "tenant1",
    "portal26.user.id": "relusys",
    "agent.type": "local-test"
})

# Create TracerProvider
provider = TracerProvider(resource=resource)

# Add OTLP exporter (will automatically use OTEL_EXPORTER_OTLP_HEADERS from env)
otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

# Set as global tracer provider
trace.set_tracer_provider(provider)
print("[OK] OTEL initialized with Portal26 config")
print()

# Create test span
print("Step 3: Creating test span")
print("-" * 70)

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("local_agent_test") as span:
    span.set_attribute("test.type", "local_verification")
    span.set_attribute("test.query", "What is the weather in Bengaluru?")
    span.set_attribute("test.response", "Partly cloudy, 28C")
    print("[OK] Test span created with attributes")

print()
print("Step 4: Flushing spans to Portal26")
print("-" * 70)
print("Waiting for BatchSpanProcessor to export...")

# Force flush
provider.force_flush()
time.sleep(2)

print("[OK] Spans flushed")
print()

print("=" * 70)
print("OTEL Test Complete")
print("=" * 70)
print()
print("Verification:")
print("-" * 70)
print("""
Check Portal26 Dashboard:

1. Log in to Portal26: https://portal26.in

2. Navigate to Traces/Telemetry section

3. Filter by:
   - Tenant ID: tenant1
   - User ID: relusys
   - Time: Last 5 minutes

4. Look for:
   - Service: portal26_otel_agent
   - Span: local_agent_test
   - Attributes:
     * test.type = local_verification
     * test.query = What is the weather in Bengaluru?
     * test.response = Partly cloudy, 28C

If this trace appears → Portal26 integration is WORKING! ✓

The agent configuration is correct and will send telemetry automatically
when deployed and queried via Google Cloud Console.
""")
