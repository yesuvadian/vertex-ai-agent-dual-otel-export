"""
Simple local OTEL receiver that:
1. Receives OTLP/HTTP traces on port 4318
2. Logs to console and file
3. Forwards to Portal26 endpoint
"""
import http.server
import socketserver
import json
import os
from datetime import datetime
import requests

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

            # Log to console
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'='*80}")
            print(f"[{timestamp}] Received OTEL traces from {self.client_address[0]}")
            print(f"Content-Length: {content_length} bytes")
            print(f"Content-Type: {self.headers.get('Content-Type')}")

            # Try to parse and display JSON if possible
            try:
                if self.headers.get('Content-Type') == 'application/json':
                    data = json.loads(body.decode('utf-8'))
                    print(f"Traces: {json.dumps(data, indent=2)[:500]}...")
            except:
                print(f"Body: {body[:200]}...")

            # Log to file
            log_file = os.path.join(LOG_DIR, f"traces_{datetime.now().strftime('%Y%m%d')}.log")
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"[{timestamp}] From: {self.client_address[0]}\n")
                f.write(f"Headers: {dict(self.headers)}\n")
                f.write(f"Body: {body.decode('utf-8', errors='ignore')}\n")

            # Forward to Portal26
            try:
                headers = {
                    'Content-Type': self.headers.get('Content-Type', 'application/json'),
                    'X-Tenant-ID': 'tenant1'
                }
                response = requests.post(
                    PORTAL26_ENDPOINT,
                    data=body,
                    headers=headers,
                    timeout=10
                )
                print(f"Forwarded to Portal26: {response.status_code}")
            except Exception as e:
                print(f"Failed to forward to Portal26: {e}")

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "success"}')

            print(f"[OK] Trace received and logged")
            print(f"{'='*80}\n")
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle health check"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP server logs"""
        pass

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"Local OTEL Receiver Starting...")
    print(f"{'='*80}")
    print(f"Port: {PORT}")
    print(f"Endpoint: http://localhost:{PORT}/v1/traces")
    print(f"Forwarding to: {PORTAL26_ENDPOINT}")
    print(f"Logs directory: {LOG_DIR}/")
    print(f"{'='*80}\n")
    print(f"Waiting for OTEL traces...")
    print(f"Press Ctrl+C to stop\n")

    with socketserver.TCPServer(("", PORT), OTELHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nStopping OTEL receiver...")
            httpd.shutdown()
