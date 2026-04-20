"""
Log and Trace Pattern Analyzer
Analyzes GCP Reasoning Engine logs to understand:
- How many logs per agent invocation
- Trace structure and spans
- Log types and severity patterns
- Timing and latency patterns
"""
import json
import time
from datetime import datetime, timezone
from collections import defaultdict, Counter
from google.cloud import pubsub_v1
from dotenv import load_dotenv
import os
import sys

load_dotenv()

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "agentic-ai-integration-490716")
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "vertex-telemetry-subscription")
ANALYSIS_DURATION = int(os.environ.get("ANALYSIS_DURATION", "300"))  # 5 minutes default

# Data structures for analysis
traces = defaultdict(lambda: {
    'logs': [],
    'spans': defaultdict(list),
    'start_time': None,
    'end_time': None,
    'severity_counts': Counter(),
    'log_types': Counter(),
    'reasoning_engine_id': None,
    'customer_project': None
})

invocation_stats = []
running = True

def extract_trace_info(log_entry):
    """Extract trace and span information"""
    trace_id = None
    span_id = None

    if 'trace' in log_entry:
        trace = log_entry['trace']
        if '/' in trace:
            trace_id = trace.split('/')[-1]
        else:
            trace_id = trace

    if 'spanId' in log_entry:
        span_id = log_entry['spanId']

    return trace_id, span_id

def extract_timing(log_entry):
    """Extract timing information"""
    if 'timestamp' in log_entry:
        return datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
    return datetime.now(timezone.utc)

def classify_log_type(log_entry):
    """Classify the type of log entry"""
    text_payload = log_entry.get('textPayload', '')
    json_payload = log_entry.get('jsonPayload', {})

    # Check for specific patterns
    if 'request' in text_payload.lower() or 'request' in json_payload:
        return 'request'
    elif 'response' in text_payload.lower() or 'response' in json_payload:
        return 'response'
    elif 'error' in text_payload.lower():
        return 'error'
    elif 'trace' in json_payload or 'span' in json_payload:
        return 'trace'
    elif 'metric' in json_payload:
        return 'metric'
    else:
        return 'general'

def analyze_log_entry(log_entry):
    """Analyze a single log entry"""
    trace_id, span_id = extract_trace_info(log_entry)

    if not trace_id:
        return  # Skip logs without trace

    # Get trace data
    trace_data = traces[trace_id]

    # Extract metadata
    resource = log_entry.get('resource', {})
    resource_labels = resource.get('labels', {})

    trace_data['reasoning_engine_id'] = resource_labels.get('reasoning_engine_id', 'unknown')
    trace_data['customer_project'] = resource_labels.get('project_id', 'unknown')

    # Add log to trace
    log_info = {
        'timestamp': extract_timing(log_entry),
        'severity': log_entry.get('severity', 'INFO'),
        'span_id': span_id,
        'log_type': classify_log_type(log_entry),
        'text_payload': log_entry.get('textPayload', ''),
        'json_payload': log_entry.get('jsonPayload', {}),
        'size': len(json.dumps(log_entry))
    }

    trace_data['logs'].append(log_info)

    # Update span information
    if span_id:
        trace_data['spans'][span_id].append(log_info)

    # Update counters
    trace_data['severity_counts'][log_info['severity']] += 1
    trace_data['log_types'][log_info['log_type']] += 1

    # Update timing
    if not trace_data['start_time'] or log_info['timestamp'] < trace_data['start_time']:
        trace_data['start_time'] = log_info['timestamp']
    if not trace_data['end_time'] or log_info['timestamp'] > trace_data['end_time']:
        trace_data['end_time'] = log_info['timestamp']

def generate_trace_report(trace_id, trace_data):
    """Generate detailed report for a trace"""
    logs = trace_data['logs']

    if not logs:
        return None

    # Sort logs by timestamp
    logs.sort(key=lambda x: x['timestamp'])

    # Calculate duration
    duration = None
    if trace_data['start_time'] and trace_data['end_time']:
        duration = (trace_data['end_time'] - trace_data['start_time']).total_seconds()

    # Calculate average log size
    total_size = sum(log['size'] for log in logs)
    avg_size = total_size / len(logs) if logs else 0

    report = {
        'trace_id': trace_id,
        'reasoning_engine_id': trace_data['reasoning_engine_id'],
        'customer_project': trace_data['customer_project'],
        'total_logs': len(logs),
        'unique_spans': len(trace_data['spans']),
        'duration_seconds': duration,
        'total_size_bytes': total_size,
        'avg_log_size_bytes': avg_size,
        'severity_distribution': dict(trace_data['severity_counts']),
        'log_type_distribution': dict(trace_data['log_types']),
        'logs_per_span': {
            span_id: len(span_logs)
            for span_id, span_logs in trace_data['spans'].items()
        },
        'timeline': [
            {
                'timestamp': log['timestamp'].isoformat(),
                'severity': log['severity'],
                'type': log['log_type'],
                'span_id': log['span_id']
            }
            for log in logs
        ]
    }

    return report

