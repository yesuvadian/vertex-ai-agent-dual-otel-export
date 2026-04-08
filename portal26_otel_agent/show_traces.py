"""
Show traces from Portal26 logs (handles pretty-printed JSON)
"""
import json
import re

LOG_FILE = "portal26_otel_agent_logs_20260407_125530.jsonl"

print("=" * 80)
print("ANALYZING PORTAL26 LOGS")
print("=" * 80)
print()

# Read entire file and split by records
with open(LOG_FILE, 'r') as f:
    content = f.read()

# Split by '}\n{' pattern (records separated by newlines)
records_raw = re.split(r'\}\n\{', content)

traces = []
logs = []

for record_str in records_raw:
    # Fix the split (add back the braces)
    if not record_str.startswith('{'):
        record_str = '{' + record_str
    if not record_str.endswith('}'):
        record_str = record_str + '}'

    try:
        data = json.loads(record_str)

        if 'resourceSpans' in data:
            traces.append(data)
        elif 'resourceLogs' in data:
            logs.append(data)
    except:
        pass

print(f"Found: {len(traces)} traces, {len(logs)} logs")
print()

# Show traces
if traces:
    print("=" * 80)
    print("TRACES")
    print("=" * 80)

    for i, trace in enumerate(traces[:3], 1):  # First 3 traces
        print(f"\n--- TRACE #{i} ---")

        try:
            rs = trace['resourceSpans'][0]

            # Service name
            service = "unknown"
            for attr in rs['resource']['attributes']:
                if attr['key'] == 'service.name':
                    service = attr['value']['stringValue']

            print(f"Service: {service}")

            # Spans
            spans = rs['scopeSpans'][0]['spans']
            print(f"Spans: {len(spans)}")

            for span in spans:
                name = span['name']
                trace_id = span['traceId']
                span_id = span['spanId']

                start_ns = int(span['startTimeUnixNano'])
                end_ns = int(span['endTimeUnixNano'])
                duration_ms = (end_ns - start_ns) / 1_000_000

                print(f"\n  Span: {name}")
                print(f"    Trace ID: {trace_id}")
                print(f"    Span ID: {span_id}")
                print(f"    Duration: {duration_ms:.2f}ms")

                # Attributes
                if 'attributes' in span:
                    print(f"    Attributes:")
                    for attr in span['attributes'][:3]:
                        key = attr['key']
                        val = attr['value'].get('stringValue', attr['value'].get('intValue', ''))
                        print(f"      {key}: {val}")

        except Exception as e:
            print(f"  Error: {e}")

print("\n" + "=" * 80)

# Show logs
if logs:
    print("LOGS")
    print("=" * 80)

    for i, log in enumerate(logs[:3], 1):  # First 3 logs
        print(f"\n--- LOG #{i} ---")

        try:
            rl = log['resourceLogs'][0]

            # Service name
            service = "unknown"
            for attr in rl['resource']['attributes']:
                if attr['key'] == 'service.name':
                    service = attr['value']['stringValue']

            print(f"Service: {service}")

            # Log records
            log_records = rl['scopeLogs'][0]['logRecords']
            print(f"Records: {len(log_records)}")

            for rec in log_records[:2]:
                timestamp = rec['timeUnixNano']
                severity = rec.get('severityText', 'INFO')
                body = rec['body'].get('stringValue', '')

                print(f"\n  [{severity}] {body[:100]}")

        except Exception as e:
            print(f"  Error: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total Traces: {len(traces)}")
print(f"Total Logs: {len(logs)}")
print()

# Check for your agent's query
print("Search for 'bengaluru' or 'new york' queries:")
for i, trace in enumerate(traces):
    trace_str = json.dumps(trace).lower()
    if 'bengaluru' in trace_str or 'new york' in trace_str:
        print(f"  Trace #{i+1} contains query data")

print()
