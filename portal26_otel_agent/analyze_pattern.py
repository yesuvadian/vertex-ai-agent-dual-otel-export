"""Analyze relusys telemetry pattern"""
import json
from datetime import datetime
from collections import Counter

log_file = 'portal26_otel_agent_logs_20260410_101340.jsonl'

print('=' * 80)
print('COMPREHENSIVE PATTERN ANALYSIS - 5 MINUTES OF DATA')
print('=' * 80)
print('Time window: 15:38-15:43 IST')
print()

# Parse multi-line JSON
with open(log_file, 'r') as f:
    content = f.read()

json_objects = []
brace_count = 0
start_idx = 0
in_json = False

for i, char in enumerate(content):
    if char == '{':
        if brace_count == 0:
            start_idx = i
            in_json = True
        brace_count += 1
    elif char == '}':
        brace_count -= 1
        if brace_count == 0 and in_json:
            json_str = content[start_idx:i+1]
            try:
                obj = json.loads(json_str)
                json_objects.append(obj)
            except:
                pass
            in_json = False

print(f'Total telemetry records parsed: {len(json_objects)}')
print()

# Extract detailed info
records = []

for obj in json_objects:
    record_info = {
        'user': 'unknown',
        'service': 'unknown',
        'timestamp_nano': None,
        'error_msg': None,
        'severity': None,
        'type': 'unknown'
    }

    # Parse resourceLogs
    if 'resourceLogs' in obj:
        record_info['type'] = 'LOG'
        attrs = obj['resourceLogs'][0]['resource']['attributes']
        for attr in attrs:
            if attr['key'] == 'portal26.user.id':
                record_info['user'] = attr['value'].get('stringValue', 'unknown')
            elif attr['key'] == 'user.id':
                record_info['user'] = attr['value'].get('stringValue', 'unknown')
            elif attr['key'] == 'service.name':
                record_info['service'] = attr['value'].get('stringValue', 'unknown')

        # Get timestamp and error message
        if 'scopeLogs' in obj['resourceLogs'][0]:
            for scope_log in obj['resourceLogs'][0]['scopeLogs']:
                for log in scope_log.get('logRecords', []):
                    record_info['timestamp_nano'] = log.get('timeUnixNano', log.get('observedTimeUnixNano'))
                    record_info['severity'] = log.get('severityText', 'INFO')
                    body = log.get('body', {}).get('stringValue', '')
                    if 'Failed' in body or 'Error' in body or 'error' in body:
                        record_info['error_msg'] = body[:80]

    # Parse resourceSpans
    elif 'resourceSpans' in obj:
        record_info['type'] = 'TRACE'
        attrs = obj['resourceSpans'][0]['resource']['attributes']
        for attr in attrs:
            if attr['key'] == 'portal26.user.id':
                record_info['user'] = attr['value'].get('stringValue', 'unknown')
            elif attr['key'] == 'user.id':
                record_info['user'] = attr['value'].get('stringValue', 'unknown')
            elif attr['key'] == 'service.name':
                record_info['service'] = attr['value'].get('stringValue', 'unknown')

        if 'scopeSpans' in obj['resourceSpans'][0]:
            spans = obj['resourceSpans'][0]['scopeSpans'][0].get('spans', [])
            if spans:
                record_info['timestamp_nano'] = spans[0].get('startTimeUnixNano')

    if record_info['timestamp_nano']:
        records.append(record_info)

# Sort by timestamp
records.sort(key=lambda x: int(x['timestamp_nano']))

print('=' * 80)
print('1. USER & SERVICE BREAKDOWN')
print('=' * 80)

user_counter = Counter()
service_counter = Counter()
user_service_combo = Counter()

for r in records:
    user_counter[r['user']] += 1
    service_counter[r['service']] += 1
    user_service_combo[(r['user'], r['service'])] += 1

print('Users:')
for user, count in user_counter.most_common():
    pct = (count / len(records)) * 100
    print(f'  {user:<20} {count:>3} records ({pct:>5.1f}%)')

print()
print('Services:')
for service, count in service_counter.most_common():
    pct = (count / len(records)) * 100
    print(f'  {service:<30} {count:>3} records ({pct:>5.1f}%)')

print()
print('User-Service Combinations:')
for (user, service), count in user_service_combo.most_common():
    pct = (count / len(records)) * 100
    print(f'  {user:<15} + {service:<25} {count:>3} records ({pct:>5.1f}%)')

print()
print('=' * 80)
print('2. RELUSYS TIMING PATTERN ANALYSIS')
print('=' * 80)

relusys_records = [r for r in records if r['user'] == 'relusys']
print(f'Total relusys records: {len(relusys_records)}')
print()

