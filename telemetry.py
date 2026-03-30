import os
import logging
from dotenv import load_dotenv
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

load_dotenv()

# Parse resource attributes from env
def parse_resource_attributes():
    """Parse OTEL_RESOURCE_ATTRIBUTES from env into a dict."""
    attrs = {"service.name": os.getenv("OTEL_SERVICE_NAME", "ai-agent")}
    resource_attrs = os.getenv("OTEL_RESOURCE_ATTRIBUTES", "")

    if resource_attrs:
        for pair in resource_attrs.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                attrs[key.strip()] = value.strip()

    return attrs

# Parse headers for OTLP
def parse_headers():
    """Parse OTEL_EXPORTER_OTLP_HEADERS into a dict."""
    headers_str = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    headers = {}
    if headers_str:
        for header in headers_str.split(","):
            if "=" in header:
                key, value = header.split("=", 1)
                headers[key.strip()] = value.strip()
    return headers

# Create resource with all attributes
resource = Resource.create(parse_resource_attributes())

# ===== TRACES SETUP =====
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

traces_exporter = os.getenv("OTEL_TRACES_EXPORTER", "gcp_trace").lower()

if traces_exporter == "otlp":
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint and not endpoint.endswith("/v1/traces"):
            endpoint = endpoint.rstrip("/") + "/v1/traces"

        headers = parse_headers()
        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
        span_processor = BatchSpanProcessor(exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        print(f"[telemetry] OK OTLP trace exporter configured: {endpoint}")
    except Exception as e:
        print(f"[telemetry] ERROR Failed to configure OTLP trace exporter: {e}")

elif traces_exporter == "gcp_trace":
    try:
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        exporter = CloudTraceSpanExporter(project_id=project_id)
        span_processor = BatchSpanProcessor(exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        print(f"[telemetry] OK GCP Cloud Trace exporter configured: {project_id}")
    except Exception as e:
        print(f"[telemetry] ERROR Failed to configure GCP Cloud Trace exporter: {e}")

# ===== METRICS SETUP =====
metrics_exporter = os.getenv("OTEL_METRICS_EXPORTER", "none").lower()

if metrics_exporter == "otlp":
    try:
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint and not endpoint.endswith("/v1/metrics"):
            endpoint = endpoint.rstrip("/") + "/v1/metrics"

        headers = parse_headers()
        metric_exporter = OTLPMetricExporter(endpoint=endpoint, headers=headers)

        # Get export interval (default 60000ms = 60s, Portal26 uses 1000ms = 1s)
        export_interval_ms = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "1000"))

        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=export_interval_ms
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        print(f"[telemetry] OK OTLP metric exporter configured: {endpoint} (interval: {export_interval_ms}ms)")
    except Exception as e:
        print(f"[telemetry] ERROR Failed to configure OTLP metric exporter: {e}")

# ===== LOGS SETUP =====
logs_exporter = os.getenv("OTEL_LOGS_EXPORTER", "none").lower()

if logs_exporter == "otlp":
    try:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint and not endpoint.endswith("/v1/logs"):
            endpoint = endpoint.rstrip("/") + "/v1/logs"

        headers = parse_headers()
        log_exporter = OTLPLogExporter(endpoint=endpoint, headers=headers)

        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

        # Attach OTEL handler to root logger
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)

        print(f"[telemetry] OK OTLP log exporter configured: {endpoint}")
    except Exception as e:
        print(f"[telemetry] ERROR Failed to configure OTLP log exporter: {e}")

# Export meter for application use
meter = metrics.get_meter(__name__)
