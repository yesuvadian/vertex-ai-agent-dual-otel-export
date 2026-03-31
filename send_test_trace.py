"""
Send a test OTEL trace to local receiver to demonstrate JSON generation
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import time

print("Sending test OTEL trace to local receiver...")
print("This will generate a JSON file in otel-data/")
print()

# Create a tracer provider with custom resource attributes
resource = Resource.create({
    "service.name": "test_agent",
    "portal26.tenant_id": "tenant1",
    "portal26.user.id": "relusys",
    "agent.type": "test"
})

provider = TracerProvider(resource=resource)

# Add OTLP exporter pointing to local receiver
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces"
)
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

# Set as global tracer provider
trace.set_tracer_provider(provider)

# Get a tracer
tracer = trace.get_tracer(__name__)

# Create some test spans
print("Creating test spans...")

with tracer.start_as_current_span("test_operation") as span:
    span.set_attribute("test.type", "demonstration")
    span.set_attribute("test.purpose", "Generate JSON file")

    with tracer.start_as_current_span("sub_operation") as child_span:
        child_span.set_attribute("query", "What is 2+2?")
        child_span.set_attribute("response", "4")
        child_span.add_event("Processing query")
        time.sleep(0.1)  # Simulate some work
        child_span.add_event("Query processed")

print("Spans created. Flushing to exporter...")

# Force flush to send immediately
provider.force_flush()

print()
print("[OK] Test trace sent!")
print()
print("Check otel-data/ folder for new JSON file:")
print("  ls otel-data/*.json")
print("  or")
print("  dir otel-data\\*.json")
