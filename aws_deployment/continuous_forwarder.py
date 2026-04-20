"""
Production Continuous Pull-Based Forwarder - AWS ECS Version
Enhanced for AWS deployment with Secrets Manager integration
"""
import json
import os
import time
import signal
import sys
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv
import requests
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Handle GCP credentials from AWS Secrets Manager (passed as env var)
if 'GOOGLE_APPLICATION_CREDENTIALS_JSON' in os.environ:
    logger.info("Loading GCP credentials from AWS Secrets Manager...")
    creds_json = os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON']
    with open('/tmp/gcp-creds.json', 'w') as f:
        f.write(creds_json)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/gcp-creds.json'
    logger.info("GCP credentials loaded successfully")

load_dotenv()

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "agentic-ai-integration-490716")
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "all-customers-logs-sub")
PORTAL26_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "gcp-vertex-monitor")
BATCH_SIZE = int(os.environ.get("PORTAL26_BATCH_SIZE", "20"))
BATCH_TIMEOUT = int(os.environ.get("PORTAL26_BATCH_TIMEOUT", "5"))
OTEL_HEADERS = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
TENANT_ID = os.environ.get("PORTAL26_TENANT_ID", "")
USER_ID = os.environ.get("PORTAL26_USER_ID", "")
AGENT_TYPE = os.environ.get("AGENT_TYPE", "aws-ecs-forwarder")
HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", "60"))

# Validate configuration
if not PORTAL26_ENDPOINT:
    logger.error("OTEL_EXPORTER_OTLP_ENDPOINT not set!")
    sys.exit(1)

# Global state
running = True
total_received = 0
total_forwarded = 0
total_errors = 0
batch = []
last_batch_time = time.time()
last_health_check = time.time()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_severity_number(severity):
    """Map GCP severity to OTEL severity number"""
    severity_map = {
        "DEBUG": 5, "INFO": 9, "NOTICE": 10, "WARNING": 13,
        "ERROR": 17, "CRITICAL": 21, "ALERT": 22, "EMERGENCY": 23
    }
    return severity_map.get(severity, 9)

def extract_trace_id(trace_str):
    """Extract trace ID from GCP trace string"""
    if '/' in trace_str:
        return trace_str.split('/')[-1]
    return trace_str

def extract_client_info(log_entry):
    """
    Extract customer/client identification from log entry

    Extracts:
    - Customer project ID (from resource labels)
    - Customer reasoning engine ID
    - Customer location/region
    - Custom labels (if customer tagged their engines)
    """
    resource = log_entry.get('resource', {})
    resource_labels = resource.get('labels', {})

    # Extract customer identifiers
    customer_project_id = resource_labels.get('project_id', 'unknown')
    reasoning_engine_id = resource_labels.get('reasoning_engine_id', 'unknown')
    location = resource_labels.get('location', 'unknown')

    # Check for custom client labels (if customer labeled their engines)
    labels = log_entry.get('labels', {})
    customer_id = labels.get('client_id') or labels.get('customer_id') or customer_project_id
    agent_id = labels.get('agent_id') or reasoning_engine_id
    agent_type = labels.get('agent_type', 'reasoning-engine')
    environment = labels.get('environment', 'production')

    return {
        'customer_project_id': customer_project_id,
        'customer_id': customer_id,
        'reasoning_engine_id': reasoning_engine_id,
        'agent_id': agent_id,
        'agent_type': agent_type,
        'location': location,
        'environment': environment
    }

def convert_to_otel_log(log_entry):
    """Convert GCP log entry to OTEL log format with multi-client support"""
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

    # Extract customer information
    client_info = extract_client_info(log_entry)

    # Add customer/client identification attributes (FIRST - most important for filtering)
    otel_log["attributes"].extend([
        {"key": "customer.project_id", "value": {"stringValue": client_info['customer_project_id']}},
        {"key": "customer.id", "value": {"stringValue": client_info['customer_id']}},
        {"key": "customer.reasoning_engine_id", "value": {"stringValue": client_info['reasoning_engine_id']}},
        {"key": "customer.agent_id", "value": {"stringValue": client_info['agent_id']}},
        {"key": "customer.agent_type", "value": {"stringValue": client_info['agent_type']}},
        {"key": "customer.location", "value": {"stringValue": client_info['location']}},
        {"key": "customer.environment", "value": {"stringValue": client_info['environment']}}
    ])

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

    # Add trace/span IDs
    if 'trace' in log_entry:
        otel_log["traceId"] = extract_trace_id(log_entry['trace'])
    if 'spanId' in log_entry:
        otel_log["spanId"] = log_entry['spanId']

    return otel_log

