"""
Export OTEL data to Portal26 backend
"""
import logging
import os
from typing import Dict, Any
import requests
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest
)
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans

logger = logging.getLogger(__name__)


class Portal26Exporter:
    """
    Exports OTEL traces to Portal26 backend
    """

    def __init__(self):
        """
        Initialize exporter with Portal26 credentials from environment
        """
        self.endpoint = os.environ.get('PORTAL26_ENDPOINT')
        self.username = os.environ.get('PORTAL26_USERNAME')
        self.password = os.environ.get('PORTAL26_PASSWORD')

        if not self.endpoint:
            raise ValueError("PORTAL26_ENDPOINT environment variable not set")
        if not self.username:
            raise ValueError("PORTAL26_USERNAME environment variable not set")
        if not self.password:
            raise ValueError("PORTAL26_PASSWORD environment variable not set")

        # Default timeout
        self.timeout = int(os.environ.get('PORTAL26_TIMEOUT', '30'))

        logger.info(f"Portal26Exporter initialized with endpoint: {self.endpoint}")

    def export(self, resource_spans: ResourceSpans, tenant_id: str) -> Dict[str, Any]:
        """
        Export OTEL traces to Portal26

        Args:
            resource_spans: OTEL ResourceSpans object
            tenant_id: Tenant identifier

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            # Create OTLP export request
            request = ExportTraceServiceRequest()
            request.resource_spans.append(resource_spans)

            # Serialize to protobuf
            data = request.SerializeToString()

            logger.info(f"Exporting {len(resource_spans.scope_spans[0].spans)} spans for tenant {tenant_id}")
            logger.debug(f"Payload size: {len(data)} bytes")

            # Prepare headers
            headers = {
                'Content-Type': 'application/x-protobuf',
                'X-Tenant-ID': tenant_id,
                'User-Agent': 'vertex-ai-telemetry-worker/1.0'
            }

            # Basic authentication
            auth = (self.username, self.password)

            # Send to Portal26
            response = requests.post(
                self.endpoint,
                data=data,
                headers=headers,
                auth=auth,
                timeout=self.timeout
            )

            # Check response
            if response.status_code == 200:
                logger.info(f"Successfully exported traces for tenant {tenant_id}")
                return {'success': True}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(f"Export failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Error exporting to Portal26: {e}", exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }

    def export_batch(self, traces: list, tenant_id: str) -> Dict[str, Any]:
        """
        Export multiple traces in a single request

        Args:
            traces: List of ResourceSpans objects
            tenant_id: Tenant identifier

        Returns:
            {'success': bool, 'error': str, 'exported': int, 'failed': int}
        """
        if not traces:
            return {
                'success': True,
                'exported': 0,
                'failed': 0
            }

        try:
            # Create OTLP export request with all traces
            request = ExportTraceServiceRequest()
            for trace in traces:
                request.resource_spans.append(trace)

            # Serialize to protobuf
            data = request.SerializeToString()

            total_spans = sum(
                len(rs.scope_spans[0].spans)
                for rs in traces
                if rs.scope_spans
            )

            logger.info(
                f"Exporting batch of {len(traces)} traces "
                f"({total_spans} spans) for tenant {tenant_id}"
            )

            # Prepare headers
            headers = {
                'Content-Type': 'application/x-protobuf',
                'X-Tenant-ID': tenant_id,
                'User-Agent': 'vertex-ai-telemetry-worker/1.0'
            }

            # Basic authentication
            auth = (self.username, self.password)

            # Send to Portal26
            response = requests.post(
                self.endpoint,
                data=data,
                headers=headers,
                auth=auth,
                timeout=self.timeout
            )

            # Check response
            if response.status_code == 200:
                logger.info(
                    f"Successfully exported batch for tenant {tenant_id}: "
                    f"{len(traces)} traces, {total_spans} spans"
                )
                return {
                    'success': True,
                    'exported': len(traces),
                    'failed': 0
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(f"Batch export failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code,
                    'exported': 0,
                    'failed': len(traces)
                }

        except Exception as e:
            error_msg = f"Batch export error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'exported': 0,
                'failed': len(traces)
            }
