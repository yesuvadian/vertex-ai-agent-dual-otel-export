"""
Verify Portal26 telemetry integration and agent configuration
"""
import os
import time
import json
import requests
from datetime import datetime

PORTAL26_ENDPOINT = "https://otel-tenant1.portal26.in:4318/v1/traces"
AUTH_HEADER = "Basic dGl0YW5pYW06aGVsbG93b3JsZA=="

def check_portal26_auth():
    """Test Portal26 endpoint authentication"""
    try:
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
        from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span
        from opentelemetry.proto.resource.v1.resource_pb2 import Resource
        from opentelemetry.proto.common.v1.common_pb2 import KeyValue, AnyValue

        resource = Resource()
        resource.attributes.append(KeyValue(
            key="service.name",
            value=AnyValue(string_value="verification_test")
        ))
        resource.attributes.append(KeyValue(
            key="portal26.tenant_id",
            value=AnyValue(string_value="tenant1")
        ))
        resource.attributes.append(KeyValue(
            key="portal26.user.id",
            value=AnyValue(string_value="relusys")
        ))

        span = Span(
            trace_id=b'\x99\x88\x77\x66' * 4,
            span_id=b'\x11\x22\x33\x44' * 2,
            name="verification_span",
            start_time_unix_nano=int(time.time() * 1e9),
            end_time_unix_nano=int((time.time() + 0.1) * 1e9)
        )

        scope_spans = ScopeSpans()
        scope_spans.spans.append(span)

        resource_spans = ResourceSpans()
        resource_spans.resource.CopyFrom(resource)
        resource_spans.scope_spans.append(scope_spans)

        export_request = ExportTraceServiceRequest()
        export_request.resource_spans.append(resource_spans)

        headers = {
            'Content-Type': 'application/x-protobuf',
            'X-Tenant-ID': 'tenant1',
            'Authorization': AUTH_HEADER,
        }

        response = requests.post(
            PORTAL26_ENDPOINT,
            data=export_request.SerializeToString(),
            headers=headers,
            timeout=10
        )

        return response.status_code == 200, response.status_code
    except Exception as e:
        return False, str(e)

def check_agent_config(agent_name, env_file):
    """Check agent .env configuration"""
    config = {
        'exists': False,
        'has_endpoint': False,
        'has_service': False,
        'has_attrs': False,
        'has_auth': False,
        'endpoint': None
    }

    if os.path.exists(env_file):
        config['exists'] = True
        with open(env_file, 'r') as f:
            for line in f:
                if 'OTEL_EXPORTER_OTLP_ENDPOINT' in line and not line.strip().startswith('#'):
                    config['has_endpoint'] = True
                    config['endpoint'] = line.split('=', 1)[1].strip() if '=' in line else None
                if 'OTEL_SERVICE_NAME' in line and not line.strip().startswith('#'):
                    config['has_service'] = True
                if 'OTEL_RESOURCE_ATTRIBUTES' in line and not line.strip().startswith('#'):
                    config['has_attrs'] = True
                if 'OTEL_EXPORTER_OTLP_HEADERS' in line and 'Authorization' in line:
                    config['has_auth'] = True

    return config

def main():
    print("=" * 70)
    print("Portal26 Telemetry Integration Verification")
    print("=" * 70)
    print()

    # Check Portal26 authentication
    print("Step 1: Portal26 Authentication")
    print("-" * 70)
    success, status = check_portal26_auth()
    if success:
        print(f"Portal26 Endpoint: {PORTAL26_ENDPOINT}")
        print(f"Response Status: {status}")
        print("[OK] Portal26 authentication working!")
    else:
        print(f"[ERROR] Portal26 test failed: {status}")
    print()

    # Check agent configurations
    print("Step 2: Agent Configuration")
    print("-" * 70)

    agents = [
        ("portal26_ngrok_agent", "C:/Yesu/ai_agent_projectgcp/portal26_ngrok_agent/.env"),
        ("portal26_otel_agent", "C:/Yesu/ai_agent_projectgcp/portal26_otel_agent/.env")
    ]

    for agent_name, env_file in agents:
        print(f"\n{agent_name}:")
        config = check_agent_config(agent_name, env_file)

        if not config['exists']:
            print(f"  [ERROR] .env file not found")
            continue

        print(f"  OTEL_EXPORTER_OTLP_ENDPOINT: {'YES' if config['has_endpoint'] else 'MISSING'}")
        if config['endpoint']:
            print(f"    -> {config['endpoint']}")
        print(f"  OTEL_SERVICE_NAME: {'YES' if config['has_service'] else 'MISSING'}")
        print(f"  OTEL_RESOURCE_ATTRIBUTES: {'YES' if config['has_attrs'] else 'MISSING'}")
        print(f"  OTEL_EXPORTER_OTLP_HEADERS (auth): {'YES' if config['has_auth'] else 'MISSING'}")

        if not config['has_auth'] and 'otel' in agent_name.lower():
            print("  [WARNING] Direct agent missing auth header!")

    print()
    print("Step 3: Test Deployed Agents")
    print("-" * 70)
    print("""
To generate telemetry from deployed agents:

1. Open Google Cloud Console:
   https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716

2. Click on "portal26_ngrok_agent" or "portal26_otel_agent"

3. Send a test query:
   "What is the weather in Bengaluru?"

4. Wait for agent response (30-60 seconds)

5. Check Portal26 Dashboard:
   - Log in to Portal26
   - Filter by:
     * Tenant ID: tenant1
     * User ID: relusys
     * Time: Last 1 hour
   - Look for traces with your query
""")

    print()
    print("Step 4: Verify in GCP Console")
    print("-" * 70)
    print("""
To verify agents are deployed with latest configuration:

1. Go to GCP Console Agent Engine page
2. Click on each agent
3. Check "Environment" section in deployment details
4. Verify these environment variables are set:
   - OTEL_EXPORTER_OTLP_ENDPOINT
   - OTEL_SERVICE_NAME
   - OTEL_RESOURCE_ATTRIBUTES
   - OTEL_EXPORTER_OTLP_HEADERS (for portal26_otel_agent)

If environment variables are missing or incorrect:
   Agents need to be redeployed!
""")

    print()
    print("=" * 70)
    print("Verification Complete")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
