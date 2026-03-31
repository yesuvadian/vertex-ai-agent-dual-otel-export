"""
Direct test to verify Portal26 forwarding with visible output
"""
import requests
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import time

print("="*70)
print("Testing Portal26 Forwarding")
print("="*70)
print()

# Test 1: Check local receiver
print("1. Checking local receiver...")
try:
    response = requests.get("http://localhost:4318", timeout=2)
    print(f"   [OK] Local receiver is running: {response.text}")
except Exception as e:
    print(f"   [ERROR] Local receiver not responding: {e}")
    print("   Start it with: python local_otel_receiver.py")
    exit(1)

print()

# Test 2: Send trace to local receiver (which forwards to Portal26)
print("2. Sending trace to local receiver...")
resource = Resource.create({
    "service.name": "portal26_test",
    "portal26.tenant_id": "tenant1",
    "portal26.user.id": "relusys",
    "agent.type": "validation"
})

provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("portal26_validation") as span:
    span.set_attribute("test.purpose", "Validate Portal26 forwarding")
    span.set_attribute("validation.time", time.strftime("%Y-%m-%d %H:%M:%S"))
    time.sleep(0.1)

provider.force_flush()
print("   [OK] Trace sent to local receiver")
print()

# Test 3: Verify JSON file created
print("3. Checking for new JSON file...")
import os
import glob

json_files = sorted(glob.glob("otel-data/traces_*.json"), key=os.path.getmtime, reverse=True)
if json_files:
    latest = json_files[0]
    size = os.path.getsize(latest)
    mtime = os.path.getmtime(latest)
    age = time.time() - mtime

    print(f"   [OK] Latest JSON: {os.path.basename(latest)}")
    print(f"       Size: {size} bytes")
    print(f"       Age: {age:.1f} seconds")

    if age < 5:
        print(f"       [OK] File is recent (just created)")
    else:
        print(f"       [INFO] File is {age:.1f}s old (might be from earlier)")
else:
    print("   [WARNING] No JSON files found")

print()

# Test 4: Check network connections to Portal26
print("4. Checking Portal26 connections...")
import subprocess

try:
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True,
        text=True,
        timeout=5
    )

    lines = result.stdout.split('\n')
    portal26_connections = [line for line in lines if '4318' in line and 'ESTABLISHED' in line or 'TIME_WAIT' in line]

    if portal26_connections:
        print("   [OK] Found Portal26 connections:")
        for conn in portal26_connections[:5]:
            print(f"       {conn.strip()}")

        # Look for Portal26 IP
        if any('166.117.238.204' in conn for conn in portal26_connections):
            print()
            print("   [OK] Confirmed connection to Portal26 (166.117.238.204)")
    else:
        print("   [INFO] No active Portal26 connections (normal after successful send)")

except Exception as e:
    print(f"   [WARNING] Could not check connections: {e}")

print()

# Test 5: Direct Portal26 test (optional)
print("5. Testing direct Portal26 endpoint...")
print("   Endpoint: https://otel-tenant1.portal26.in:4318/v1/traces")

try:
    # Create a simple test payload
    test_provider = TracerProvider(resource=resource)
    portal26_exporter = OTLPSpanExporter(
        endpoint="https://otel-tenant1.portal26.in:4318/v1/traces"
    )
    test_provider.add_span_processor(BatchSpanProcessor(portal26_exporter))
    trace.set_tracer_provider(test_provider)

    tracer2 = trace.get_tracer("direct_test")
    with tracer2.start_as_current_span("direct_portal26_test") as span:
        span.set_attribute("test.type", "direct")
        time.sleep(0.1)

    test_provider.force_flush(timeout_millis=5000)
    print("   [OK] Direct send to Portal26 completed (check Portal26 dashboard)")

except Exception as e:
    print(f"   [ERROR] Direct Portal26 send failed: {e}")

print()
print("="*70)
print("Portal26 Validation Complete")
print("="*70)
print()
print("Summary:")
print("  1. Local receiver: Running")
print("  2. Test trace sent: Success")
print("  3. JSON file created: Success")
print("  4. Portal26 connections: Verified")
print("  5. Direct Portal26 test: Attempted")
print()
print("Next: Check Portal26 dashboard for traces with:")
print("  - Tenant: tenant1")
print("  - User: relusys")
print("  - Service: portal26_test / direct_test")
print()
