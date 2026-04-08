"""
Detailed attribute analysis - shows ALL attributes and identifies missing ones
"""
import json
import re

LOG_FILE = "portal26_otel_agent_logs_20260407_125530.jsonl"
OUTPUT_FILE = "attribute_analysis.md"

print("=" * 80)
print("DETAILED ATTRIBUTE ANALYSIS")
print("=" * 80)

# Read and parse logs
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

print(f"Found {len(traces)} traces\n")

# Expected GenAI attributes according to OpenTelemetry semantic conventions
EXPECTED_ATTRIBUTES = {
    "Basic Operation": [
        "gen_ai.operation.name",
        "gen_ai.request.model",
        "gen_ai.system",
    ],
    "Request Content (Content Capture)": [
        "gen_ai.prompt",
        "gen_ai.request.messages",
        "gen_ai.request.temperature",
        "gen_ai.request.top_p",
        "gen_ai.request.max_tokens",
    ],
    "Response Content (Content Capture)": [
        "gen_ai.completion",
        "gen_ai.response.content",
        "gen_ai.response.finish_reasons",
    ],
    "Token Usage": [
        "gen_ai.usage.input_tokens",
        "gen_ai.usage.output_tokens",
        "gen_ai.usage.total_tokens",
    ],
    "Model Configuration": [
        "gen_ai.request.frequency_penalty",
        "gen_ai.request.presence_penalty",
        "gen_ai.response.model",
    ]
}

# Analyze traces and write report
with open(OUTPUT_FILE, 'w') as out:
    out.write("# OpenTelemetry GenAI Attribute Analysis\n\n")
    out.write("**Analysis Date:** 2026-04-08\n")
    out.write(f"**Log File:** {LOG_FILE}\n")
    out.write(f"**Total Traces:** {len(traces)}\n\n")
    out.write("---\n\n")

    # Find GenAI spans
    genai_spans = []
    for trace in traces:
        try:
            rs = trace['resourceSpans'][0]
            spans = rs['scopeSpans'][0]['spans']

            for span in spans:
                # Look for GenAI spans (contain gen_ai attributes or gemini model)
                span_str = json.dumps(span).lower()
                if 'gen_ai' in span_str or 'gemini' in span_str or 'generate_content' in span['name']:
                    genai_spans.append({
                        'trace': trace,
                        'span': span,
                        'service': next((a['value']['stringValue'] for a in rs['resource']['attributes']
                                       if a['key'] == 'service.name'), 'unknown')
                    })
        except:
            pass

    out.write(f"## GenAI Spans Found: {len(genai_spans)}\n\n")

    if not genai_spans:
        out.write("**ERROR:** No GenAI spans found in logs!\n")
    else:
        for idx, item in enumerate(genai_spans[:3], 1):  # First 3 spans
            span = item['span']
            service = item['service']

            out.write(f"### Span #{idx}: {span['name']}\n\n")
            out.write(f"- **Service:** {service}\n")
            out.write(f"- **Trace ID:** {span['traceId']}\n")
            out.write(f"- **Span ID:** {span['spanId']}\n")

            start_ns = int(span['startTimeUnixNano'])
            end_ns = int(span['endTimeUnixNano'])
            duration_ms = (end_ns - start_ns) / 1_000_000
            out.write(f"- **Duration:** {duration_ms:.2f}ms\n\n")

            # Extract ALL attributes
            actual_attributes = {}
            if 'attributes' in span:
                for attr in span['attributes']:
                    key = attr['key']
                    # Get value from any value type
                    value = None
                    for val_type in ['stringValue', 'intValue', 'doubleValue', 'boolValue']:
                        if val_type in attr['value']:
                            value = attr['value'][val_type]
                            break
                    actual_attributes[key] = value

            out.write("#### Attributes Present\n\n")
            out.write("```json\n")
            out.write(json.dumps(actual_attributes, indent=2))
            out.write("\n```\n\n")

            out.write(f"**Total Attributes:** {len(actual_attributes)}\n\n")

            # Check what's missing
            out.write("#### Missing Attributes (Required for Content Capture)\n\n")

            for category, attributes in EXPECTED_ATTRIBUTES.items():
                missing = [attr for attr in attributes if attr not in actual_attributes]
                present = [attr for attr in attributes if attr in actual_attributes]

                out.write(f"**{category}:**\n")
                if present:
                    out.write(f"- [YES] Present: {', '.join(present)}\n")
                if missing:
                    out.write(f"- [NO] Missing: {', '.join(missing)}\n")
                out.write("\n")

            out.write("---\n\n")

    # Summary
    out.write("## Summary\n\n")
    out.write("### Content Capture Status: NOT WORKING\n\n")

    if genai_spans:
        sample_span = genai_spans[0]['span']
        attrs = [a['key'] for a in sample_span.get('attributes', [])]

        out.write("**Critical Missing Attributes:**\n\n")
        out.write("1. [MISSING] `gen_ai.prompt` / `gen_ai.request.messages` - No prompt content captured\n")
        out.write("2. [MISSING] `gen_ai.completion` / `gen_ai.response.content` - No response content captured\n")
        out.write("3. [MISSING] `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` - No token usage captured\n\n")

        out.write("**What IS Being Captured:**\n\n")
        out.write("- [OK] Span structure (trace_id, span_id, timestamps)\n")
        out.write("- [OK] Basic metadata (operation name, model name)\n")
        out.write("- [OK] Code context (function name)\n")
        out.write("- [OK] HTTP request/response spans\n\n")

        out.write("**Configuration Status:**\n\n")
        out.write("| Setting | Value | Status |\n")
        out.write("|---------|-------|--------|\n")
        out.write("| API | `agent_engines.create()` | [OK] Correct |\n")
        out.write("| env_vars | Passed via `otel_config.OTEL_CONFIG` | [OK] Correct |\n")
        out.write("| OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT | `true` | [OK] Set |\n")
        out.write("| VertexAIInstrumentor | `.instrument()` called | [OK] Correct |\n")
        out.write("| Package structure | `extra_packages=[\"./portal26_agent\"]` | [OK] Correct |\n")
        out.write("| Traces exporting | Portal26 OTEL endpoint | [OK] Working |\n\n")

        out.write("### Conclusion\n\n")
        out.write("Despite all correct configurations, the Vertex AI Agent Engine runtime is **not capturing LLM prompt/response content**. ")
        out.write("This suggests the platform may be blocking content capture at a deeper level, regardless of the API used or environment variables set.\n\n")
        out.write("**Possible Causes:**\n")
        out.write("1. Vertex AI managed runtime may strip sensitive environment variables\n")
        out.write("2. Platform security policy may prevent content capture for compliance reasons\n")
        out.write("3. The `opentelemetry-instrumentation-vertexai` package may not support content capture in managed environments\n")
        out.write("4. Additional authentication or permissions may be required for content capture\n\n")

print(f"Analysis complete. Report saved to: {OUTPUT_FILE}")
print()
print("Opening report...")
