"""
Transform Cloud Trace format to OTEL format
"""
import logging
import os
from typing import Dict, Any
from google.cloud import trace_v1
from opentelemetry.proto.trace.v1.trace_pb2 import (
    ResourceSpans, ScopeSpans, Span, Status
)
from opentelemetry.proto.resource.v1.resource_pb2 import Resource
from opentelemetry.proto.common.v1.common_pb2 import KeyValue, AnyValue

logger = logging.getLogger(__name__)


class OTELTransformer:
    """
    Transforms GCP Cloud Trace format to OpenTelemetry format
    """

    def __init__(self):
        """Initialize transformer with optional OTEL resource attributes"""
        # Parse OTEL_RESOURCE_ATTRIBUTES if provided
        # Format: key1=value1,key2=value2
        self.resource_attributes = {}
        otel_attrs = os.environ.get('OTEL_RESOURCE_ATTRIBUTES', '')
        if otel_attrs:
            for pair in otel_attrs.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    self.resource_attributes[key.strip()] = value.strip()
            logger.info(f"Loaded OTEL resource attributes: {self.resource_attributes}")

        logger.info("OTELTransformer initialized")

    def transform(self, gcp_trace: trace_v1.Trace, metadata: Dict[str, Any]) -> ResourceSpans:
        """
        Convert GCP Cloud Trace to OTEL ResourceSpans

        Args:
            gcp_trace: Cloud Trace API response
            metadata: Dict with tenant_id, project_id, etc.

        Returns:
            OTEL ResourceSpans object
        """
        resource_spans = ResourceSpans()

        # Set resource attributes (includes tenant_id)
        resource = resource_spans.resource
        self._add_resource_attribute(resource, 'service.name', 'vertex-ai-agent')
        self._add_resource_attribute(resource, 'cloud.provider', 'gcp')
        self._add_resource_attribute(resource, 'cloud.platform', 'gcp_vertex_ai')
        self._add_resource_attribute(resource, 'tenant.id', metadata.get('tenant_id'))
        self._add_resource_attribute(resource, 'project.id', metadata.get('project_id'))
        self._add_resource_attribute(resource, 'reasoning_engine.id', metadata.get('reasoning_engine_id'))
        self._add_resource_attribute(resource, 'location', metadata.get('location'))

        # Add OTEL_RESOURCE_ATTRIBUTES if configured
        for key, value in self.resource_attributes.items():
            self._add_resource_attribute(resource, key, value)

        # Create scope spans
        scope_spans = resource_spans.scope_spans.add()
        scope_spans.scope.name = 'vertex-ai-telemetry'
        scope_spans.scope.version = '1.0'

        # Convert each GCP span to OTEL span
        span_count = 0
        if gcp_trace.spans:
            for gcp_span in gcp_trace.spans:
                try:
                    otel_span = self._convert_span(gcp_span, metadata)
                    scope_spans.spans.append(otel_span)
                    span_count += 1
                except Exception as e:
                    logger.error(f"Failed to convert span {gcp_span.span_id}: {e}", exc_info=True)
                    # Continue with other spans

        logger.info(f"Transformed {span_count} spans to OTEL format")
        return resource_spans

    def _convert_span(self, gcp_span: trace_v1.TraceSpan, metadata: Dict[str, Any]) -> Span:
        """
        Convert single GCP span to OTEL span

        Args:
            gcp_span: GCP TraceSpan object
            metadata: Metadata dictionary

        Returns:
            OTEL Span object
        """
        span = Span()

        # Trace ID and Span ID (convert to bytes)
        trace_id_hex = metadata.get('trace_id', '')
        if trace_id_hex:
            try:
                # Remove any dashes and convert to bytes
                trace_id_clean = trace_id_hex.replace('-', '')
                # Pad to 32 characters (16 bytes) if needed
                trace_id_clean = trace_id_clean.zfill(32)
                span.trace_id = bytes.fromhex(trace_id_clean)
            except Exception as e:
                logger.warning(f"Failed to parse trace_id {trace_id_hex}: {e}")

        # Span ID
        if gcp_span.span_id:
            try:
                span_id_str = str(gcp_span.span_id)
                # Pad to 16 characters (8 bytes)
                span_id_str = span_id_str.zfill(16)
                span.span_id = bytes.fromhex(span_id_str)
            except Exception as e:
                logger.warning(f"Failed to parse span_id {gcp_span.span_id}: {e}")

        # Parent Span ID
        if gcp_span.parent_span_id:
            try:
                parent_id_str = str(gcp_span.parent_span_id)
                parent_id_str = parent_id_str.zfill(16)
                span.parent_span_id = bytes.fromhex(parent_id_str)
            except Exception as e:
                logger.warning(f"Failed to parse parent_span_id {gcp_span.parent_span_id}: {e}")

        # Span name
        if hasattr(gcp_span, 'display_name') and gcp_span.display_name:
            if hasattr(gcp_span.display_name, 'value'):
                span.name = gcp_span.display_name.value
            else:
                span.name = str(gcp_span.display_name)
        else:
            span.name = 'unknown'

        # Span kind
        span.kind = self._map_span_kind(gcp_span)

        # Timestamps (convert to nanoseconds)
        if hasattr(gcp_span, 'start_time') and gcp_span.start_time:
            span.start_time_unix_nano = int(gcp_span.start_time.timestamp() * 1e9)
        if hasattr(gcp_span, 'end_time') and gcp_span.end_time:
            span.end_time_unix_nano = int(gcp_span.end_time.timestamp() * 1e9)

        # Attributes (including labels from GCP span)
        if hasattr(gcp_span, 'labels') and gcp_span.labels:
            for key, value in gcp_span.labels.items():
                self._add_span_attribute(span, key, value)

        # Add tenant_id and metadata to each span
        self._add_span_attribute(span, 'tenant.id', metadata.get('tenant_id'))
        self._add_span_attribute(span, 'project.id', metadata.get('project_id'))
        self._add_span_attribute(span, 'insert_id', metadata.get('insert_id'))

        # Status
        if hasattr(gcp_span, 'status') and gcp_span.status:
            span.status.code = self._map_status_code(gcp_span.status.code)
            if hasattr(gcp_span.status, 'message') and gcp_span.status.message:
                span.status.message = gcp_span.status.message

        return span

    def _add_resource_attribute(self, resource: Resource, key: str, value: Any):
        """Add attribute to resource"""
        if value is not None:
            attr = resource.attributes.add()
            attr.key = key
            attr.value.string_value = str(value)

    def _add_span_attribute(self, span: Span, key: str, value: Any):
        """Add attribute to span"""
        if value is not None:
            attr = span.attributes.add()
            attr.key = key
            attr.value.string_value = str(value)

    def _map_span_kind(self, gcp_span) -> int:
        """
        Map GCP span kind to OTEL span kind

        Args:
            gcp_span: GCP TraceSpan object

        Returns:
            OTEL span kind constant
        """
        # GCP span kinds:
        # SPAN_KIND_UNSPECIFIED = 0
        # RPC_SERVER = 1
        # RPC_CLIENT = 2

        if hasattr(gcp_span, 'kind'):
            kind = gcp_span.kind
            if kind == 1:  # RPC_SERVER
                return Span.SPAN_KIND_SERVER
            elif kind == 2:  # RPC_CLIENT
                return Span.SPAN_KIND_CLIENT

        # Default to INTERNAL
        return Span.SPAN_KIND_INTERNAL

    def _map_status_code(self, gcp_code: int) -> int:
        """
        Map GCP status code to OTEL status code

        Args:
            gcp_code: GCP status code

        Returns:
            OTEL status code
        """
        # GCP codes (from google.rpc.Code):
        # 0 = OK
        # Non-zero = ERROR

        if gcp_code == 0:
            return Status.STATUS_CODE_OK
        else:
            return Status.STATUS_CODE_ERROR
