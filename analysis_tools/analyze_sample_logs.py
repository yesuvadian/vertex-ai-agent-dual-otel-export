"""Analyze sample logs from file"""
import json
from collections import defaultdict, Counter
from datetime import datetime

# Load logs
with open('sample_logs.json', 'r') as f:
    logs = json.load(f)

print("="*80)
print("REAL LOG ANALYSIS - From Your Actual Reasoning Engine")
print("="*80)
print(f"Total logs found: {len(logs)}")
print("")

# Group by trace
traces = defaultdict(list)
for log in logs:
    trace_id = log.get('trace', 'unknown')
    if '/' in trace_id:
        trace_id = trace_id.split('/')[-1]
    traces[trace_id].append(log)

print(f"Total traces (invocations): {len(traces)}")
print("")

# Analyze each trace
trace_stats = []
for trace_id, trace_logs in traces.items():
    # Sort by timestamp
    trace_logs.sort(key=lambda x: x.get('timestamp', ''))

    # Calculate stats
    severities = Counter(log.get('severity', 'INFO') for log in trace_logs)

    # Calculate size
    total_size = sum(len(json.dumps(log)) for log in trace_logs)

    # Get timestamps
    timestamps = [log.get('timestamp') for log in trace_logs if log.get('timestamp')]
    duration = None
    if len(timestamps) >= 2:
        start = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
        end = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
        duration = (end - start).total_seconds()

    # Count spans
    spans = set(log.get('spanId') for log in trace_logs if log.get('spanId'))

    trace_stats.append({
        'trace_id': trace_id,
        'log_count': len(trace_logs),
        'span_count': len(spans),
        'duration': duration,
        'size_bytes': total_size,
        'severities': dict(severities)
    })

# Sort by log count
trace_stats.sort(key=lambda x: x['log_count'], reverse=True)

print("AGGREGATE STATISTICS:")
print("-"*80)
total_logs = sum(t['log_count'] for t in trace_stats)
avg_logs = total_logs / len(trace_stats) if trace_stats else 0
print(f"Total Logs: {total_logs}")
print(f"Avg Logs per Invocation: {avg_logs:.1f}")

total_spans = sum(t['span_count'] for t in trace_stats)
avg_spans = total_spans / len(trace_stats) if trace_stats else 0
print(f"Total Unique Spans: {total_spans}")
print(f"Avg Spans per Invocation: {avg_spans:.1f}")

durations = [t['duration'] for t in trace_stats if t['duration']]
if durations:
    print(f"\nDURATION STATISTICS:")
    print(f"  Min: {min(durations):.3f}s")
    print(f"  Max: {max(durations):.3f}s")
    print(f"  Avg: {sum(durations)/len(durations):.3f}s")

sizes = [t['size_bytes'] for t in trace_stats]
if sizes:
    print(f"\nSIZE STATISTICS:")
    print(f"  Min: {min(sizes)} bytes ({min(sizes)/1024:.1f} KB)")
    print(f"  Max: {max(sizes)} bytes ({max(sizes)/1024:.1f} KB)")
    print(f"  Avg: {sum(sizes)/len(sizes):.0f} bytes ({sum(sizes)/len(sizes)/1024:.1f} KB)")

print("")
print("="*80)
print("DETAILED TRACE BREAKDOWN (Top 5):")
print("="*80)

for i, trace in enumerate(trace_stats[:5], 1):
    print(f"\nTrace {i}:")
    print(f"  ID: {trace['trace_id'][:40]}...")
    print(f"  Logs: {trace['log_count']}")
    print(f"  Spans: {trace['span_count']}")
    if trace['duration']:
        print(f"  Duration: {trace['duration']:.3f}s")
    print(f"  Size: {trace['size_bytes']} bytes ({trace['size_bytes']/1024:.1f} KB)")
    print(f"  Severities: {trace['severities']}")

print("")
print("="*80)
print("KEY INSIGHTS FOR YOUR SYSTEM:")
print("="*80)

if trace_stats:
    avg_size_kb = (sum(sizes)/len(sizes))/1024
    print(f"\n1. LOG VOLUME:")
    print(f"   - Average {avg_logs:.0f} logs per invocation")
    print(f"   - Average {avg_size_kb:.1f} KB per invocation")
    print(f"   - For 1000 invocations/day: {avg_size_kb * 1000 / 1024:.1f} MB/day")
    print(f"   - Monthly estimate: {avg_size_kb * 1000 * 30 / 1024:.1f} GB/month")

    print(f"\n2. ROUTING RECOMMENDATION:")
    if avg_size_kb < 50:
        print(f"   - Most invocations < 50 KB -> Portal26")
        print(f"   - Threshold: SMALL_LOG_THRESHOLD=51200 (50 KB)")
    elif avg_size_kb < 100:
        print(f"   - Most invocations < 100 KB -> Portal26")
        print(f"   - Some invocations may need Kinesis")
        print(f"   - Threshold: SMALL_LOG_THRESHOLD=102400 (100 KB)")
    else:
        print(f"   - Large invocations -> Consider Kinesis/S3")
        print(f"   - Threshold: SMALL_LOG_THRESHOLD={int(avg_size_kb * 1024 * 0.8)} ({avg_size_kb * 0.8:.0f} KB)")

    if durations:
        avg_dur = sum(durations)/len(durations)
        print(f"\n3. PERFORMANCE:")
        print(f"   - Average duration: {avg_dur:.2f}s")
        if avg_dur < 2:
            print(f"   - Performance: GOOD (< 2s)")
        elif avg_dur < 5:
            print(f"   - Performance: ACCEPTABLE (2-5s)")
        else:
            print(f"   - Performance: NEEDS OPTIMIZATION (> 5s)")

print("\n" + "="*80)
