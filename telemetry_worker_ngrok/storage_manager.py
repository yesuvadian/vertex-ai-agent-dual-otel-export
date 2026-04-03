"""
Storage Manager - Archive traces before and after OTEL transformation
Stores: Raw GCP traces, OTEL transformed traces, and export confirmations
"""
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from google.cloud import trace_v1
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans
from google.protobuf import json_format

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages storage of traces at different pipeline stages:
    1. Raw GCP trace (before transformation)
    2. OTEL transformed trace (after transformation)
    3. Export confirmation (after Portal26 export)
    """

    def __init__(self, base_path: str = None):
        """
        Initialize storage manager

        Args:
            base_path: Base directory for storage (default: ./trace_archive)
        """
        self.base_path = Path(base_path or os.getenv('TRACE_ARCHIVE_PATH', './trace_archive'))
        self.enabled = os.getenv('ENABLE_TRACE_STORAGE', 'true').lower() == 'true'

        if self.enabled:
            self._create_directories()
            logger.info(f"StorageManager initialized with path: {self.base_path}")
        else:
            logger.info("StorageManager disabled (ENABLE_TRACE_STORAGE=false)")

    def _create_directories(self):
        """Create storage directory structure"""
        directories = [
            self.base_path / 'raw_gcp',      # Raw GCP traces
            self.base_path / 'otel',         # OTEL transformed
            self.base_path / 'confirmations', # Export confirmations
            self.base_path / 'metadata',     # Metadata and logs
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created storage directories under {self.base_path}")

    def _get_trace_filename(self, trace_id: str, tenant_id: str, suffix: str) -> Path:
        """
        Generate filename for trace storage

        Args:
            trace_id: Trace ID
            tenant_id: Tenant ID
            suffix: File suffix (e.g., 'raw', 'otel', 'confirm')

        Returns:
            Path to file
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{tenant_id}_{trace_id}_{timestamp}_{suffix}.json"
        return filename

    def store_raw_gcp_trace(
        self,
        trace: trace_v1.Trace,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store raw GCP trace before transformation

        Args:
            trace: GCP Cloud Trace object
            metadata: Metadata (trace_id, tenant_id, project_id, etc.)

        Returns:
            Path to stored file, or None if disabled
        """
        if not self.enabled:
            return None

        try:
            trace_id = metadata.get('trace_id', 'unknown')
            tenant_id = metadata.get('tenant_id', 'default')

            # Convert trace to dict
            trace_dict = {
                'storage_type': 'raw_gcp_trace',
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata,
                'trace': {
                    'project_id': trace.project_id,
                    'trace_id': trace.trace_id,
                    'spans': []
                }
            }

            # Add spans
            if trace.spans:
                for span in trace.spans:
                    span_dict = {
                        'span_id': str(span.span_id),
                        'parent_span_id': str(span.parent_span_id) if span.parent_span_id else None,
                        'name': str(span.name) if span.name else None,
                        'start_time': span.start_time.ToDatetime().isoformat() if span.start_time else None,
                        'end_time': span.end_time.ToDatetime().isoformat() if span.end_time else None,
                        'labels': dict(span.labels) if span.labels else {},
                        'kind': str(span.kind) if hasattr(span, 'kind') else None,
                    }

                    # Add status if present
                    if hasattr(span, 'status') and span.status:
                        span_dict['status'] = {
                            'code': span.status.code,
                            'message': span.status.message if hasattr(span.status, 'message') else None
                        }

                    trace_dict['trace']['spans'].append(span_dict)

            # Write to file
            filename = self._get_trace_filename(trace_id, tenant_id, 'raw')
            filepath = self.base_path / 'raw_gcp' / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trace_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Stored raw GCP trace: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to store raw GCP trace: {e}", exc_info=True)
            return None

    def store_otel_trace(
        self,
        resource_spans: ResourceSpans,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store OTEL transformed trace before export

        Args:
            resource_spans: OTEL ResourceSpans protobuf object
            metadata: Metadata

        Returns:
            Path to stored file, or None if disabled
        """
        if not self.enabled:
            return None

        try:
            trace_id = metadata.get('trace_id', 'unknown')
            tenant_id = metadata.get('tenant_id', 'default')

            # Convert protobuf to JSON
            otel_json = json_format.MessageToDict(resource_spans)

            # Wrap with metadata
            storage_dict = {
                'storage_type': 'otel_transformed',
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata,
                'otel_trace': otel_json
            }

            # Write to file
            filename = self._get_trace_filename(trace_id, tenant_id, 'otel')
            filepath = self.base_path / 'otel' / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(storage_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Stored OTEL trace: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to store OTEL trace: {e}", exc_info=True)
            return None

    def store_export_confirmation(
        self,
        trace_id: str,
        tenant_id: str,
        success: bool,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store export confirmation after sending to Portal26

        Args:
            trace_id: Trace ID
            tenant_id: Tenant ID
            success: Whether export succeeded
            status_code: HTTP status code from Portal26
            response_body: Response body from Portal26
            error: Error message if failed
            metadata: Additional metadata

        Returns:
            Path to stored file, or None if disabled
        """
        if not self.enabled:
            return None

        try:
            confirmation = {
                'storage_type': 'export_confirmation',
                'timestamp': datetime.utcnow().isoformat(),
                'trace_id': trace_id,
                'tenant_id': tenant_id,
                'export_success': success,
                'status_code': status_code,
                'response_body': response_body,
                'error': error,
                'metadata': metadata or {}
            }

            # Write to file
            filename = self._get_trace_filename(trace_id, tenant_id, 'confirm')
            filepath = self.base_path / 'confirmations' / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(confirmation, f, indent=2, ensure_ascii=False)

            logger.info(f"Stored export confirmation: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to store export confirmation: {e}", exc_info=True)
            return None

    def store_processing_log(
        self,
        trace_id: str,
        tenant_id: str,
        stage: str,
        status: str,
        details: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store processing log for audit trail

        Args:
            trace_id: Trace ID
            tenant_id: Tenant ID
            stage: Processing stage (fetch, transform, export)
            status: Status (success, error, warning)
            details: Additional details

        Returns:
            Path to stored file, or None if disabled
        """
        if not self.enabled:
            return None

        try:
            log_entry = {
                'storage_type': 'processing_log',
                'timestamp': datetime.utcnow().isoformat(),
                'trace_id': trace_id,
                'tenant_id': tenant_id,
                'stage': stage,
                'status': status,
                'details': details
            }

            # Append to daily log file
            date_str = datetime.utcnow().strftime('%Y%m%d')
            filename = f"processing_log_{date_str}.jsonl"
            filepath = self.base_path / 'metadata' / filename

            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to store processing log: {e}", exc_info=True)
            return None

    def get_trace_history(self, trace_id: str) -> Dict[str, Any]:
        """
        Get complete history of a trace through the pipeline

        Args:
            trace_id: Trace ID

        Returns:
            Dict with paths to all stored artifacts
        """
        if not self.enabled:
            return {}

        history = {
            'trace_id': trace_id,
            'raw_gcp': [],
            'otel': [],
            'confirmations': [],
        }

        # Search for files containing trace_id
        for stage, directory in [
            ('raw_gcp', self.base_path / 'raw_gcp'),
            ('otel', self.base_path / 'otel'),
            ('confirmations', self.base_path / 'confirmations'),
        ]:
            if directory.exists():
                files = list(directory.glob(f'*{trace_id}*.json'))
                history[stage] = [str(f) for f in sorted(files)]

        return history

    def cleanup_old_files(self, days: int = 7):
        """
        Clean up files older than specified days

        Args:
            days: Number of days to retain
        """
        if not self.enabled:
            return

        import time
        cutoff_time = time.time() - (days * 86400)

        cleaned_count = 0
        for directory in [
            self.base_path / 'raw_gcp',
            self.base_path / 'otel',
            self.base_path / 'confirmations',
            self.base_path / 'metadata',
        ]:
            if directory.exists():
                for filepath in directory.iterdir():
                    if filepath.is_file() and filepath.stat().st_mtime < cutoff_time:
                        filepath.unlink()
                        cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} files older than {days} days")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics

        Returns:
            Dict with file counts and sizes
        """
        if not self.enabled:
            return {'enabled': False}

        stats = {
            'enabled': True,
            'base_path': str(self.base_path),
            'directories': {}
        }

        for stage, directory in [
            ('raw_gcp', self.base_path / 'raw_gcp'),
            ('otel', self.base_path / 'otel'),
            ('confirmations', self.base_path / 'confirmations'),
            ('metadata', self.base_path / 'metadata'),
        ]:
            if directory.exists():
                files = list(directory.iterdir())
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                stats['directories'][stage] = {
                    'file_count': len(files),
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2)
                }

        return stats
