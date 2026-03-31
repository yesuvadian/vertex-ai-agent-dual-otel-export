"""
Direct test to check Portal26 endpoint response
"""
import requests
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span
from opentelemetry.proto.resource.v1.resource_pb2 import Resource
from opentelemetry.proto.common.v1.common_pb2 import KeyValue, AnyValue
import time

print("="*70)
print("Testing Portal26 Endpoint Direct Response")
print("="*70)
print()

# Portal26 endpoint
PORTAL26_ENDPOINT = "https://otel-tenant1.portal26.in:4318/v1/traces"

print(f"Endpoint: {PORTAL26_ENDPOINT}")
print()

# Create a minimal valid OTLP protobuf payload
print("1. Creating OTLP protobuf payload...")

# Create resource with attributes
resource = Resource()
resource.attributes.append(KeyValue(
    key="service.name",
    value=AnyValue(string_value="portal26_direct_test")
))
resource.attributes.append(KeyValue(
    key="portal26.tenant_id",
    value=AnyValue(string_value="tenant1")
))
resource.attributes.append(KeyValue(
    key="portal26.user.id",
    value=AnyValue(string_value="relusys")
))

# Create a span
span = Span(
    trace_id=b'\x12\x34\x56\x78' * 4,  # 16 bytes
    span_id=b'\xAB\xCD\xEF\x01' * 2,   # 8 bytes
    name="direct_test_span",
    start_time_unix_nano=int(time.time() * 1e9),
    end_time_unix_nano=int((time.time() + 0.1) * 1e9)
)

# Create scope spans
scope_spans = ScopeSpans()
scope_spans.spans.append(span)

# Create resource spans
resource_spans = ResourceSpans()
resource_spans.resource.CopyFrom(resource)
resource_spans.scope_spans.append(scope_spans)

# Create export request
export_request = ExportTraceServiceRequest()
export_request.resource_spans.append(resource_spans)

# Serialize to protobuf
protobuf_data = export_request.SerializeToString()

print(f"   Payload size: {len(protobuf_data)} bytes")
print(f"   Resource attributes: service.name, portal26.tenant_id, portal26.user.id")
print(f"   Spans: 1")
print()

# Send to Portal26
print("2. Sending to Portal26...")
print(f"   POST {PORTAL26_ENDPOINT}")
print()

try:
    headers = {
        'Content-Type': 'application/x-protobuf',
        'X-Tenant-ID': 'tenant1',
        'Authorization': 'Basic dGl0YW5pYW06aGVsbG93b3JsZA==',  # Portal26 auth
        'User-Agent': 'OTel-Test/1.0'
    }

    response = requests.post(
        PORTAL26_ENDPOINT,
        data=protobuf_data,
        headers=headers,
        timeout=10
    )

    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text[:500]}")
    print()

    if response.status_code == 200:
        print("[SUCCESS] Portal26 accepted the trace data!")
    elif response.status_code == 401:
        print("[ERROR] Authentication required - check credentials")
    elif response.status_code == 403:
        print("[ERROR] Forbidden - check tenant_id and permissions")
    elif response.status_code == 400:
        print("[ERROR] Bad request - Portal26 rejected the payload")
        print(f"        Response: {response.text}")
    elif response.status_code >= 500:
        print("[ERROR] Portal26 server error")
        print(f"        Response: {response.text}")
    else:
        print(f"[WARNING] Unexpected status code: {response.status_code}")
        print(f"          Response: {response.text}")

except requests.exceptions.ConnectionError as e:
    print(f"[ERROR] Connection failed: {e}")
    print("        - Check if Portal26 endpoint is correct")
    print("        - Check network connectivity")
    print("        - Check firewall settings")

except requests.exceptions.Timeout:
    print("[ERROR] Request timed out")
    print("        - Portal26 might be slow to respond")
    print("        - Check network latency")

except requests.exceptions.SSLError as e:
    print(f"[ERROR] SSL/TLS error: {e}")
    print("        - Check if endpoint requires specific SSL config")

except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
print("Test Complete")
print("="*70)
