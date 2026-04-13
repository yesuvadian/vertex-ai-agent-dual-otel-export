import json
import sys

machines = {}
filename = 'portal26_otel_agent_logs_20260410_083554.jsonl'

with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

# Split by "}\n{" pattern to separate JSON objects
json_objects = content.replace('}\n{', '}|||{').split('|||')

for json_str in json_objects:
    try:
        data = json.loads(json_str)

        # Check for resourceLogs (logs format)
        for rl in data.get('resourceLogs', []):
            attrs = {}
            for attr in rl.get('resource', {}).get('attributes', []):
                key = attr.get('key', '')
                value = attr.get('value', {})
                if 'stringValue' in value:
                    attrs[key] = value['stringValue']
                elif 'intValue' in value:
                    attrs[key] = str(value['intValue'])

            # Extract identifying info
            service = attrs.get('service.name', 'unknown')
            service_version = attrs.get('service.version', 'N/A')
            user_id = attrs.get('portal26.user.id', 'N/A')
            os_type = attrs.get('os.type', 'N/A')
            os_version = attrs.get('os.version', 'N/A')
            host_arch = attrs.get('host.arch', 'N/A')

            # Use session ID from log records as machine identifier
            session_ids = set()
            terminal_types = set()
            for scopeLog in rl.get('scopeLogs', []):
                for log in scopeLog.get('logRecords', []):
                    for attr in log.get('attributes', []):
                        if attr.get('key') == 'session.id':
                            if 'stringValue' in attr.get('value', {}):
                                session_ids.add(attr['value']['stringValue'])
                        if attr.get('key') == 'terminal.type':
                            if 'stringValue' in attr.get('value', {}):
                                terminal_types.add(attr['value']['stringValue'])

            session_id = list(session_ids)[0] if session_ids else 'N/A'
            terminal_type = list(terminal_types)[0] if terminal_types else 'N/A'

            key_str = f'{user_id}|{service}|{os_type}|{os_version}|{host_arch}|{session_id}'
            if key_str not in machines:
                machines[key_str] = {
                    'user_id': user_id,
                    'service': service,
                    'service_version': service_version,
                    'os_type': os_type,
                    'os_version': os_version,
                    'host_arch': host_arch,
                    'terminal_type': terminal_type,
                    'session_id': session_id,
                    'count': 0
                }
            machines[key_str]['count'] += 1

    except json.JSONDecodeError as e:
        # Skip malformed JSON
        continue

print('=' * 100)
print('MACHINES POSTING TO OTEL (Last 5 minutes)')
print('=' * 100)
for key_str, info in sorted(machines.items(), key=lambda x: -x[1]['count']):
    print()
    print(f"User: {info['user_id']}")
    print(f"Service: {info['service']} (v{info['service_version']})")
    print(f"OS: {info['os_type']} {info['os_version']} ({info['host_arch']})")
    print(f"Terminal: {info['terminal_type']}")
    print(f"Session ID: {info['session_id'][:16]}...")
    print(f"Log Records: {info['count']}")
    print('-' * 100)

print(f"\nTotal unique machine/session combinations: {len(machines)}")
print(f"\nNOTE: Hostname/machine name is NOT available in the telemetry data.")
print(f"Machines are identified by: User + OS + Session ID combination.")
print(f"Session ID represents a single Claude Code CLI/Desktop session.")
