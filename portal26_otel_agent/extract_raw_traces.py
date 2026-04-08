"""
Extract raw GenAI span data
"""
import json
import re

LOG_FILE = "portal26_otel_agent_logs_20260407_125530.jsonl"

with open(LOG_FILE, 'r') as f:
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

# Find GenAI spans and extract full data
genai_traces = []
for trace in traces:
    try:
        rs = trace['resourceSpans'][0]
        spans = rs['scopeSpans'][0]['spans']

        for span in spans:
            span_str = json.dumps(span).lower()
            if 'gen_ai' in span_str or 'gemini' in span_str or 'generate_content' in span['name']:
                genai_traces.append(trace)
                break
    except:
        pass

# Save to file
with open('raw_trace_data.json', 'w') as f:
    json.dump(genai_traces, f, indent=2)

print(f"Extracted {len(genai_traces)} GenAI traces to raw_trace_data.json")
