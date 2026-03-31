"""
Enhanced local OTEL receiver that:
1. Receives OTLP/HTTP traces on port 4318
2. Decodes protobuf and saves as JSON files
3. Logs to console
4. Forwards to Portal26 endpoint
"""
import http.server
import socketserver
import json
import os
from datetime import datetime
import requests

# Import OTLP protobuf definitions
try:
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
    from google.protobuf.json_format import MessageToDict
    PROTOBUF_AVAILABLE = True
except ImportError:
    print("[WARNING] Protobuf libraries not available. Install with:")
    print("  pip install opentelemetry-proto")
    PROTOBUF_AVAILABLE = False

PORT = 4318
PORTAL26_ENDPOINT = "https://otel-tenant1.portal26.in:4318/v1/traces"
LOG_DIR = "otel-data"

os.makedirs(LOG_DIR, exist_ok=True)

class OTELHandler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        """Handle incoming OTLP/HTTP POST requests"""
        if self.path == "/v1/traces":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")

            print(f"\n{'='*80}")
            print(f"[{timestamp}] Received OTEL traces")
            print(f"From: {self.client_address[0]}")
            print(f"Content-Length: {content_length} bytes")
            print(f"Content-Type: {self.headers.get('Content-Type')}")

            trace_data = None

            # Try to decode protobuf
            if self.headers.get('Content-Type') == 'application/x-protobuf' and PROTOBUF_AVAILABLE:
                try:
                    # Decode protobuf
                    request = ExportTraceServiceRequest()
                    request.ParseFromString(body)

                    # Convert to dict/JSON
                    trace_data = MessageToDict(request, preserving_proto_field_name=True)

                    # Extract useful info
                    span_count = 0
                    service_name = "unknown"
                    tenant_id = "unknown"

                    if 'resource_spans' in trace_data:
                        for rs in trace_data['resource_spans']:
                            # Get service name and tenant_id from resource attributes
                            if 'resource' in rs and 'attributes' in rs['resource']:
                                for attr in rs['resource']['attributes']:
                                    if attr.get('key') == 'service.name':
                                        service_name = attr.get('value', {}).get('string_value', 'unknown')
                                    elif attr.get('key') == 'portal26.tenant_id':
                                        tenant_id = attr.get('value', {}).get('string_value', 'unknown')

                            # Count spans
                            if 'scope_spans' in rs:
                                for ss in rs['scope_spans']:
                                    span_count += len(ss.get('spans', []))

                    print(f"Service: {service_name}")
                    print(f"Tenant: {tenant_id}")
                    print(f"Spans: {span_count}")

                    # Save as JSON file
                    json_file = os.path.join(LOG_DIR, f"traces_{timestamp_file}.json")
                    with open(json_file, 'w') as f:
                        json.dump(trace_data, f, indent=2)

                    print(f"[OK] Saved JSON: {json_file}")

                except Exception as e:
                    print(f"[ERROR] Failed to decode protobuf: {e}")
                    trace_data = None

            elif self.headers.get('Content-Type') == 'application/json':
                # Already JSON
                try:
                    trace_data = json.loads(body.decode('utf-8'))
                    json_file = os.path.join(LOG_DIR, f"traces_{timestamp_file}.json")
                    with open(json_file, 'w') as f:
                        json.dump(trace_data, f, indent=2)
                    print(f"[OK] Saved JSON: {json_file}")
                except Exception as e:
                    print(f"[ERROR] Failed to parse JSON: {e}")

            # Also save raw log for debugging
            log_file = os.path.join(LOG_DIR, f"traces_{datetime.now().strftime('%Y%m%d')}.log")
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"[{timestamp}] From: {self.client_address[0]}\n")
                f.write(f"Headers: {dict(self.headers)}\n")
                if trace_data:
                    f.write(f"JSON saved to: traces_{timestamp_file}.json\n")

            # Forward to Portal26
            try:
                headers = {
                    'Content-Type': self.headers.get('Content-Type', 'application/x-protobuf'),
                    'X-Tenant-ID': 'tenant1',
                    'Authorization': 'Basic dGl0YW5pYW06aGVsbG93b3JsZA=='  # Portal26 auth
                }
                response = requests.post(
                    PORTAL26_ENDPOINT,
                    data=body,
                    headers=headers,
                    timeout=10
                )
                print(f"[OK] Forwarded to Portal26: {response.status_code}")
                if response.status_code != 200:
                    print(f"[WARNING] Portal26 response: {response.text}")
            except Exception as e:
                print(f"[ERROR] Failed to forward to Portal26: {e}")

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "success"}')

            print(f"{'='*80}\n")
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle health check"""
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK - Local OTEL Receiver Running')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP server logs"""
        pass

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"Enhanced Local OTEL Receiver Starting...")
    print(f"{'='*80}")
    print(f"Port: {PORT}")
    print(f"Endpoint: http://localhost:{PORT}/v1/traces")
    print(f"Forwarding to: {PORTAL26_ENDPOINT}")
    print(f"Logs directory: {LOG_DIR}/")

    if PROTOBUF_AVAILABLE:
        print(f"[OK] Protobuf decoder available - JSON files will be generated")
    else:
        print(f"[WARNING] Protobuf decoder not available - only .log files will be generated")
        print(f"           Install with: pip install opentelemetry-proto")

    print(f"{'='*80}\n")
    print(f"Waiting for OTEL traces...")
    print(f"Press Ctrl+C to stop\n")

    with socketserver.TCPServer(("", PORT), OTELHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nStopping OTEL receiver...")
            httpd.shutdown()
