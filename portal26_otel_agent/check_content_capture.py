#!/usr/bin/env python3
import json
import re

# Read the log file
with open('hardcoded_otel_logs_20260408_022702.jsonl', 'r') as f:
    content = f.read()

# Split by record boundaries
records = re.split(r'\}\n\{', content)

found_content = False
for i, record_str in enumerate(records[:5]):  # Check first 5 records
    # Fix split boundaries
    if not record_str.startswith('{'):
        record_str = '{' + record_str
    if not record_str.endswith('}'):
        record_str = record_str + '}'

    try:
        data = json.loads(record_str)

        # Check if it's a trace with spans
        if 'resourceSpans' in data:
            for rs in data['resourceSpans']:
                for scope_span in rs.get('scopeSpans', []):
                    for span in scope_span.get('spans', []):
                        span_name = span.get('name', '')

                        # Look for GenAI related spans
                        if 'gen_ai' in span_name.lower() or 'generate' in span_name.lower():
                            print(f"\n=== Span: {span_name} ===")

                            # Check attributes for content
                            for attr in span.get('attributes', []):
                                key = attr.get('key', '')

                                # Look for prompt/content related attributes
                                if any(x in key.lower() for x in ['prompt', 'message', 'content', 'input', 'output', 'request', 'response']):
                                    value = attr.get('value', {})

                                    # Get the actual value
                                    val_str = (value.get('stringValue', '') or
                                              value.get('intValue', '') or
                                              str(value))

                                    print(f"  {key}: {val_str[:200]}")

                                    if val_str and len(val_str) > 10:
                                        found_content = True

    except Exception as e:
        pass

if not found_content:
    print("\n❌ No content capture detected - prompts/responses are empty or missing")
else:
    print("\n✅ Content capture appears to be working!")