def print_statistics():
    """Print current statistics"""
    print("\n" + "="*80)
    print("CURRENT STATISTICS")
    print("="*80)
    print(f"Total traces captured: {len(traces)}")
    print(f"Time elapsed: {time.time() - start_time:.1f}s")
    print("")

    if traces:
        # Calculate aggregate statistics
        total_logs = sum(len(t['logs']) for t in traces.values())
        avg_logs_per_trace = total_logs / len(traces)

        all_severities = Counter()
        all_log_types = Counter()

        for trace_data in traces.values():
            all_severities.update(trace_data['severity_counts'])
            all_log_types.update(trace_data['log_types'])

        print(f"Total logs: {total_logs}")
        print(f"Average logs per trace: {avg_logs_per_trace:.1f}")
        print("")

        print("Severity Distribution:")
        for severity, count in all_severities.most_common():
            percentage = (count / total_logs * 100) if total_logs > 0 else 0
            print(f"  {severity:12s}: {count:5d} ({percentage:5.1f}%)")
        print("")

        print("Log Type Distribution:")
        for log_type, count in all_log_types.most_common():
            percentage = (count / total_logs * 100) if total_logs > 0 else 0
            print(f"  {log_type:12s}: {count:5d} ({percentage:5.1f}%)")
        print("")

        # Show recent traces
        recent_traces = sorted(
            [(tid, t) for tid, t in traces.items() if t['logs']],
            key=lambda x: x[1]['start_time'] if x[1]['start_time'] else datetime.min,
            reverse=True
        )[:5]

        if recent_traces:
            print("Recent Traces (last 5):")
            for i, (trace_id, trace_data) in enumerate(recent_traces, 1):
                duration = None
                if trace_data['start_time'] and trace_data['end_time']:
                    duration = (trace_data['end_time'] - trace_data['start_time']).total_seconds()

                print(f"\n  {i}. Trace: {trace_id[:16]}...")
                print(f"     Engine: {trace_data['reasoning_engine_id']}")
                print(f"     Logs: {len(trace_data['logs'])}")
                print(f"     Spans: {len(trace_data['spans'])}")
                if duration:
                    print(f"     Duration: {duration:.2f}s")
                print(f"     Severities: {dict(trace_data['severity_counts'])}")

        print("\n" + "="*80)

