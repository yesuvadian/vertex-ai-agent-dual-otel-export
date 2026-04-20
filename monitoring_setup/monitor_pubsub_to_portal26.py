"""
Monitor GCP Pub/Sub and forward logs to Portal26 OTEL endpoint
Pulls messages from vertex-telemetry-topic and sends to Portal26 for observability
"""
import json
import os
import time
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv
import requests

load_dotenv()

# GCP Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "agentic-ai-integration-490716")
TOPIC_ID = "vertex-telemetry-topic"
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "vertex-telemetry-subscription")

# Portal26 Configuration
PORTAL26_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
if not PORTAL26_ENDPOINT:
    print("[ERROR] OTEL_EXPORTER_OTLP_ENDPOINT environment variable not set")
    print("Example: export OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318")
    exit(1)

SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "gcp-pubsub-monitor")
BATCH_SIZE = int(os.environ.get("PORTAL26_BATCH_SIZE", "10"))
BATCH_TIMEOUT = int(os.environ.get("PORTAL26_BATCH_TIMEOUT", "5"))

# Authentication
OTEL_HEADERS = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
PROTOCOL = os.environ.get("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")

# Multi-tenant attributes
TENANT_ID = os.environ.get("PORTAL26_TENANT_ID", "")
USER_ID = os.environ.get("PORTAL26_USER_ID", "")
AGENT_TYPE = os.environ.get("AGENT_TYPE", "gcp-pubsub-monitor")

print("=" * 80)
print("GCP PUB/SUB TO PORTAL26 FORWARDER")
print("=" * 80)
print(f"GCP Project: {PROJECT_ID}")
print(f"Pub/Sub Topic: {TOPIC_ID}")
print(f"Subscription: {SUBSCRIPTION_ID}")
print(f"Portal26 Endpoint: {PORTAL26_ENDPOINT}")
print(f"Service Name: {SERVICE_NAME}")
print(f"Protocol: {PROTOCOL}")
print(f"Batch Size: {BATCH_SIZE}")
if TENANT_ID:
    print(f"Tenant ID: {TENANT_ID}")
if USER_ID:
    print(f"User ID: {USER_ID}")
print("=" * 80)
print()

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

# Stats
total_received = 0
total_forwarded = 0
errors = 0
batch = []
last_batch_time = time.time()

def convert_to_otel_log(log_entry):
    """Convert GCP log entry to OTEL log format"""
    timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)

    # Extract key fields
    severity = log_entry.get('severity', 'INFO')
    text_payload = log_entry.get('textPayload', '')
    json_payload = log_entry.get('jsonPayload', {})
    resource = log_entry.get('resource', {})
    labels = log_entry.get('labels', {})

    # Build OTEL log record
    otel_log = {
        "timeUnixNano": str(timestamp_ns),
        "severityText": severity,
        "severityNumber": get_severity_number(severity),
        "body": {
            "stringValue": text_payload if text_payload else json.dumps(json_payload)
        },
        "attributes": []
    }

    # Add resource attributes
    resource_labels = resource.get('labels', {})
    for key, value in resource_labels.items():
        otel_log["attributes"].append({
            "key": f"resource.{key}",
            "value": {"stringValue": str(value)}
        })

    # Add log labels
    for key, value in labels.items():
        otel_log["attributes"].append({
            "key": key,
            "value": {"stringValue": str(value)}
        })

    # Add GCP-specific attributes
    if 'trace' in log_entry:
        otel_log["traceId"] = extract_trace_id(log_entry['trace'])
    if 'spanId' in log_entry:
        otel_log["spanId"] = log_entry['spanId']

    return otel_log

def get_severity_number(severity):
    """Map GCP severity to OTEL severity number"""
    severity_map = {
        "DEBUG": 5,
        "INFO": 9,
        "NOTICE": 10,
        "WARNING": 13,
        "ERROR": 17,
        "CRITICAL": 21,
        "ALERT": 22,
        "EMERGENCY": 23
    }
    return severity_map.get(severity, 9)

def extract_trace_id(trace_str):
    """Extract trace ID from GCP trace string"""
    # Format: projects/PROJECT/traces/TRACE_ID
    if '/' in trace_str:
        return trace_str.split('/')[-1]
    return trace_str

