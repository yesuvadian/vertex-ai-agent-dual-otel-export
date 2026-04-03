"""
Core processing logic: Extract metadata, fetch traces, transform, export
Stateless design - each message processed independently
"""
import logging
from typing import Dict, Any, Optional
from trace_fetcher import TraceFetcher
from otel_transformer import OTELTransformer
from portal26_exporter import Portal26Exporter
from dedup_cache import DedupCache
from storage_manager import StorageManager

logger = logging.getLogger(__name__)


class TraceProcessor:
    """
    Processes log entries to fetch traces and export to Portal26
    """

    def __init__(self):
        """Initialize processor components"""
        try:
            self.trace_fetcher = TraceFetcher()
            logger.info("TraceFetcher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TraceFetcher: {e}")
            raise

        try:
            self.transformer = OTELTransformer()
            logger.info("OTELTransformer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OTELTransformer: {e}")
            raise

        try:
            self.exporter = Portal26Exporter()
            logger.info("Portal26Exporter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Portal26Exporter: {e}")
            raise

        try:
            self.dedup_cache = DedupCache()
            logger.info("DedupCache initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize DedupCache: {e} - continuing without dedup")
            self.dedup_cache = None

        try:
            self.storage = StorageManager()
            logger.info("StorageManager initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize StorageManager: {e} - continuing without storage")
            self.storage = None

    def process_log_entry(self, log_entry: Dict[str, Any], attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single log entry

        Args:
            log_entry: Parsed log entry from Pub/Sub message
            attributes: Pub/Sub message attributes

        Returns:
            {'success': bool, 'tenant_id': str, 'trace_id': str, 'error': str}
        """
        try:
            # Step 1: Extract metadata (DYNAMIC tenant pickup)
            metadata = self.extract_metadata(log_entry, attributes)

            if not metadata['trace_id']:
                return {
                    'success': False,
                    'tenant_id': metadata.get('tenant_id', 'unknown'),
                    'error': 'No trace ID found in log entry'
                }

            if not metadata['project_id']:
                return {
                    'success': False,
                    'tenant_id': metadata.get('tenant_id', 'unknown'),
                    'error': 'No project ID found in log entry'
                }

            # Use default tenant if not specified
            if not metadata['tenant_id']:
                logger.warning(f"No tenant_id found for trace {metadata['trace_id']}, using 'default'")
                metadata['tenant_id'] = 'default'

            logger.info(f"Processing trace {metadata['trace_id']} for tenant {metadata['tenant_id']}")

            # Step 2: Check deduplication cache
            if self.dedup_cache and self.dedup_cache.is_processed(metadata['trace_id']):
                logger.info(f"Skipping duplicate trace {metadata['trace_id']}")
                return {
                    'success': True,
                    'tenant_id': metadata['tenant_id'],
                    'trace_id': metadata['trace_id'],
                    'skipped': True,
                    'reason': 'duplicate'
                }

            # Step 3: Fetch full trace from Cloud Trace API
            trace_data = self.trace_fetcher.fetch_trace(
                project_id=metadata['project_id'],
                trace_id=metadata['trace_id']
            )

            if not trace_data:
                return {
                    'success': False,
                    'tenant_id': metadata['tenant_id'],
                    'trace_id': metadata['trace_id'],
                    'error': 'Failed to fetch trace from Cloud Trace API'
                }

            # Store raw GCP trace (before transformation)
            if self.storage:
                self.storage.store_raw_gcp_trace(trace_data, metadata)
                self.storage.store_processing_log(
                    trace_id=metadata['trace_id'],
                    tenant_id=metadata['tenant_id'],
                    stage='fetch',
                    status='success',
                    details={'span_count': len(trace_data.spans) if trace_data.spans else 0}
                )

            # Step 4: Transform to OTEL format
            try:
                otel_data = self.transformer.transform(trace_data, metadata)

                # Store OTEL transformed trace (before export)
                if self.storage:
                    self.storage.store_otel_trace(otel_data, metadata)
                    self.storage.store_processing_log(
                        trace_id=metadata['trace_id'],
                        tenant_id=metadata['tenant_id'],
                        stage='transform',
                        status='success',
                        details={'format': 'otel_protobuf'}
                    )
            except Exception as e:
                logger.error(f"Failed to transform trace {metadata['trace_id']}: {e}", exc_info=True)

                # Store transformation error
                if self.storage:
                    self.storage.store_processing_log(
                        trace_id=metadata['trace_id'],
                        tenant_id=metadata['tenant_id'],
                        stage='transform',
                        status='error',
                        details={'error': str(e)}
                    )

                return {
                    'success': False,
                    'tenant_id': metadata['tenant_id'],
                    'trace_id': metadata['trace_id'],
                    'error': f'Transform failed: {str(e)}'
                }

            # Step 5: Export to Portal26 (with tenant_id in metadata)
            export_result = self.exporter.export(otel_data, metadata['tenant_id'])

            # Store export confirmation
            if self.storage:
                self.storage.store_export_confirmation(
                    trace_id=metadata['trace_id'],
                    tenant_id=metadata['tenant_id'],
                    success=export_result['success'],
                    status_code=export_result.get('status_code'),
                    response_body=export_result.get('response_body'),
                    error=export_result.get('error'),
                    metadata=metadata
                )

                # Store processing log
                self.storage.store_processing_log(
                    trace_id=metadata['trace_id'],
                    tenant_id=metadata['tenant_id'],
                    stage='export',
                    status='success' if export_result['success'] else 'error',
                    details={
                        'endpoint': 'portal26',
                        'status_code': export_result.get('status_code'),
                        'error': export_result.get('error')
                    }
                )

            if not export_result['success']:
                return {
                    'success': False,
                    'tenant_id': metadata['tenant_id'],
                    'trace_id': metadata['trace_id'],
                    'error': f"Export failed: {export_result['error']}"
                }

            # Step 6: Mark as processed in cache
            if self.dedup_cache:
                self.dedup_cache.mark_processed(metadata['trace_id'])

            return {
                'success': True,
                'tenant_id': metadata['tenant_id'],
                'trace_id': metadata['trace_id']
            }

        except Exception as e:
            logger.error(f"Error processing log entry: {e}", exc_info=True)
            return {
                'success': False,
                'tenant_id': 'unknown',
                'error': str(e)
            }

    def extract_metadata(self, log_entry: Dict[str, Any], attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract trace_id, tenant_id, project_id from log entry
        DYNAMIC TENANT PICKUP - no hardcoding

        Args:
            log_entry: Parsed log entry
            attributes: Pub/Sub message attributes

        Returns:
            Metadata dictionary
        """
        # Extract trace ID from trace field
        # Format: "projects/PROJECT_ID/traces/TRACE_ID"
        trace_full = log_entry.get('trace', '')
        trace_id = None
        project_id = None

        if trace_full:
            trace_parts = trace_full.split('/')
            if len(trace_parts) >= 4:
                # projects/PROJECT_ID/traces/TRACE_ID
                project_id = trace_parts[1]
                trace_id = trace_parts[3]
            elif len(trace_parts) == 1:
                # Just the trace ID
                trace_id = trace_parts[0]

        # Extract tenant_id from labels (set by log sink) or attributes
        labels = log_entry.get('labels', {})
        tenant_id = labels.get('tenant_id') or attributes.get('tenant_id')

        # Extract resource information
        resource = log_entry.get('resource', {})
        resource_labels = resource.get('labels', {})

        # If project_id not in trace field, try resource labels
        if not project_id:
            project_id = resource_labels.get('project_id')

        metadata = {
            'trace_id': trace_id,
            'project_id': project_id,
            'tenant_id': tenant_id,
            'reasoning_engine_id': resource_labels.get('reasoning_engine_id'),
            'location': resource_labels.get('location', 'us-central1'),
            'timestamp': log_entry.get('timestamp'),
            'log_name': log_entry.get('logName'),
            'severity': log_entry.get('severity'),
            'insert_id': log_entry.get('insertId')
        }

        logger.debug(f"Extracted metadata: {metadata}")
        return metadata
