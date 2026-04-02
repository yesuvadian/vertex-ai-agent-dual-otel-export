"""
Fetch traces from Google Cloud Trace using Cloud Trace API
"""
from google.cloud import trace_v1
from datetime import datetime, timedelta
import json

PROJECT_ID = "agentic-ai-integration-490716"
SERVICE_NAME = "gcp_traces_agent"


def fetch_traces(hours_ago=1, max_results=10):
    """
    Fetch traces from Cloud Trace API

    Args:
        hours_ago: How many hours back to search
        max_results: Maximum number of traces to return
    """
    print("=" * 70)
    print("Fetching Traces from Google Cloud Trace")
    print("=" * 70)
    print()

    # Create client
    print(f"Connecting to Cloud Trace API...")
    print(f"Project: {PROJECT_ID}")
    print(f"Service: {SERVICE_NAME}")
    print()

    client = trace_v1.TraceServiceClient()

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours_ago)

    print(f"Time range:")
    print(f"  Start: {start_time.isoformat()}Z")
    print(f"  End: {end_time.isoformat()}Z")
    print()

    # List traces
    print(f"Fetching traces...")
    print("-" * 70)

    try:
        project_name = f"projects/{PROJECT_ID}"

        # List traces for the project using correct API
        request = trace_v1.ListTracesRequest(
            project_id=PROJECT_ID,
            view=trace_v1.ListTracesRequest.ViewType.COMPLETE
        )

        traces = client.list_traces(request=request)

        trace_count = 0
        traces_data = []

        for trace in traces:
            trace_count += 1

            print(f"\nTrace #{trace_count}")
            print("-" * 70)
            print(f"Trace ID: {trace.trace_id}")
            print(f"Project: {trace.project_id}")

            # Get spans
            if trace.spans:
                print(f"Spans: {len(trace.spans)}")

                for i, span in enumerate(trace.spans, 1):
                    print(f"\n  Span #{i}:")
                    print(f"    Span ID: {span.span_id}")
                    print(f"    Name: {span.name}")
                    print(f"    Kind: {span.kind}")

                    # Start and end time
                    if span.start_time:
                        print(f"    Start: {span.start_time}")
                    if span.end_time:
                        print(f"    End: {span.end_time}")

                    # Labels
                    if hasattr(span, 'labels') and span.labels:
                        print(f"    Labels:")
                        for key, value in span.labels.items():
                            print(f"      {key}: {value}")

            # Store trace data
            trace_data = {
                "trace_id": trace.trace_id,
                "project_id": trace.project_id,
                "spans": []
            }

            for span in trace.spans:
                span_data = {
                    "span_id": span.span_id,
                    "name": span.name,
                    "kind": str(span.kind),
                    "start_time": str(span.start_time) if span.start_time else None,
                    "end_time": str(span.end_time) if span.end_time else None,
                    "attributes": {}
                }

                if hasattr(span, 'labels') and span.labels:
                    span_data["labels"] = dict(span.labels)

                trace_data["spans"].append(span_data)

            traces_data.append(trace_data)

            if trace_count >= max_results:
                break

        print()
        print("=" * 70)
        print(f"Summary: Found {trace_count} trace(s)")
        print("=" * 70)
        print()

        # Save to JSON file in traces folder
        if traces_data:
            output_file = f"traces/traces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(traces_data, f, indent=2)
            print(f"Traces saved to: {output_file}")
        else:
            print("No traces found in the specified time range")

        return traces_data

    except Exception as e:
        print(f"[ERROR] Failed to fetch traces: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_trace_by_id(trace_id):
    """
    Get specific trace by ID

    Args:
        trace_id: The trace ID to fetch
    """
    print("=" * 70)
    print(f"Fetching Trace ID: {trace_id}")
    print("=" * 70)
    print()

    client = trace_v1.TraceServiceClient()

    try:
        trace_name = f"projects/{PROJECT_ID}/traces/{trace_id}"
        trace = client.get_trace(name=trace_name)

        print(f"Trace ID: {trace.trace_id}")
        print(f"Project: {trace.project_id}")
        print(f"Spans: {len(trace.spans)}")
        print()

        for i, span in enumerate(trace.spans, 1):
            print(f"Span #{i}:")
            print(f"  Span ID: {span.span_id}")
            print(f"  Name: {span.name}")
            print(f"  Kind: {span.kind}")

            if span.attributes and span.attributes.attribute_map:
                print(f"  Attributes:")
                for key, value in span.attributes.attribute_map.items():
                    print(f"    {key}: {value.string_value.value if value.string_value else value}")
            print()

        return trace

    except Exception as e:
        print(f"[ERROR] Failed to fetch trace: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Google Cloud Trace API Client")
    print()

    # Fetch recent traces
    traces = fetch_traces(hours_ago=1, max_results=10)

    print()
    print("To fetch a specific trace by ID:")
    print('  python fetch_traces.py <trace_id>')
    print()
