"""
Test gcp_traces_agent locally to verify Cloud Trace exporter works
"""
import os
import sys
import time

print("=" * 70)
print("Testing gcp_traces_agent with Cloud Trace Exporter")
print("=" * 70)
print()

# Load environment
env_file = "gcp_traces_agent/.env"
with open(env_file, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

print("Environment loaded:")
print(f"  GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
print(f"  OTEL_SERVICE_NAME: {os.environ.get('OTEL_SERVICE_NAME')}")
print()

# Change to agent directory
os.chdir("gcp_traces_agent")
sys.path.insert(0, os.getcwd())

print("Importing agent (will initialize Cloud Trace exporter)...")
print("-" * 70)

try:
    from agent import root_agent
    print("[OK] Agent imported!")
    print()
except Exception as e:
    print(f"[ERROR] Failed to import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Creating test span using OTEL...")
print("-" * 70)

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

try:
    with tracer.start_as_current_span("test_gcp_trace_span") as span:
        span.set_attribute("test.query", "What is the weather in Tokyo?")
        span.set_attribute("test.type", "local_verification")
        print("[OK] Test span created")
        time.sleep(1)

    print()
    print("Flushing spans to Cloud Trace...")
    provider = trace.get_tracer_provider()
    if hasattr(provider, 'force_flush'):
        provider.force_flush()
    time.sleep(3)

    print("[OK] Spans flushed")
    print()

except Exception as e:
    print(f"[ERROR] Span creation failed: {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
print("Test Complete")
print("=" * 70)
print()
print("Next: Check GCP Cloud Trace")
print("-" * 70)
print("1. Go to: https://console.cloud.google.com/traces?project=agentic-ai-integration-490716")
print("2. Filter by service: gcp_traces_agent")
print("3. Time: Last 10 minutes")
print("4. Look for span: test_gcp_trace_span")
print()
print("If span appears -> Cloud Trace exporter working!")
print()
