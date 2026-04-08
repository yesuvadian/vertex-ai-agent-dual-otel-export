"""
Compare GenAI attributes between portal26_otel_agent and hardcoded-otel-deployed
Focus on LLM span attributes to identify differences
"""
import json
import re
import os
from collections import defaultdict

# File paths - find log files with traces
PORTAL26_LOG = None
HARDCODED_LOG = None

# Find log files - prioritize files with traces
portal26_candidates = []
hardcoded_candidates = []

for f in sorted(os.listdir('.'), reverse=True):
    if f.startswith('portal26_otel_agent_logs_') and f.endswith('.jsonl'):
        portal26_candidates.append(f)
    if f.startswith('hardcoded_otel_logs_') and f.endswith('.jsonl'):
        hardcoded_candidates.append(f)

# Use the file with traces (check file size as indicator)
if portal26_candidates:
    # Prefer larger files (more likely to have traces)
    portal26_candidates.sort(key=lambda f: os.path.getsize(f), reverse=True)
    PORTAL26_LOG = portal26_candidates[0]

if hardcoded_candidates:
    # Use latest hardcoded log
    HARDCODED_LOG = hardcoded_candidates[0]

if not PORTAL26_LOG:
    print("ERROR: No portal26_otel_agent log file found!")
    print("Expected: portal26_otel_agent_logs_YYYYMMDD_HHMMSS.jsonl")
    exit(1)

if not HARDCODED_LOG:
    print("ERROR: No hardcoded-otel log file found!")
    print("Expected: hardcoded_otel_logs_YYYYMMDD_HHMMSS.jsonl")
    exit(1)

print("=" * 80)
print("COMPARING GenAI ATTRIBUTES")
print("=" * 80)
print(f"Portal26 Agent: {PORTAL26_LOG}")
print(f"Hardcoded OTEL: {HARDCODED_LOG}")
print()


def parse_log_file(file_path):
    """Parse JSONL file and extract traces"""
    with open(file_path, 'r') as f:
        content = f.read()

    records_raw = re.split(r'\}\n\{', content)

    traces = []
    for record_str in records_raw:
        if not record_str.startswith('{'):
            record_str = '{' + record_str
        if not record_str.endswith('}'):
            record_str = record_str + '}'

        try:
            data = json.loads(record_str)
            if 'resourceSpans' in data:
                traces.append(data)
        except:
            pass

    return traces


def extract_genai_spans(traces):
    """Extract GenAI spans from traces"""
    genai_spans = []
    for trace in traces:
        try:
            rs = trace['resourceSpans'][0]
            service = "unknown"
            for attr in rs['resource']['attributes']:
                if attr['key'] == 'service.name':
                    service = attr['value']['stringValue']
                    break

            spans = rs['scopeSpans'][0]['spans']

            for span in spans:
                span_str = json.dumps(span).lower()
                # Look for GenAI spans
                if 'gen_ai' in span_str or 'gemini' in span_str or 'generate_content' in span['name']:
                    # Extract attributes
                    attrs = {}
                    if 'attributes' in span:
                        for attr in span['attributes']:
                            key = attr['key']
                            value = None
                            for val_type in ['stringValue', 'intValue', 'doubleValue', 'boolValue', 'arrayValue']:
                                if val_type in attr['value']:
                                    value = attr['value'][val_type]
                                    break
                            attrs[key] = value

                    genai_spans.append({
                        'service': service,
                        'span_name': span['name'],
                        'attributes': attrs
                    })
        except:
            pass

    return genai_spans


# Parse both log files
print("[1/4] Parsing portal26_otel_agent logs...")
portal26_traces = parse_log_file(PORTAL26_LOG)
portal26_genai = extract_genai_spans(portal26_traces)
print(f"  Found {len(portal26_traces)} traces, {len(portal26_genai)} GenAI spans")

print("[2/4] Parsing hardcoded-otel logs...")
hardcoded_traces = parse_log_file(HARDCODED_LOG)
hardcoded_genai = extract_genai_spans(hardcoded_traces)
print(f"  Found {len(hardcoded_traces)} traces, {len(hardcoded_genai)} GenAI spans")
print()

if not portal26_genai:
    print("ERROR: No GenAI spans found in portal26_otel_agent logs!")
    exit(1)

if not hardcoded_genai:
    print("ERROR: No GenAI spans found in hardcoded-otel logs!")
    exit(1)

# Compare attributes
print("[3/4] Comparing attributes...")
print()

# Collect all unique attribute keys
portal26_keys = set()
hardcoded_keys = set()

for span in portal26_genai:
    portal26_keys.update(span['attributes'].keys())

for span in hardcoded_genai:
    hardcoded_keys.update(span['attributes'].keys())

# Find differences
only_portal26 = portal26_keys - hardcoded_keys
only_hardcoded = hardcoded_keys - portal26_keys
common = portal26_keys & hardcoded_keys

