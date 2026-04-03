"""
Fetch full traces from Cloud Trace API across projects
Uses service account credentials with cloudtrace.user role
"""
import logging
from typing import Optional
from google.cloud import trace_v1
from google.api_core import retry
from google.api_core.exceptions import NotFound, PermissionDenied, GoogleAPIError

logger = logging.getLogger(__name__)


class TraceFetcher:
    """
    Fetches traces from Cloud Trace API with retry logic
    """

    def __init__(self):
        """
        Initialize Cloud Trace API client
        Uses Application Default Credentials (service account in Cloud Run)
        """
        try:
            self.client = trace_v1.TraceServiceClient()
            logger.info("Cloud Trace API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Trace client: {e}", exc_info=True)
            raise

    @retry.Retry(
        predicate=retry.if_exception_type(
            GoogleAPIError,
            ConnectionError,
            TimeoutError
        ),
        initial=2.0,        # 2 seconds initial delay
        maximum=5.0,        # 5 seconds max delay
        multiplier=1.5,     # exponential backoff
        deadline=30.0,      # total timeout 30 seconds
        on_error=lambda e: logger.warning(f"Retrying after error: {e}")
    )
    def fetch_trace(self, project_id: str, trace_id: str) -> Optional[trace_v1.Trace]:
        """
        Fetch full trace from Cloud Trace API

        Args:
            project_id: GCP project ID where trace is stored
            trace_id: Trace ID to fetch

        Returns:
            Trace object or None if not found
        """
        if not project_id or not trace_id:
            logger.error(f"Invalid input: project_id={project_id}, trace_id={trace_id}")
            return None

        try:
            trace_name = f"projects/{project_id}/traces/{trace_id}"
            logger.info(f"Fetching trace: {trace_name}")

            trace = self.client.get_trace(project_id=project_id, trace_id=trace_id)

            span_count = len(trace.spans) if trace.spans else 0
            logger.info(f"Fetched trace {trace_id} with {span_count} spans")

            return trace

        except NotFound:
            logger.warning(
                f"Trace not found: {trace_id} in project {project_id}. "
                "This may be normal if trace is not yet written to Cloud Trace."
            )
            return None

        except PermissionDenied as e:
            logger.error(
                f"Permission denied fetching trace from {project_id}. "
                f"Ensure service account has roles/cloudtrace.user role. Error: {e}"
            )
            return None

        except GoogleAPIError as e:
            logger.error(f"Google API error fetching trace {trace_id}: {e}", exc_info=True)
            # Will be retried by decorator
            raise

        except Exception as e:
            logger.error(f"Unexpected error fetching trace {trace_id}: {e}", exc_info=True)
            return None

    def list_traces(
        self,
        project_id: str,
        start_time=None,
        end_time=None,
        filter_str: str = None,
        page_size: int = 100
    ):
        """
        List traces in a project (for batch processing)

        Args:
            project_id: GCP project ID
            start_time: Start time for trace query
            end_time: End time for trace query
            filter_str: Filter string (Cloud Trace filter syntax)
            page_size: Number of traces per page

        Yields:
            Trace objects
        """
        try:
            request = trace_v1.ListTracesRequest(
                project_id=project_id,
                page_size=page_size
            )

            if start_time:
                request.start_time = start_time
            if end_time:
                request.end_time = end_time
            if filter_str:
                request.filter = filter_str

            logger.info(f"Listing traces from project {project_id}")

            page_result = self.client.list_traces(request=request)

            for trace in page_result:
                yield trace

        except Exception as e:
            logger.error(f"Error listing traces from {project_id}: {e}", exc_info=True)
            raise