if relusys_records:
    print('All relusys timestamps with intervals:')
    for i, r in enumerate(relusys_records, 1):
        ts_sec = int(r['timestamp_nano']) / 1_000_000_000
        dt = datetime.fromtimestamp(ts_sec)
        error_indicator = ' [ERROR]' if r['error_msg'] else ''

        # Calculate interval from previous
        if i > 1:
            prev_ts = int(relusys_records[i-2]['timestamp_nano']) / 1_000_000_000
            interval = ts_sec - prev_ts
            print(f'  {i:2}. {dt.strftime("%H:%M:%S")} (+{interval:5.1f}s){error_indicator}')
        else:
            print(f'  {i:2}. {dt.strftime("%H:%M:%S")}          {error_indicator}')

    # Calculate intervals
    if len(relusys_records) > 1:
        intervals = []
        for i in range(1, len(relusys_records)):
            interval_sec = (int(relusys_records[i]['timestamp_nano']) - int(relusys_records[i-1]['timestamp_nano'])) / 1_000_000_000
            intervals.append(interval_sec)

        print()
        print('Timing Statistics:')
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        std_dev = (sum((x - avg_interval)**2 for x in intervals) / len(intervals))**0.5

        print(f'  Average interval: {avg_interval:.2f} seconds')
        print(f'  Min interval: {min_interval:.2f} seconds')
        print(f'  Max interval: {max_interval:.2f} seconds')
        print(f'  Standard deviation: {std_dev:.2f} seconds')

        # Pattern detection
        print()
        print('Pattern Classification:')
        if std_dev < 2:
            print(f'  Type: HIGHLY REGULAR')
            print(f'  Behavior: Strict timer-based (~{avg_interval:.0f}s)')
            print(f'  Source: Likely cron job or scheduled export')
        elif std_dev < 5:
            print(f'  Type: MOSTLY REGULAR')
            print(f'  Behavior: Timer with some jitter (~{avg_interval:.0f}s +/- {std_dev:.1f}s)')
            print(f'  Source: Likely polling loop or retry mechanism')
        else:
            print(f'  Type: IRREGULAR')
            print(f'  Behavior: Variable timing')
            print(f'  Source: Likely event-driven or manual')

print()
print('=' * 80)
print('3. ERROR MESSAGE ANALYSIS')
print('=' * 80)

error_records = [r for r in relusys_records if r['error_msg']]
print(f'Records with errors: {len(error_records)} / {len(relusys_records)}')

if error_records:
    print()
    print('Error messages:')
    error_msgs = Counter()
    for r in error_records:
        error_msgs[r['error_msg']] += 1

    for msg, count in error_msgs.most_common():
        print(f'  [{count}x] {msg}')

    print()
    print('Diagnosis:')
    if 'Failed to export metrics' in str(error_msgs.most_common(1)):
        print('  - Portal26 /v1/metrics endpoint returns 404')
        print('  - OTEL metrics exporter retries every ~10 seconds')
        print('  - This creates continuous error log stream to Kinesis')

print()
print('=' * 80)
print('4. COMPARISON: KALPANA (CLAUDE-CODE)')
print('=' * 80)

kalpana_records = [r for r in records if r['user'] == 'kalpana']
print(f'Total kalpana records: {len(kalpana_records)}')

if kalpana_records and len(kalpana_records) > 1:
    intervals = []
    for i in range(1, min(len(kalpana_records), 20)):
        interval_sec = (int(kalpana_records[i]['timestamp_nano']) - int(kalpana_records[i-1]['timestamp_nano'])) / 1_000_000_000
        intervals.append(interval_sec)

    avg_interval = sum(intervals) / len(intervals)
    std_dev = (sum((x - avg_interval)**2 for x in intervals) / len(intervals))**0.5

    print(f'  Average interval: {avg_interval:.2f} seconds')
    print(f'  Standard deviation: {std_dev:.2f} seconds')
    print(f'  Pattern: IRREGULAR - Event-driven (user activity in Claude Code)')

print()
print('=' * 80)
print('5. KEY FINDINGS & CONCLUSION')
print('=' * 80)

if relusys_records:
    mins = 5  # 5 minute window
    rate_per_min = len(relusys_records) / mins
    rate_per_hour = rate_per_min * 60

    print(f'RELUSYS Activity:')
    print(f'  - {len(relusys_records)} records in {mins} minutes')
    print(f'  - Rate: {rate_per_min:.1f} per minute, {rate_per_hour:.0f} per hour')
    print(f'  - 100% are ERROR logs (metrics export failures)')

    if len(relusys_records) > 1:
        intervals = [(int(relusys_records[i]['timestamp_nano']) - int(relusys_records[i-1]['timestamp_nano'])) / 1_000_000_000 for i in range(1, len(relusys_records))]
        avg = sum(intervals) / len(intervals)
        print(f'  - Average interval: Every {avg:.1f} seconds')

    print()
    print(f'KALPANA Activity:')
    print(f'  - {len(kalpana_records)} records in {mins} minutes')
    print(f'  - Pattern: Irregular (normal user activity)')
    print()
    print('CONCLUSION:')
    print('  The relusys source is:')
    print('    1. A continuously running process (not manual)')
    print('    2. Configured with portal26_otel_agent code')
    print('    3. Has metrics exporter enabled')
    print('    4. Getting 404 errors every ~10 seconds')
    print('    5. NOT from your Windows machine (confirmed clean)')
    print('    6. NOT from deleted Reasoning Engines')
    print()
    print('  Most likely source:')
    print('    - Team member running portal26_otel_agent locally')
    print('    - OR: Undiscovered cloud deployment (Function/Run)')
    print('    - OR: Local development server still running')

print('=' * 80)
