"""
OpenTelemetry configuration for Vertex AI Agent Engine deployment
Exports to Portal26 OTEL collector with full content capture enabled
"""
import config

# OpenTelemetry environment variables for Agent Engine deployment
OTEL_CONFIG = {
    # Service identification
    "OTEL_SERVICE_NAME": config.SERVICE_NAME,

    # Portal26 multi-tenant tags
    "PORTAL26_TENANT_ID": config.TENANT_ID,
    "PORTAL26_USER_ID": config.USER_ID,

    # OTLP Exporter endpoints
    "OTEL_EXPORTER_OTLP_ENDPOINT": config.OTEL_ENDPOINT,
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": f"{config.OTEL_ENDPOINT}/v1/traces",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT": f"{config.OTEL_ENDPOINT}/v1/metrics",
    "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT": f"{config.OTEL_ENDPOINT}/v1/logs",

    # Exporter configuration
    "OTEL_TRACES_EXPORTER": "otlp",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",

    # CRITICAL: Enable full content capture (prompts & responses)
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",

    # Additional instrumentation settings
    "OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED": "true",
    "OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT": "65536",
    "OTEL_PROPAGATORS": "tracecontext,baggage",

    # GCP settings
    "GOOGLE_GENAI_USE_VERTEXAI": "true",
}
