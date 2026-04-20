"""
Verbose Portal26 Forwarder - Shows everything happening
Perfect for manual testing to see logs being forwarded
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
SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "gcp-vertex-monitor")
BATCH_SIZE = int(os.environ.get("PORTAL26_BATCH_SIZE", "10"))
BATCH_TIMEOUT = int(os.environ.get("PORTAL26_BATCH_TIMEOUT", "5"))
OTEL_HEADERS = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
TENANT_ID = os.environ.get("PORTAL26_TENANT_ID", "")
USER_ID = os.environ.get("PORTAL26_USER_ID", "")
AGENT_TYPE = os.environ.get("AGENT_TYPE", "gcp-pubsub-monitor")

print("=" * 80)
print("VERBOSE PORTAL26 FORWARDER - Manual Testing Mode")
print("=" * 80)
print(f"GCP Project:     {PROJECT_ID}")
print(f"Subscription:    {SUBSCRIPTION_ID}")
print(f"Portal26:        {PORTAL26_ENDPOINT}")
print(f"Service Name:    {SERVICE_NAME}")
print(f"Tenant:          {TENANT_ID}")
print(f"Batch Size:      {BATCH_SIZE}")
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

    severity = log_entry.get('severity', 'INFO')
    text_payload = log_entry.get('textPayload', '')
    json_payload = log_entry.get('jsonPayload', {})
    resource = log_entry.get('resource', {})
    labels = log_entry.get('labels', {})

    otel_log = {
        "timeUnixNano": str(timestamp_ns),
        "severityText": severity,
        "severityNumber": get_severity_number(severity),
        "body": {
            "stringValue": text_payload if text_payload else json.dumps(json_payload)
        },
        "attributes": []
    }

    resource_labels = resource.get('labels', {})
    for key, value in resource_labels.items():
        otel_log["attributes"].append({
            "key": f"resource.{key}",
            "value": {"stringValue": str(value)}
        })

    for key, value in labels.items():
        otel_log["attributes"].append({
            "key": key,
            "value": {"stringValue": str(value)}
        })

    if 'trace' in log_entry:
        otel_log["traceId"] = extract_trace_id(log_entry['trace'])
    if 'spanId' in log_entry:
        otel_log["spanId"] = log_entry['spanId']

    return otel_log

def get_severity_number(severity):
    severity_map = {
        "DEBUG": 5, "INFO": 9, "NOTICE": 10, "WARNING": 13,
        "ERROR": 17, "CRITICAL": 21, "ALERT": 22, "EMERGENCY": 23
    }
    return severity_map.get(severity, 9)

def extract_trace_id(trace_str):
    if '/' in trace_str:
        return trace_str.split('/')[-1]
    return trace_str

def send_batch_to_portal26(logs):
    global total_forwarded, errors

    if not logs:
        return

    print("\n" + "=" * 80)
    print(f"SENDING BATCH TO PORTAL26 ({len(logs)} logs)")
    print("=" * 80)

    resource_attrs = [
        {"key": "service.name", "value": {"stringValue": SERVICE_NAME}},
        {"key": "source", "value": {"stringValue": "gcp-pubsub"}},
        {"key": "gcp.project", "value": {"stringValue": PROJECT_ID}}
    ]

    if TENANT_ID:
        resource_attrs.append({"key": "tenant.id", "value": {"stringValue": TENANT_ID}})
    if USER_ID:
        resource_attrs.append({"key": "user.id", "value": {"stringValue": USER_ID}})
    if AGENT_TYPE:
        resource_attrs.append({"key": "agent.type", "value": {"stringValue": AGENT_TYPE}})

    payload = {
        "resourceLogs": [{
            "resource": {"attributes": resource_attrs},
            "scopeLogs": [{
                "scope": {"name": "gcp-pubsub-monitor", "version": "1.0.0"},
                "logRecords": logs
            }]
        }]
    }

    try:
        url = f"{PORTAL26_ENDPOINT}/v1/logs"
        headers = {"Content-Type": "application/json"}

        if OTEL_HEADERS:
            for header in OTEL_HEADERS.split(','):
                if '=' in header:
                    key, value = header.split('=', 1)
                    headers[key.strip()] = value.strip()

        print(f"POST {url}")
        print(f"Payload size: {len(json.dumps(payload))} bytes")
        print(f"Headers: {list(headers.keys())}")

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        print(f"Response: {response.status_code}")
        if response.text:
            print(f"Body: {response.text[:200]}")

        if response.status_code in [200, 201, 202]:
            total_forwarded += len(logs)
            print(f"[SUCCESS] Sent {len(logs)} logs to Portal26")
            print(f"[TOTAL] {total_forwarded} logs forwarded so far")
        else:
            errors += 1
            print(f"[ERROR] Portal26 returned {response.status_code}")

    except Exception as e:
        errors += 1
        print(f"[ERROR] Failed to send: {e}")

def flush_batch():
    global batch, last_batch_time
    if batch:
        send_batch_to_portal26(batch)
        batch = []
    last_batch_time = time.time()

def callback(message):
    global total_received, batch

    total_received += 1

    try:
        log_entry = json.loads(message.data.decode('utf-8'))

        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')

        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            severity = log_entry.get('severity', 'INFO')
            timestamp = log_entry.get('timestamp', 'unknown')
            resource_labels = resource.get('labels', {})
            engine_id = resource_labels.get('reasoning_engine_id', 'unknown')

            text_payload = log_entry.get('textPayload', '')
            json_payload = log_entry.get('jsonPayload', {})

            print("\n" + "-" * 80)
            print(f"RECEIVED LOG #{total_received}")
            print("-" * 80)
            print(f"Time:      {timestamp}")
            print(f"Severity:  {severity}")
            print(f"Engine:    {engine_id}")

            if text_payload:
                print(f"Text:      {text_payload[:100]}")
            if json_payload:
                print(f"JSON keys: {list(json_payload.keys())}")

            # Convert to OTEL
            otel_log = convert_to_otel_log(log_entry)
            batch.append(otel_log)

            print(f">>> Added to batch ({len(batch)}/{BATCH_SIZE}) <<<")

            # Flush if batch full
            if len(batch) >= BATCH_SIZE:
                print("\n>>> BATCH FULL - Flushing to Portal26 >>>")
                flush_batch()

        message.ack()

    except Exception as e:
        errors += 1
        print(f"\n[ERROR] Failed to process message: {e}")
        import traceback
        traceback.print_exc()
        message.ack()

print("Starting Pub/Sub listener...")
print("Will show all Reasoning Engine logs and forward to Portal26")
print("Press Ctrl+C to stop")
print()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    while True:
        # Auto-flush on timeout
        if batch and (time.time() - last_batch_time) >= BATCH_TIMEOUT:
            print(f"\n>>> BATCH TIMEOUT ({BATCH_TIMEOUT}s) - Flushing {len(batch)} logs >>>")
            flush_batch()
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n[STOPPED] User interrupted")
finally:
    # Flush remaining logs
    if batch:
        print(f"\n>>> Flushing remaining {len(batch)} logs >>>")
        flush_batch()

    streaming_pull_future.cancel()
    streaming_pull_future.result()

print()
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Total received:           {total_received}")
print(f"Total forwarded to Portal26: {total_forwarded}")
print(f"Errors:                   {errors}")
print()

if total_forwarded > 0:
    print("[SUCCESS] Logs forwarded to Portal26!")
    print()
    print("Check Portal26 dashboard:")
    print(f'  service.name = "{SERVICE_NAME}"')
    print(f'  tenant.id = "{TENANT_ID}"')
else:
    print("[INFO] No logs forwarded")
    print()
    print("Try triggering a prompt in Google Console UI")
print()
