"""
View and analyze traces from Google Cloud Trace
"""
from google.cloud import trace_v1
from datetime import datetime, timedelta
import json
import argparse
import os


# Load configuration from .env file
def load_config():
    """Load configuration from .env file"""
    config = {
        'PROJECT_ID': 'agentic-ai-integration-490716',
        'SERVICE_NAME': 'gcp_traces_agent',
        'FILTER_BY_AGENT': 'true',
        'DEFAULT_HOURS': '1',
        'DEFAULT_LIMIT': '10'
    }

    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

    return config

_config = load_config()
PROJECT_ID = _config['PROJECT_ID']
SERVICE_NAME = _config['SERVICE_NAME']


def format_duration(start_time, end_time):
    """Calculate duration between two timestamps"""
    if not start_time or not end_time:
        return "N/A"

    try:
        # Handle DatetimeWithNanoseconds objects
        if hasattr(start_time, 'timestamp'):
            start = start_time.timestamp()
        else:
            start = start_time.seconds + start_time.nanos / 1e9

        if hasattr(end_time, 'timestamp'):
            end = end_time.timestamp()
        else:
            end = end_time.seconds + end_time.nanos / 1e9

        duration_ms = (end - start) * 1000
        return f"{duration_ms:.2f}ms"
    except Exception as e:
        return f"N/A ({e})"


def display_trace_tree(trace):
    """Display trace as a hierarchical tree"""
    print(f"\nTrace ID: {trace.trace_id}")
    print("=" * 70)

    if not trace.spans:
        print("No spans found")
        return

    # Build span hierarchy
    spans_by_id = {span.span_id: span for span in trace.spans}
    root_spans = [span for span in trace.spans if not span.parent_span_id]

    def print_span(span, indent=0):
        prefix = "  " * indent + ("|- " if indent > 0 else "")

        # Get labels (Cloud Trace uses labels, not attributes)
        attrs = {}
        if hasattr(span, 'labels') and span.labels:
            attrs = dict(span.labels)

        duration = format_duration(span.start_time, span.end_time)

        print(f"{prefix}{span.name} [{duration}]")

        # Show important attributes
        if 'query.text' in attrs:
            print(f"{'  ' * (indent + 1)}Query: {attrs['query.text']}")
        if 'llm.model' in attrs:
            print(f"{'  ' * (indent + 1)}Model: {attrs['llm.model']}")
        if 'tool.name' in attrs:
            print(f"{'  ' * (indent + 1)}Tool: {attrs['tool.name']}")
        if 'tool.input.city' in attrs:
            print(f"{'  ' * (indent + 1)}Input: city={attrs['tool.input.city']}")
        if 'tool.output' in attrs:
            print(f"{'  ' * (indent + 1)}Output: {attrs['tool.output']}")

        # Find and print child spans
        child_spans = [s for s in trace.spans if s.parent_span_id == span.span_id]
        for child in child_spans:
            print_span(child, indent + 1)

    # Print all root spans and their children
    for root_span in root_spans:
        print_span(root_span)
        print()