def generate_final_report():
    """Generate final comprehensive report"""
    print("\n" + "="*80)
    print("FINAL ANALYSIS REPORT")
    print("="*80)
    print(f"Analysis Duration: {ANALYSIS_DURATION}s")
    print(f"Total Traces: {len(traces)}")
    print("")

    # Generate individual trace reports
    trace_reports = []
    for trace_id, trace_data in traces.items():
        report = generate_trace_report(trace_id, trace_data)
        if report:
            trace_reports.append(report)

    if not trace_reports:
        print("No traces captured during analysis period.")
        return

    # Aggregate statistics
    total_logs = sum(r['total_logs'] for r in trace_reports)
    total_spans = sum(r['unique_spans'] for r in trace_reports)

    print("AGGREGATE STATISTICS:")
    print(f"  Total Invocations (Traces): {len(trace_reports)}")
    print(f"  Total Logs: {total_logs}")
    print(f"  Total Unique Spans: {total_spans}")
    print(f"  Avg Logs per Invocation: {total_logs / len(trace_reports):.1f}")
    print(f"  Avg Spans per Invocation: {total_spans / len(trace_reports):.1f}")

    # Duration statistics
    durations = [r['duration_seconds'] for r in trace_reports if r['duration_seconds']]
    if durations:
        print(f"\nDURATION STATISTICS:")
        print(f"  Min: {min(durations):.2f}s")
        print(f"  Max: {max(durations):.2f}s")
        print(f"  Avg: {sum(durations) / len(durations):.2f}s")

    # Size statistics
    sizes = [r['total_size_bytes'] for r in trace_reports]
    if sizes:
        print(f"\nSIZE STATISTICS:")
        print(f"  Min: {min(sizes)} bytes ({min(sizes)/1024:.1f} KB)")
        print(f"  Max: {max(sizes)} bytes ({max(sizes)/1024:.1f} KB)")
        print(f"  Avg: {sum(sizes) / len(sizes):.0f} bytes ({sum(sizes) / len(sizes) / 1024:.1f} KB)")

    # Detailed trace examples
    print("\n" + "="*80)
    print("DETAILED TRACE EXAMPLES:")
    print("="*80)

    # Show 3 example traces
    for i, report in enumerate(trace_reports[:3], 1):
        print(f"\nExample {i}:")
        print(f"  Trace ID: {report['trace_id']}")
        print(f"  Reasoning Engine: {report['reasoning_engine_id']}")
        print(f"  Customer Project: {report['customer_project']}")
        print(f"  Total Logs: {report['total_logs']}")
        print(f"  Unique Spans: {report['unique_spans']}")
        if report['duration_seconds']:
            print(f"  Duration: {report['duration_seconds']:.2f}s")
        print(f"  Total Size: {report['total_size_bytes']} bytes ({report['total_size_bytes']/1024:.1f} KB)")
        print(f"\n  Severity Distribution:")
        for severity, count in report['severity_distribution'].items():
            print(f"    {severity}: {count}")
        print(f"\n  Log Type Distribution:")
        for log_type, count in report['log_type_distribution'].items():
            print(f"    {log_type}: {count}")

        if report['logs_per_span']:
            print(f"\n  Logs per Span:")
            for span_id, count in sorted(report['logs_per_span'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    Span {span_id[:16]}...: {count} logs")

        # Show timeline summary
        if report['timeline']:
            print(f"\n  Timeline (first 5 logs):")
            for log in report['timeline'][:5]:
                print(f"    {log['timestamp']} | {log['severity']:8s} | {log['type']:10s}")

    # Save detailed report to file
    output_file = f"log_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_duration_seconds': ANALYSIS_DURATION,
            'total_traces': len(trace_reports),
            'aggregate_stats': {
                'total_logs': total_logs,
                'total_spans': total_spans,
                'avg_logs_per_invocation': total_logs / len(trace_reports) if trace_reports else 0,
                'avg_spans_per_invocation': total_spans / len(trace_reports) if trace_reports else 0,
                'duration_stats': {
                    'min': min(durations) if durations else None,
                    'max': max(durations) if durations else None,
                    'avg': sum(durations) / len(durations) if durations else None
                },
                'size_stats': {
                    'min_bytes': min(sizes) if sizes else None,
                    'max_bytes': max(sizes) if sizes else None,
                    'avg_bytes': sum(sizes) / len(sizes) if sizes else None
                }
            },
            'traces': trace_reports
        }, f, indent=2)

    print(f"\n\nDetailed report saved to: {output_file}")
    print("="*80)

def callback(message):
    """Process incoming Pub/Sub message"""
    try:
        log_entry = json.loads(message.data.decode('utf-8'))

        # Filter for Reasoning Engine logs
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')

        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            analyze_log_entry(log_entry)

        message.ack()

    except Exception as e:
        print(f"Error processing message: {e}")
        message.ack()

def main():
    """Main analysis loop"""
    global start_time, running

    start_time = time.time()

    print("="*80)
    print("LOG AND TRACE PATTERN ANALYZER")
    print("="*80)
    print(f"GCP Project:     {PROJECT_ID}")
    print(f"Subscription:    {SUBSCRIPTION_ID}")
    print(f"Analysis Duration: {ANALYSIS_DURATION}s")
    print("")
    print("Starting analysis...")
    print("Trigger your Reasoning Engine agent to generate logs!")
    print("")
    print("Press Ctrl+C to stop early and see results.")
    print("="*80)

    # Initialize Pub/Sub subscriber
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    # Start streaming pull
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    last_stats_time = time.time()

    try:
        while running and (time.time() - start_time) < ANALYSIS_DURATION:
            # Print stats every 30 seconds
            if time.time() - last_stats_time >= 30:
                print_statistics()
                last_stats_time = time.time()

            time.sleep(1)

        print("\n\nAnalysis duration reached. Generating final report...")

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted. Generating final report...")
    finally:
        # Stop subscriber
        streaming_pull_future.cancel()
        try:
            streaming_pull_future.result(timeout=5)
        except Exception:
            pass

        # Generate final report
        generate_final_report()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
