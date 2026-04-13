"""
Shared OTEL initialization module for Portal 26 integration.
Works with Vertex AI Agent Engine deployments.

Usage in any agent:
    import otel_portal26  # Auto-initializes OTEL on import
    from google.adk.agents import Agent
    # ... rest of agent code unchanged
"""
import os
import sys

def init_otel():
    """Initialize OTEL for Portal 26 from environment variables."""

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        print("[OTEL] No Portal 26 endpoint configured")
        return

    service_name = os.getenv("OTEL_SERVICE_NAME", "vertex-agent")

    print(f"[OTEL] Initializing Portal 26 integration...")
    print(f"[OTEL] Endpoint: {endpoint}")
    print(f"[OTEL] Service: {service_name}")

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

        resource = Resource(attributes={"service.name": service_name})

        # Initialize Traces
        tracer_provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)
        print("[OTEL] ✓ Traces → Portal 26")

        # Initialize Metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics")
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        print("[OTEL] ✓ Metrics → Portal 26")

        # Initialize Logs
        logger_provider = LoggerProvider(resource=resource)
        log_exporter = OTLPLogExporter(endpoint=f"{endpoint}/v1/logs")
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
        print("[OTEL] ✓ Logs → Portal 26")

        # Auto-instrument Vertex AI
        try:
            from opentelemetry.instrumentation.vertexai import VertexAIInstrumentor
            VertexAIInstrumentor().instrument()
            print("[OTEL] ✓ Vertex AI instrumented")
        except Exception as e:
            print(f"[OTEL] Warning: Vertex AI instrumentation: {e}")

        print("[OTEL] ✅ Portal 26 integration complete!")

    except Exception as e:
        print(f"[OTEL] ❌ Failed to initialize: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

# Auto-initialize on import
init_otel()