def list_recent_traces(hours=1, limit=10, filter_agent=True):
    """List recent traces, optionally filtered by agent"""
    print("=" * 70)
    print("Recent Traces from Google Cloud Trace")
    print("=" * 70)
    print(f"Project: {PROJECT_ID}")
    print(f"Service: {SERVICE_NAME}")
    if filter_agent:
        print(f"Filter: Only traces from {SERVICE_NAME}")
    print(f"Time Range: Last {hours} hour(s)")
    print()

    client = trace_v1.TraceServiceClient()

    try:
        project_name = f"projects/{PROJECT_ID}"

        # List traces using correct API
        request = trace_v1.ListTracesRequest(
            project_id=PROJECT_ID,
            view=trace_v1.ListTracesRequest.ViewType.COMPLETE
        )

        traces = client.list_traces(request=request)

        trace_count = 0
        all_traces = []

        for trace in traces:
            # Filter by agent if requested
            if filter_agent:
                # Check if trace belongs to gcp_traces_agent
                is_our_agent = False
                for span in trace.spans:
                    if hasattr(span, 'labels') and span.labels:
                        agent_name = span.labels.get('gen_ai.agent.name', '')
                        if agent_name == SERVICE_NAME:
                            is_our_agent = True
                            break

                # Skip traces from other agents
                if not is_our_agent:
                    continue

            trace_count += 1
            all_traces.append(trace)

            display_trace_tree(trace)

            if trace_count >= limit:
                break

        print("=" * 70)
        print(f"Total traces found: {trace_count}")
        print("=" * 70)

        return all_traces

    except Exception as e:
        print(f"[ERROR] Failed to list traces: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_trace_details(trace_id):
    """Get detailed information about a specific trace"""
    print("=" * 70)
    print(f"Trace Details: {trace_id}")
    print("=" * 70)
    print()

    client = trace_v1.TraceServiceClient()

    try:
        trace_name = f"projects/{PROJECT_ID}/traces/{trace_id}"
        trace = client.get_trace(name=trace_name)

        display_trace_tree(trace)

        # Show all attributes
        print("\nDetailed Span Attributes:")
        print("-" * 70)

        for i, span in enumerate(trace.spans, 1):
            print(f"\nSpan #{i}: {span.name}")
            print(f"  Span ID: {span.span_id}")
            print(f"  Parent: {span.parent_span_id if span.parent_span_id else 'None (root)'}")
            print(f"  Kind: {span.kind}")
            print(f"  Duration: {format_duration(span.start_time, span.end_time)}")

            if hasattr(span, 'labels') and span.labels:
                print(f"  Labels:")
                for key, value in span.labels.items():
                    print(f"    {key}: {value}")

        return trace

    except Exception as e:
        print(f"[ERROR] Failed to get trace: {e}")
        import traceback
        traceback.print_exc()
        return None


def export_traces_to_json(output_file="traces_export.json", hours=1, limit=10, filter_agent=True):
    """Export traces to JSON file"""
    print(f"Exporting traces to {output_file}...")
    if filter_agent:
        print(f"Filter: Only traces from {SERVICE_NAME}")

    client = trace_v1.TraceServiceClient()

    try:
        # List traces using correct API
        request = trace_v1.ListTracesRequest(
            project_id=PROJECT_ID,
            view=trace_v1.ListTracesRequest.ViewType.COMPLETE
        )

        traces = client.list_traces(request=request)

        traces_data = []
        trace_count = 0

        for trace in traces:
            # Filter by agent if requested
            if filter_agent:
                is_our_agent = False
                for span in trace.spans:
                    if hasattr(span, 'labels') and span.labels:
                        agent_name = span.labels.get('gen_ai.agent.name', '')
                        if agent_name == SERVICE_NAME:
                            is_our_agent = True
                            break
                if not is_our_agent:
                    continue

            trace_count += 1
            trace_count += 1

            trace_data = {
                "trace_id": trace.trace_id,
                "project_id": trace.project_id,
                "spans": []
            }

            for span in trace.spans:
                span_data = {
                    "span_id": span.span_id,
                    "parent_span_id": span.parent_span_id,
                    "name": span.name,
                    "kind": str(span.kind),
                    "start_time": str(span.start_time) if span.start_time else None,
                    "end_time": str(span.end_time) if span.end_time else None,
                    "duration_ms": format_duration(span.start_time, span.end_time),
                    "labels": {}
                }

                if hasattr(span, 'labels') and span.labels:
                    span_data["labels"] = dict(span.labels)

                trace_data["spans"].append(span_data)

            traces_data.append(trace_data)

            if trace_count >= limit:
                break

        with open(output_file, 'w') as f:
            json.dump(traces_data, f, indent=2)

        print(f"[OK] Exported {trace_count} trace(s) to {output_file}")
        return traces_data

    except Exception as e:
        print(f"[ERROR] Failed to export traces: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View Google Cloud Trace data")
    parser.add_argument("--trace-id", help="Get details for specific trace ID")
    parser.add_argument("--hours", type=int, default=1, help="Hours to look back (default: 1)")
    parser.add_argument("--limit", type=int, default=10, help="Max traces to fetch (default: 10)")
    parser.add_argument("--export", help="Export traces to JSON file")
    parser.add_argument("--no-filter", action="store_true", help="Fetch traces from ALL agents (not just gcp_traces_agent)")

    args = parser.parse_args()

    filter_agent = not args.no_filter  # Filter by default, unless --no-filter is specified

    if args.trace_id:
        get_trace_details(args.trace_id)
    elif args.export:
        export_traces_to_json(args.export, args.hours, args.limit, filter_agent)
    else:
        list_recent_traces(args.hours, args.limit, filter_agent)