print("=" * 80)
print("ATTRIBUTE COMPARISON")
print("=" * 80)
print()

print(f"Portal26 Agent: {len(portal26_keys)} unique attributes")
print(f"Hardcoded OTEL: {len(hardcoded_keys)} unique attributes")
print(f"Common: {len(common)} attributes")
print()

# Content capture specific attributes
CONTENT_CAPTURE_ATTRS = [
    'gen_ai.prompt',
    'gen_ai.request.messages',
    'gen_ai.completion',
    'gen_ai.response.content',
    'gen_ai.request.temperature',
    'gen_ai.request.top_p',
    'gen_ai.request.max_tokens',
]

print("=" * 80)
print("CONTENT CAPTURE ATTRIBUTES")
print("=" * 80)
print()

for attr in CONTENT_CAPTURE_ATTRS:
    portal26_has = attr in portal26_keys
    hardcoded_has = attr in hardcoded_keys

    status = ""
    if portal26_has and hardcoded_has:
        status = "[BOTH]    "
    elif portal26_has:
        status = "[P26 ONLY]"
    elif hardcoded_has:
        status = "[HC ONLY] "
    else:
        status = "[MISSING] "

    print(f"{status} {attr}")

print()
print("=" * 80)
print("ATTRIBUTES ONLY IN HARDCODED-OTEL")
print("=" * 80)
print()

if only_hardcoded:
    for attr in sorted(only_hardcoded):
        # Show sample value from first span
        sample_value = None
        for span in hardcoded_genai:
            if attr in span['attributes']:
                sample_value = span['attributes'][attr]
                break

        value_str = str(sample_value)
        if len(value_str) > 100:
            value_str = value_str[:100] + "..."

        print(f"  + {attr}")
        print(f"      Sample: {value_str}")
else:
    print("  (none)")

print()
print("=" * 80)
print("ATTRIBUTES ONLY IN PORTAL26_OTEL_AGENT")
print("=" * 80)
print()

if only_portal26:
    for attr in sorted(only_portal26):
        # Show sample value
        sample_value = None
        for span in portal26_genai:
            if attr in span['attributes']:
                sample_value = span['attributes'][attr]
                break

        value_str = str(sample_value)
        if len(value_str) > 100:
            value_str = value_str[:100] + "..."

        print(f"  + {attr}")
        print(f"      Sample: {value_str}")
else:
    print("  (none)")

print()
print("[4/4] Writing detailed comparison to file...")

# Write detailed JSON comparison
output = {
    "comparison_date": "2026-04-08",
    "files": {
        "portal26": PORTAL26_LOG,
        "hardcoded": HARDCODED_LOG
    },
    "summary": {
        "portal26_genai_spans": len(portal26_genai),
        "hardcoded_genai_spans": len(hardcoded_genai),
        "portal26_unique_attrs": len(portal26_keys),
        "hardcoded_unique_attrs": len(hardcoded_keys),
        "common_attrs": len(common)
    },
    "content_capture_status": {
        attr: {
            "portal26": attr in portal26_keys,
            "hardcoded": attr in hardcoded_keys
        }
        for attr in CONTENT_CAPTURE_ATTRS
    },
    "only_in_hardcoded": sorted(list(only_hardcoded)),
    "only_in_portal26": sorted(list(only_portal26)),
    "common_attributes": sorted(list(common)),
    "sample_spans": {
        "portal26": portal26_genai[0] if portal26_genai else None,
        "hardcoded": hardcoded_genai[0] if hardcoded_genai else None
    }
}

with open('agent_comparison.json', 'w') as f:
    json.dump(output, f, indent=2)

print("  Saved to: agent_comparison.json")
print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()

# Check if hardcoded has content capture
hardcoded_has_content = any(attr in hardcoded_keys for attr in CONTENT_CAPTURE_ATTRS)
portal26_has_content = any(attr in portal26_keys for attr in CONTENT_CAPTURE_ATTRS)

if hardcoded_has_content and not portal26_has_content:
    print("[KEY FINDING] Hardcoded-OTEL captures content, but portal26_otel_agent does NOT")
    print()
    print("This suggests a configuration difference between the two deployments.")
    print("Check:")
    print("  1. env_vars in deploy.py")
    print("  2. OTEL initialization in agent_deployed.py")
    print("  3. Resource attributes")
elif portal26_has_content and not hardcoded_has_content:
    print("[KEY FINDING] Portal26_otel_agent captures content, but hardcoded-OTEL does NOT")
    print()
    print("Unexpected - portal26 agent should be the one with issues.")
elif hardcoded_has_content and portal26_has_content:
    print("[KEY FINDING] BOTH agents capture content successfully")
    print()
    print("Content capture is working in both deployments!")
else:
    print("[KEY FINDING] NEITHER agent captures content")
    print()
    print("Both deployments are missing content capture attributes.")
    print("This suggests a platform-level limitation in Vertex AI Agent Engine.")

print()