def send_batch_to_portal26(logs):
    """Send batch of logs to Portal26 OTEL endpoint"""
    global total_forwarded, errors

    if not logs:
        return

    # Build resource attributes
    resource_attrs = [
        {"key": "service.name", "value": {"stringValue": SERVICE_NAME}},
        {"key": "source", "value": {"stringValue": "gcp-pubsub"}},
        {"key": "gcp.project", "value": {"stringValue": PROJECT_ID}}
    ]

    # Add multi-tenant attributes
    if TENANT_ID:
        resource_attrs.append({"key": "tenant.id", "value": {"stringValue": TENANT_ID}})
    if USER_ID:
        resource_attrs.append({"key": "user.id", "value": {"stringValue": USER_ID}})
    if AGENT_TYPE:
        resource_attrs.append({"key": "agent.type", "value": {"stringValue": AGENT_TYPE}})

    # Build OTEL logs payload
    payload = {
        "resourceLogs": [{
            "resource": {
                "attributes": resource_attrs
            },
            "scopeLogs": [{
                "scope": {
                    "name": "gcp-pubsub-monitor",
                    "version": "1.0.0"
                },
                "logRecords": logs
            }]
        }]
    }

    try:
        # Send to Portal26
        url = f"{PORTAL26_ENDPOINT}/v1/logs"

        # Build headers with authentication
        headers = {}

        if PROTOCOL == "http/protobuf":
            headers["Content-Type"] = "application/x-protobuf"
        else:
            headers["Content-Type"] = "application/json"

        # Add auth headers
        if OTEL_HEADERS:
            # Parse headers like "Authorization=Basic xxx,Another=value"
            for header in OTEL_HEADERS.split(','):
                if '=' in header:
                    key, value = header.split('=', 1)
                    headers[key.strip()] = value.strip()

        # For protobuf, we need to convert to protobuf format
        # For now, using JSON (add protobuf support if needed)
        if PROTOCOL == "http/protobuf":
            print("[WARN] Protobuf protocol specified but using JSON fallback")
            print("[WARN] Install opentelemetry-exporter-otlp-proto-http for protobuf support")
            headers["Content-Type"] = "application/json"

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code in [200, 201, 202]:
            total_forwarded += len(logs)
            print(f"[PORTAL26] OK Sent {len(logs)} logs (total: {total_forwarded})")
        else:
            errors += 1
            print(f"[ERROR] Portal26 returned {response.status_code}: {response.text[:200]}")

    except Exception as e:
        errors += 1
        print(f"[ERROR] Failed to send to Portal26: {e}")

def flush_batch():
    """Flush current batch to Portal26"""
    global batch, last_batch_time

    if batch:
        send_batch_to_portal26(batch)
        batch = []

    last_batch_time = time.time()

def callback(message):
    global total_received, batch

    total_received += 1

    try:
        # Parse log entry
        log_entry = json.loads(message.data.decode('utf-8'))

        # Only forward Reasoning Engine logs
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')

        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            # Convert to OTEL format
            otel_log = convert_to_otel_log(log_entry)
            batch.append(otel_log)

            # Print progress
            severity = log_entry.get('severity', 'INFO')
            resource_labels = resource.get('labels', {})
            engine_id = resource_labels.get('reasoning_engine_id', 'unknown')

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Queued: {engine_id} | {severity} | Batch: {len(batch)}/{BATCH_SIZE}")

            # Flush if batch is full
            if len(batch) >= BATCH_SIZE:
                flush_batch()

        message.ack()

        # Periodic stats
        if total_received % 50 == 0:
            print(f"\n--- Stats: {total_received} received | {total_forwarded} forwarded | {errors} errors ---\n")

    except Exception as e:
        errors += 1
        print(f"[ERROR] Failed to process message: {e}")
        message.ack()

print("Starting Pub/Sub listener...")
print("Will forward Reasoning Engine logs to Portal26")
print()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    # Run indefinitely with periodic batch flushing
    while True:
        # Flush batch if timeout exceeded
        if batch and (time.time() - last_batch_time) >= BATCH_TIMEOUT:
            flush_batch()

        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n[STOPPED] User interrupted")
finally:
    # Flush remaining logs
    flush_batch()

    streaming_pull_future.cancel()
    streaming_pull_future.result()

print()
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Total received: {total_received}")
print(f"Total forwarded to Portal26: {total_forwarded}")
print(f"Errors: {errors}")
print()
