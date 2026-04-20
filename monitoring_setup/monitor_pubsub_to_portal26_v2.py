"""
Monitor GCP Pub/Sub and forward logs to Portal26 OTEL endpoint
Uses official OpenTelemetry SDK for proper protobuf support
"""
import json
import os
import time
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv

# OpenTelemetry imports
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import SeverityNumber
import logging

load_dotenv()

# GCP Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "agentic-ai-integration-490716")
TOPIC_ID = "vertex-telemetry-topic"
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "vertex-telemetry-subscription")

# Portal26 Configuration
PORTAL26_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
if not PORTAL26_ENDPOINT:
    print("[ERROR] OTEL_EXPORTER_OTLP_ENDPOINT environment variable not set")
    exit(1)

SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "gcp-vertex-monitor")
TENANT_ID = os.environ.get("PORTAL26_TENANT_ID", "")
USER_ID = os.environ.get("PORTAL26_USER_ID", "")
AGENT_TYPE = os.environ.get("AGENT_TYPE", "gcp-pubsub-monitor")

# Parse auth headers
OTEL_HEADERS = {}
headers_str = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
if headers_str:
    for header in headers_str.split(','):
        if '=' in header:
            key, value = header.split('=', 1)
            OTEL_HEADERS[key.strip()] = value.strip()

print("=" * 80)
print("GCP PUB/SUB → PORTAL26 FORWARDER (OTEL SDK)")
print("=" * 80)
print(f"GCP Project: {PROJECT_ID}")
print(f"Pub/Sub Topic: {TOPIC_ID}")
print(f"Subscription: {SUBSCRIPTION_ID}")
print(f"Portal26 Endpoint: {PORTAL26_ENDPOINT}")
print(f"Service Name: {SERVICE_NAME}")
if TENANT_ID:
    print(f"Tenant ID: {TENANT_ID}")
if USER_ID:
    print(f"User ID: {USER_ID}")
print("=" * 80)
print()

# Initialize OTEL Logger Provider
resource_attrs = {
    "service.name": SERVICE_NAME,
    "source": "gcp-pubsub",
    "gcp.project": PROJECT_ID
}

if TENANT_ID:
    resource_attrs["tenant.id"] = TENANT_ID
if USER_ID:
    resource_attrs["user.id"] = USER_ID
if AGENT_TYPE:
    resource_attrs["agent.type"] = AGENT_TYPE

resource = Resource(attributes=resource_attrs)

# Create OTEL log exporter
log_exporter = OTLPLogExporter(
    endpoint=f"{PORTAL26_ENDPOINT}/v1/logs",
    headers=OTEL_HEADERS
)

# Create logger provider
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

# Create logger
otel_logger = logger_provider.get_logger("gcp-pubsub-monitor", "1.0.0")

print("[OTEL] ✓ Portal26 log exporter initialized")
print()

# Pub/Sub setup
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

# Stats
total_received = 0
total_forwarded = 0
errors = 0

def severity_to_otel(gcp_severity):
    """Map GCP severity to OTEL SeverityNumber"""
    severity_map = {
        "DEBUG": SeverityNumber.DEBUG,
        "INFO": SeverityNumber.INFO,
        "NOTICE": SeverityNumber.INFO,
        "WARNING": SeverityNumber.WARN,
        "ERROR": SeverityNumber.ERROR,
        "CRITICAL": SeverityNumber.FATAL,
        "ALERT": SeverityNumber.FATAL,
        "EMERGENCY": SeverityNumber.FATAL
    }
    return severity_map.get(gcp_severity, SeverityNumber.INFO)

def forward_to_portal26(log_entry):
    """Forward GCP log entry to Portal26 via OTEL"""
    global total_forwarded, errors

    try:
        # Extract fields
        severity = log_entry.get('severity', 'INFO')
        text_payload = log_entry.get('textPayload', '')
        json_payload = log_entry.get('jsonPayload', {})
        resource = log_entry.get('resource', {})
        labels = log_entry.get('labels', {})
        timestamp_str = log_entry.get('timestamp', '')

        # Parse timestamp
        if timestamp_str:
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp_ns = int(dt.timestamp() * 1_000_000_000)
            except:
                timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)
        else:
            timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)

        # Build log body
        body = text_payload if text_payload else json.dumps(json_payload)

        # Build attributes
        attributes = {}

        # Add resource labels
        resource_labels = resource.get('labels', {})
        for key, value in resource_labels.items():
            attributes[f"resource.{key}"] = str(value)

        # Add log labels
        for key, value in labels.items():
            attributes[key] = str(value)

        # Add GCP-specific attributes
        if 'trace' in log_entry:
            trace_id = log_entry['trace'].split('/')[-1] if '/' in log_entry['trace'] else log_entry['trace']
            attributes['trace_id'] = trace_id

        if 'spanId' in log_entry:
            attributes['span_id'] = log_entry['spanId']

        # Emit log via OTEL
        log_record = otel_logger.emit(
            body=body,
            severity_number=severity_to_otel(severity),
            severity_text=severity,
            attributes=attributes,
            timestamp=timestamp_ns
        )

        total_forwarded += 1

    except Exception as e:
        errors += 1
        print(f"[ERROR] Failed to forward log: {e}")

def callback(message):
    global total_received

    total_received += 1

    try:
        # Parse log entry
        log_entry = json.loads(message.data.decode('utf-8'))

        # Only forward Reasoning Engine logs
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')

        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            # Forward to Portal26
            forward_to_portal26(log_entry)

            # Print progress
            severity = log_entry.get('severity', 'INFO')
            resource_labels = resource.get('labels', {})
            engine_id = resource_labels.get('reasoning_engine_id', 'unknown')

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Forwarded: {engine_id} | {severity} | Total: {total_forwarded}")

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
    # Run indefinitely
    streaming_pull_future.result()

except KeyboardInterrupt:
    print("\n\n[STOPPED] User interrupted")
finally:
    # Flush remaining logs
    logger_provider.force_flush()

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
