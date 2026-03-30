# Custom OTEL exporter for Portal26
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def _add_custom_exporter():
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        print("[otel] OTEL_EXPORTER_OTLP_ENDPOINT not set - skipping")
        return

    if not endpoint.endswith("/v1/traces"):
        endpoint = endpoint.rstrip("/") + "/v1/traces"

    print("[otel] Adding custom OTLP exporter to: " + endpoint)

    try:
        provider = trace.get_tracer_provider()
        print("[otel] Provider type: " + type(provider).__name__)

        if hasattr(provider, "add_span_processor"):
            headers_str = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
            headers = {}
            if headers_str:
                for header in headers_str.split(","):
                    if "=" in header:
                        key, value = header.split("=", 1)
                        headers[key.strip()] = value.strip()

            exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers=headers
            )

            provider.add_span_processor(BatchSpanProcessor(exporter))
            print("[otel] Custom OTLP exporter registered successfully")
        else:
            print("[otel] WARNING: provider has no add_span_processor")

    except Exception as e:
        print("[otel] ERROR setting up exporter: " + str(e))
        import traceback
        traceback.print_exc()

_add_custom_exporter()

from . import agent
