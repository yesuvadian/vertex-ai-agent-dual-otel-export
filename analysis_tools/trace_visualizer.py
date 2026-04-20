"""
Trace Visualizer
Creates visual timeline of logs and spans for a specific trace
"""
import json
import sys
from datetime import datetime

def load_trace_from_report(report_file, trace_index=0):
    """Load trace data from analysis report"""
    with open(report_file, 'r') as f:
        data = json.load(f)

    if not data['traces']:
        print("No traces found in report")
        return None

    if trace_index >= len(data['traces']):
        print(f"Trace index {trace_index} out of range (max: {len(data['traces'])-1})")
        return None

    return data['traces'][trace_index]

def visualize_trace(trace):
    """Create ASCII visualization of trace timeline"""
    print("\n" + "="*100)
    print("TRACE VISUALIZATION")
    print("="*100)
    print(f"Trace ID: {trace['trace_id']}")
    print(f"Reasoning Engine: {trace['reasoning_engine_id']}")
    print(f"Duration: {trace['duration_seconds']:.3f}s" if trace['duration_seconds'] else "Duration: Unknown")
    print(f"Total Logs: {trace['total_logs']}")
    print(f"Unique Spans: {trace['unique_spans']}")
    print("")

    # Print severity and type distribution
    print("Severity Distribution:")
    for severity, count in sorted(trace['severity_distribution'].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(count / trace['total_logs'] * 50)
        print(f"  {severity:12s} | {bar} {count}")
    print("")

    print("Log Type Distribution:")
    for log_type, count in sorted(trace['log_type_distribution'].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(count / trace['total_logs'] * 50)
        print(f"  {log_type:12s} | {bar} {count}")
    print("")

    # Timeline visualization
    timeline = trace['timeline']
    if not timeline:
        print("No timeline data available")
        return

    print("="*100)
    print("TIMELINE (chronological order)")
    print("="*100)
    print(f"{'#':>4s} | {'Time':>12s} | {'Delta':>8s} | {'Severity':^10s} | {'Type':^12s} | {'Span ID':^20s}")
    print("-"*100)

    start_time = datetime.fromisoformat(timeline[0]['timestamp'])

    for i, log in enumerate(timeline, 1):
        log_time = datetime.fromisoformat(log['timestamp'])
        delta = (log_time - start_time).total_seconds()

        # Color coding for severity (using symbols)
        severity_symbol = {
            'DEBUG': '·',
            'INFO': 'ℹ',
            'WARNING': '⚠',
            'ERROR': '✖',
            'CRITICAL': '‼'
        }.get(log['severity'], '?')

        # Truncate span ID
        span_id_short = log['span_id'][:18] if log['span_id'] else 'N/A'

        print(f"{i:4d} | {delta:10.3f}s | +{delta:7.3f}s | {severity_symbol} {log['severity']:8s} | {log['type']:12s} | {span_id_short:20s}")

    print("="*100)

    # Span breakdown
    if trace['logs_per_span']:
        print("\nSPAN BREAKDOWN:")
        print("-"*100)
        print(f"{'Span ID':^40s} | {'Logs':^10s} | {'Percentage':^12s}")
        print("-"*100)

        for span_id, count in sorted(trace['logs_per_span'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / trace['total_logs'] * 100) if trace['total_logs'] > 0 else 0
            span_id_display = span_id[:38] if len(span_id) > 38 else span_id
            bar = "█" * int(percentage / 2)  # Scale to 50 chars max
            print(f"{span_id_display:40s} | {count:^10d} | {percentage:5.1f}% {bar}")

        print("="*100)

def compare_traces(report_file, trace_indices):
    """Compare multiple traces side by side"""
    with open(report_file, 'r') as f:
        data = json.load(f)

    traces_to_compare = []
    for idx in trace_indices:
        if idx < len(data['traces']):
            traces_to_compare.append(data['traces'][idx])

    if len(traces_to_compare) < 2:
        print("Need at least 2 traces to compare")
        return

    print("\n" + "="*120)
    print("TRACE COMPARISON")
    print("="*120)
    print("")

    # Header
    print(f"{'Metric':30s}", end='')
    for i, trace in enumerate(traces_to_compare):
        print(f" | {'Trace ' + str(i+1):^25s}", end='')
    print("")
    print("-"*120)

    # Comparison metrics
    metrics = [
        ('Trace ID', lambda t: t['trace_id'][:23]),
        ('Engine ID', lambda t: t['reasoning_engine_id'][:23]),
        ('Total Logs', lambda t: str(t['total_logs'])),
        ('Unique Spans', lambda t: str(t['unique_spans'])),
        ('Duration (s)', lambda t: f"{t['duration_seconds']:.3f}" if t['duration_seconds'] else 'N/A'),
        ('Total Size (KB)', lambda t: f"{t['total_size_bytes']/1024:.1f}"),
        ('Avg Log Size (bytes)', lambda t: f"{t['avg_log_size_bytes']:.0f}"),
    ]

    for metric_name, metric_fn in metrics:
        print(f"{metric_name:30s}", end='')
        for trace in traces_to_compare:
            value = metric_fn(trace)
            print(f" | {value:^25s}", end='')
        print("")

    print("")
    print("Severity Distribution:")
    print("-"*120)

    # Get all severities
    all_severities = set()
    for trace in traces_to_compare:
        all_severities.update(trace['severity_distribution'].keys())

    for severity in sorted(all_severities):
        print(f"  {severity:28s}", end='')
        for trace in traces_to_compare:
            count = trace['severity_distribution'].get(severity, 0)
            percentage = (count / trace['total_logs'] * 100) if trace['total_logs'] > 0 else 0
            print(f" | {count:5d} ({percentage:5.1f}%)      ", end='')
        print("")

    print("")
    print("Log Type Distribution:")
    print("-"*120)

    # Get all log types
    all_types = set()
    for trace in traces_to_compare:
        all_types.update(trace['log_type_distribution'].keys())

    for log_type in sorted(all_types):
        print(f"  {log_type:28s}", end='')
        for trace in traces_to_compare:
            count = trace['log_type_distribution'].get(log_type, 0)
            percentage = (count / trace['total_logs'] * 100) if trace['total_logs'] > 0 else 0
            print(f" | {count:5d} ({percentage:5.1f}%)      ", end='')
        print("")

    print("="*120)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Visualize single trace:")
        print("    python trace_visualizer.py <report_file.json> [trace_index]")
        print("")
        print("  Compare multiple traces:")
        print("    python trace_visualizer.py <report_file.json> compare <trace_index1> <trace_index2> ...")
        print("")
        print("Example:")
        print("    python trace_visualizer.py log_analysis_report_20260420_143000.json 0")
        print("    python trace_visualizer.py log_analysis_report_20260420_143000.json compare 0 1 2")
        sys.exit(1)

    report_file = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == 'compare':
        # Compare mode
        trace_indices = [int(idx) for idx in sys.argv[3:]]
        compare_traces(report_file, trace_indices)
    else:
        # Single trace visualization
        trace_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        trace = load_trace_from_report(report_file, trace_index)

        if trace:
            visualize_trace(trace)

if __name__ == "__main__":
    main()
