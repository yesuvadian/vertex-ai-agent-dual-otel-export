"""
Cloud Function - Push-Based Forwarder
Automatically triggered by Pub/Sub when messages arrive
No server needed - fully serverless!
"""
import json
import os
import base64
import requests
from datetime import datetime, timezone

# Configuration from environment variables
PORTAL26_ENDPOINT = os.environ.get("PORTAL26_ENDPOINT")
PORTAL26_AUTH = os.environ.get("PORTAL26_AUTH")
TENANT_ID = os.environ.get("TENANT_ID", "tenant1")
USER_ID = os.environ.get("USER_ID", "relusys_terraform")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "gcp-vertex-monitor")

def pubsub_to_portal26(event, context):
    """
    Cloud Function entry point - triggered by Pub/Sub

    Args:
        event (dict): Pub/Sub event containing message data
        context (google.cloud.functions.Context): Event metadata
    """
    try:
        # Decode Pub/Sub message
        if 'data' not in event:
            print("No data in event")
            return

        message_data = base64.b64decode(event['data']).decode('utf-8')

        # Parse GCP log entry
        log_entry = json.loads(message_data)

        # Filter for Reasoning Engine logs only
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', '')

        if resource_type != 'aiplatform.googleapis.com/ReasoningEngine':
            print(f"Skipping non-Reasoning Engine log: {resource_type}")
            return

        # Get engine ID for logging
        resource_labels = resource.get('labels', {})
        engine_id = resource_labels.get('reasoning_engine_id', 'unknown')
        severity = log_entry.get('severity', 'INFO')

        print(f"Processing log from engine {engine_id}, severity: {severity}")

        # Convert to OTEL format
        otel_log = convert_to_otel(log_entry)

        # Send to Portal26
        success = send_to_portal26([otel_log])

        if success:
            print(f"Successfully forwarded log to Portal26")
        else:
            print(f"Failed to forward log to Portal26")

    except Exception as e:
        print(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()

def convert_to_otel(log_entry):
    """Convert GCP log entry to OTEL log format"""
    timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)

    severity = log_entry.get('severity', 'INFO')
    text_payload = log_entry.get('textPayload', '')
    json_payload = log_entry.get('jsonPayload', {})
    resource = log_entry.get('resource', {})
    labels = log_entry.get('labels', {})

    # Severity number mapping (GCP -> OTEL)
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

    otel_log = {
        "timeUnixNano": str(timestamp_ns),
        "severityText": severity,
        "severityNumber": severity_map.get(severity, 9),
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

    # Add trace and span IDs if present
    if 'trace' in log_entry:
        trace_id = log_entry['trace'].split('/')[-1] if '/' in log_entry['trace'] else log_entry['trace']
        otel_log["traceId"] = trace_id

    if 'spanId' in log_entry:
        otel_log["spanId"] = log_entry['spanId']

    return otel_log

def send_to_portal26(logs):
    """Send logs to Portal26 OTEL endpoint"""
    if not PORTAL26_ENDPOINT:
        print("ERROR: PORTAL26_ENDPOINT not configured")
        return False

    # Build OTEL payload
    payload = {
        "resourceLogs": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": SERVICE_NAME}},
                    {"key": "source", "value": {"stringValue": "cloud-function"}},
                    {"key": "tenant.id", "value": {"stringValue": TENANT_ID}},
                    {"key": "user.id", "value": {"stringValue": USER_ID}}
                ]
            },
            "scopeLogs": [{
                "scope": {
                    "name": "cloud-function-forwarder",
                    "version": "1.0.0"
                },
                "logRecords": logs
            }]
        }]
    }

    try:
        headers = {
            "Content-Type": "application/json"
        }

        if PORTAL26_AUTH:
            headers["Authorization"] = PORTAL26_AUTH

        response = requests.post(
            f"{PORTAL26_ENDPOINT}/v1/logs",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code in [200, 201, 202]:
            print(f"Portal26 accepted log (status: {response.status_code})")
            return True
        else:
            print(f"Portal26 returned error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"Failed to send to Portal26: {e}")
        return False