def send_batch_to_portal26(logs):
    """Send batch of logs to Portal26"""
    global total_forwarded, total_errors

    if not logs:
        return True

    # Build resource attributes
    resource_attrs = [
        {"key": "service.name", "value": {"stringValue": SERVICE_NAME}},
        {"key": "source", "value": {"stringValue": "aws-ecs"}},
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
                "scope": {"name": "aws-ecs-forwarder", "version": "1.0.0"},
                "logRecords": logs
            }]
        }]
    }

    try:
        url = f"{PORTAL26_ENDPOINT}/v1/logs"
        headers = {"Content-Type": "application/json"}

        # Add auth headers
        if OTEL_HEADERS:
            for header in OTEL_HEADERS.split(','):
                if '=' in header:
                    key, value = header.split('=', 1)
                    headers[key.strip()] = value.strip()

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code in [200, 201, 202]:
            total_forwarded += len(logs)
            logger.info(f"Sent {len(logs)} logs to Portal26 (total: {total_forwarded})")
            return True
        else:
            total_errors += 1
            logger.error(f"Portal26 returned {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        total_errors += 1
        logger.error(f"Failed to send to Portal26: {e}")
        return False

def flush_batch():
    """Flush current batch to Portal26"""
    global batch, last_batch_time

    if batch:
        logger.info(f"Flushing batch of {len(batch)} logs")
        send_batch_to_portal26(batch)
        batch = []

    last_batch_time = time.time()

def health_check():
    """Log health status"""
    global last_health_check

    uptime = time.time() - start_time
    uptime_hours = uptime / 3600

    logger.info(f"[HEALTH] Uptime: {uptime_hours:.1f}h | Received: {total_received} | "
                f"Forwarded: {total_forwarded} | Errors: {total_errors} | "
                f"Error rate: {(total_errors / max(total_received, 1) * 100):.1f}%")

    last_health_check = time.time()

def callback(message):
    """Process incoming Pub/Sub message"""
    global total_received, batch

    total_received += 1

    try:
        # Parse log entry
        log_entry = json.loads(message.data.decode('utf-8'))

        # Filter for Reasoning Engine logs
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')

        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            # Convert to OTEL format
            otel_log = convert_to_otel_log(log_entry)
            batch.append(otel_log)

            # Log progress (every 10 logs)
            if total_received % 10 == 0:
                logger.info(f"Processed {total_received} messages, batch size: {len(batch)}")

            # Flush if batch full
            if len(batch) >= BATCH_SIZE:
                flush_batch()

        # Always ACK to prevent redelivery
        message.ack()

    except Exception as e:
        total_errors += 1
        logger.error(f"Error processing message: {e}")
        # ACK to prevent infinite redelivery of bad messages
        message.ack()

def main():
    """Main continuous pull loop"""
    global start_time, last_health_check

    start_time = time.time()

    logger.info("=" * 80)
    logger.info("CONTINUOUS PULL-BASED FORWARDER - AWS ECS Production Mode")
    logger.info("=" * 80)
    logger.info(f"GCP Project:     {PROJECT_ID}")
    logger.info(f"Subscription:    {SUBSCRIPTION_ID}")
    logger.info(f"Portal26:        {PORTAL26_ENDPOINT}")
    logger.info(f"Service Name:    {SERVICE_NAME}")
    logger.info(f"Tenant:          {TENANT_ID}")
    logger.info(f"Batch Size:      {BATCH_SIZE}")
    logger.info(f"Batch Timeout:   {BATCH_TIMEOUT}s")
    logger.info(f"Agent Type:      {AGENT_TYPE}")
    logger.info("=" * 80)

    # Initialize Pub/Sub subscriber
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    logger.info(f"Starting continuous pull from: {subscription_path}")
    logger.info("Press Ctrl+C to stop gracefully")

    # Start streaming pull
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    try:
        while running:
            # Check if batch timeout exceeded
            if batch and (time.time() - last_batch_time) >= BATCH_TIMEOUT:
                flush_batch()

            # Periodic health check
            if (time.time() - last_health_check) >= HEALTH_CHECK_INTERVAL:
                health_check()

            # Sleep briefly to avoid busy loop
            time.sleep(1)

    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        logger.info("Shutting down...")

        # Flush remaining logs
        if batch:
            logger.info(f"Flushing final batch of {len(batch)} logs")
            flush_batch()

        # Stop subscriber
        streaming_pull_future.cancel()
        try:
            streaming_pull_future.result(timeout=5)
        except Exception:
            pass

        # Final stats
        logger.info("=" * 80)
        logger.info("SHUTDOWN COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total received:           {total_received}")
        logger.info(f"Total forwarded:          {total_forwarded}")
        logger.info(f"Total errors:             {total_errors}")
        logger.info(f"Uptime:                   {(time.time() - start_time) / 3600:.1f} hours")
        logger.info("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
