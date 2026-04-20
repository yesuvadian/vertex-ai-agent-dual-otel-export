"""
Multi-Destination Forwarder with Intelligent Routing
Routes logs to Portal26 OTEL, Kinesis, or S3 based on size and volume

Routing Strategy:
- Small logs (<100KB) → Portal26 OTEL (real-time analytics)
- Medium logs (100KB-1MB) → Kinesis (streaming)
- Large logs (>1MB) → S3 (archival/batch processing)
- High volume → Kinesis (handles scale better)

Configuration:
- Use .env file for easy configuration changes
- See .env.example for all options
"""
import json
import os
import time
import signal
import sys
from datetime import datetime, timezone
from google.cloud import pubsub_v1
import requests
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load configuration from .env file
load_dotenv()
logger.info("Configuration loaded from .env file")

# Handle GCP credentials from AWS Secrets Manager
if 'GOOGLE_APPLICATION_CREDENTIALS_JSON' in os.environ:
    logger.info("Loading GCP credentials from AWS Secrets Manager...")
    creds_json = os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON']
    with open('/tmp/gcp-creds.json', 'w') as f:
        f.write(creds_json)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/gcp-creds.json'
    logger.info("GCP credentials loaded successfully")

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "agentic-ai-integration-490716")
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "all-customers-logs-sub")
SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "gcp-vertex-monitor")
HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", "60"))

# Destination configuration
PORTAL26_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
OTEL_HEADERS = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
TENANT_ID = os.environ.get("PORTAL26_TENANT_ID", "")
USER_ID = os.environ.get("PORTAL26_USER_ID", "")

# AWS destinations
KINESIS_STREAM_NAME = os.environ.get("KINESIS_STREAM_NAME", "")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
S3_PREFIX = os.environ.get("S3_PREFIX", "gcp-logs/")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Routing thresholds (in bytes)
SMALL_LOG_THRESHOLD = int(os.environ.get("SMALL_LOG_THRESHOLD", "102400"))  # 100KB
LARGE_LOG_THRESHOLD = int(os.environ.get("LARGE_LOG_THRESHOLD", "1048576"))  # 1MB
HIGH_VOLUME_THRESHOLD = int(os.environ.get("HIGH_VOLUME_THRESHOLD", "100"))  # logs/min

# Batching configuration
PORTAL26_BATCH_SIZE = int(os.environ.get("PORTAL26_BATCH_SIZE", "20"))
PORTAL26_BATCH_TIMEOUT = int(os.environ.get("PORTAL26_BATCH_TIMEOUT", "5"))
KINESIS_BATCH_SIZE = int(os.environ.get("KINESIS_BATCH_SIZE", "100"))
S3_BATCH_SIZE = int(os.environ.get("S3_BATCH_SIZE", "500"))

# Initialize AWS clients
kinesis_client = None
s3_client = None

if KINESIS_STREAM_NAME:
    kinesis_client = boto3.client('kinesis', region_name=AWS_REGION)
    logger.info(f"Kinesis client initialized: {KINESIS_STREAM_NAME}")

if S3_BUCKET_NAME:
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    logger.info(f"S3 client initialized: {S3_BUCKET_NAME}")

# Global state
running = True
stats = {
    'total_received': 0,
    'portal26_sent': 0,
    'kinesis_sent': 0,
    's3_sent': 0,
    'errors': 0,
    'last_minute_count': 0,
    'last_minute_time': time.time()
}

# Batches for each destination
portal26_batch = []
kinesis_batch = []
s3_batch = []
last_flush_times = {
    'portal26': time.time(),
    'kinesis': time.time(),
    's3': time.time()
}

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_log_size(log_entry):
    """Calculate log entry size in bytes"""
    return len(json.dumps(log_entry).encode('utf-8'))

def update_volume_stats():
    """Update logs per minute statistic"""
    current_time = time.time()
    if current_time - stats['last_minute_time'] >= 60:
        # Reset minute counter
        stats['last_minute_count'] = 0
        stats['last_minute_time'] = current_time

def is_high_volume():
    """Check if currently experiencing high volume"""
    return stats['last_minute_count'] > HIGH_VOLUME_THRESHOLD

def route_log(log_entry, log_size):
    """
    Intelligently route log to appropriate destination

    Returns: ('portal26' | 'kinesis' | 's3', reason)
    """
    # Priority 1: Very large logs → S3
    if log_size > LARGE_LOG_THRESHOLD:
        return 's3', f'large_log_{log_size}_bytes'

    # Priority 2: High volume → Kinesis (if available)
    if is_high_volume() and kinesis_client:
        return 'kinesis', f'high_volume_{stats["last_minute_count"]}_per_min'

    # Priority 3: Medium logs → Kinesis (if available)
    if log_size > SMALL_LOG_THRESHOLD and kinesis_client:
        return 'kinesis', f'medium_log_{log_size}_bytes'

    # Default: Small logs → Portal26 (real-time analytics)
    if PORTAL26_ENDPOINT:
        return 'portal26', f'small_log_{log_size}_bytes'

    # Fallback: If Portal26 not configured, use Kinesis or S3
    if kinesis_client:
        return 'kinesis', 'fallback_portal26_unavailable'
    if s3_client:
        return 's3', 'fallback_portal26_kinesis_unavailable'

    return None, 'no_destination_configured'

def extract_client_info(log_entry):
    """Extract customer/client identification from log entry"""
    resource = log_entry.get('resource', {})
    resource_labels = resource.get('labels', {})
    labels = log_entry.get('labels', {})

    customer_project_id = resource_labels.get('project_id', 'unknown')
    reasoning_engine_id = resource_labels.get('reasoning_engine_id', 'unknown')
    location = resource_labels.get('location', 'unknown')

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
    """Convert GCP log entry to OTEL log format"""
    timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)

    severity = log_entry.get('severity', 'INFO')
    text_payload = log_entry.get('textPayload', '')
    json_payload = log_entry.get('jsonPayload', {})

    severity_map = {
        "DEBUG": 5, "INFO": 9, "NOTICE": 10, "WARNING": 13,
        "ERROR": 17, "CRITICAL": 21, "ALERT": 22, "EMERGENCY": 23
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

    # Add customer information
    client_info = extract_client_info(log_entry)
    otel_log["attributes"].extend([
        {"key": "customer.project_id", "value": {"stringValue": client_info['customer_project_id']}},
        {"key": "customer.id", "value": {"stringValue": client_info['customer_id']}},
        {"key": "customer.reasoning_engine_id", "value": {"stringValue": client_info['reasoning_engine_id']}},
        {"key": "customer.agent_id", "value": {"stringValue": client_info['agent_id']}},
        {"key": "customer.agent_type", "value": {"stringValue": client_info['agent_type']}},
        {"key": "customer.location", "value": {"stringValue": client_info['location']}},
        {"key": "customer.environment", "value": {"stringValue": client_info['environment']}}
    ])

    # Add resource and label attributes
    resource = log_entry.get('resource', {})
    for key, value in resource.get('labels', {}).items():
        otel_log["attributes"].append({
            "key": f"resource.{key}",
            "value": {"stringValue": str(value)}
        })

    for key, value in log_entry.get('labels', {}).items():
        otel_log["attributes"].append({
            "key": key,
            "value": {"stringValue": str(value)}
        })

    return otel_log

def send_to_portal26(logs):
    """Send batch of logs to Portal26 OTEL endpoint"""
    if not logs or not PORTAL26_ENDPOINT:
        return True

    resource_attrs = [
        {"key": "service.name", "value": {"stringValue": SERVICE_NAME}},
        {"key": "source", "value": {"stringValue": "aws-ecs-multi-dest"}},
        {"key": "destination", "value": {"stringValue": "portal26"}}
    ]

    if TENANT_ID:
        resource_attrs.append({"key": "tenant.id", "value": {"stringValue": TENANT_ID}})
    if USER_ID:
        resource_attrs.append({"key": "user.id", "value": {"stringValue": USER_ID}})

    payload = {
        "resourceLogs": [{
            "resource": {"attributes": resource_attrs},
            "scopeLogs": [{
                "scope": {"name": "multi-dest-forwarder", "version": "1.0.0"},
                "logRecords": logs
            }]
        }]
    }

    try:
        headers = {"Content-Type": "application/json"}
        if OTEL_HEADERS:
            for header in OTEL_HEADERS.split(','):
                if '=' in header:
                    key, value = header.split('=', 1)
                    headers[key.strip()] = value.strip()

        response = requests.post(f"{PORTAL26_ENDPOINT}/v1/logs", json=payload, headers=headers, timeout=10)

        if response.status_code in [200, 201, 202]:
            stats['portal26_sent'] += len(logs)
            logger.info(f"[Portal26] Sent {len(logs)} logs (total: {stats['portal26_sent']})")
            return True
        else:
            stats['errors'] += 1
            logger.error(f"[Portal26] Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        stats['errors'] += 1
        logger.error(f"[Portal26] Failed: {e}")
        return False

def send_to_kinesis(logs):
    """Send batch of logs to Kinesis stream"""
    if not logs or not kinesis_client:
        return True

    try:
        records = []
        for log in logs:
            # Add metadata
            log_with_meta = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'gcp-vertex-ai',
                'destination': 'kinesis',
                'log': log
            }

            records.append({
                'Data': json.dumps(log_with_meta),
                'PartitionKey': log.get('customer_project_id', 'unknown')
            })

        response = kinesis_client.put_records(
            StreamName=KINESIS_STREAM_NAME,
            Records=records
        )

        failed_count = response.get('FailedRecordCount', 0)
        if failed_count == 0:
            stats['kinesis_sent'] += len(logs)
            logger.info(f"[Kinesis] Sent {len(logs)} logs (total: {stats['kinesis_sent']})")
            return True
        else:
            stats['errors'] += failed_count
            logger.error(f"[Kinesis] Failed {failed_count}/{len(logs)} records")
            return False

    except ClientError as e:
        stats['errors'] += 1
        logger.error(f"[Kinesis] Failed: {e}")
        return False

def send_to_s3(logs):
    """Send batch of logs to S3"""
    if not logs or not s3_client:
        return True

    try:
        # Create batch file
        timestamp = datetime.now(timezone.utc).strftime('%Y/%m/%d/%H/%M')
        file_key = f"{S3_PREFIX}{timestamp}/logs_{int(time.time())}.json"

        # Add metadata to each log
        logs_with_meta = []
        for log in logs:
            logs_with_meta.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'gcp-vertex-ai',
                'destination': 's3',
                'log': log
            })

        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=json.dumps(logs_with_meta),
            ContentType='application/json'
        )

        stats['s3_sent'] += len(logs)
        logger.info(f"[S3] Sent {len(logs)} logs to {file_key} (total: {stats['s3_sent']})")
        return True

    except ClientError as e:
        stats['errors'] += 1
        logger.error(f"[S3] Failed: {e}")
        return False

def flush_batches(force=False):
    """Flush batches to all destinations"""
    global portal26_batch, kinesis_batch, s3_batch

    current_time = time.time()

    # Flush Portal26 batch
    if portal26_batch and (force or len(portal26_batch) >= PORTAL26_BATCH_SIZE or
                           current_time - last_flush_times['portal26'] >= PORTAL26_BATCH_TIMEOUT):
        send_to_portal26(portal26_batch)
        portal26_batch = []
        last_flush_times['portal26'] = current_time

    # Flush Kinesis batch
    if kinesis_batch and (force or len(kinesis_batch) >= KINESIS_BATCH_SIZE or
                          current_time - last_flush_times['kinesis'] >= PORTAL26_BATCH_TIMEOUT):
        send_to_kinesis(kinesis_batch)
        kinesis_batch = []
        last_flush_times['kinesis'] = current_time

    # Flush S3 batch
    if s3_batch and (force or len(s3_batch) >= S3_BATCH_SIZE or
                     current_time - last_flush_times['s3'] >= PORTAL26_BATCH_TIMEOUT):
        send_to_s3(s3_batch)
        s3_batch = []
        last_flush_times['s3'] = current_time

def health_check():
    """Log health status"""
    uptime = time.time() - start_time
    uptime_hours = uptime / 3600

    logger.info("=" * 80)
    logger.info(f"[HEALTH] Uptime: {uptime_hours:.1f}h")
    logger.info(f"  Total Received:  {stats['total_received']}")
    logger.info(f"  Portal26:        {stats['portal26_sent']}")
    logger.info(f"  Kinesis:         {stats['kinesis_sent']}")
    logger.info(f"  S3:              {stats['s3_sent']}")
    logger.info(f"  Errors:          {stats['errors']}")
    logger.info(f"  Current Volume:  {stats['last_minute_count']}/min")
    logger.info("=" * 80)

def callback(message):
    """Process incoming Pub/Sub message with intelligent routing"""
    global portal26_batch, kinesis_batch, s3_batch

    stats['total_received'] += 1
    stats['last_minute_count'] += 1
    update_volume_stats()

    try:
        # Parse log entry
        log_entry = json.loads(message.data.decode('utf-8'))

        # Filter for Reasoning Engine logs
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')

        if resource_type != "aiplatform.googleapis.com/ReasoningEngine":
            message.ack()
            return

        # Calculate log size
        log_size = get_log_size(log_entry)

        # Route to appropriate destination
        destination, reason = route_log(log_entry, log_size)

        if not destination:
            logger.warning(f"No destination for log: {reason}")
            message.ack()
            return

        # Convert to appropriate format
        if destination == 'portal26':
            otel_log = convert_to_otel_log(log_entry)
            portal26_batch.append(otel_log)
        elif destination == 'kinesis':
            client_info = extract_client_info(log_entry)
            log_entry['_routing'] = {'destination': 'kinesis', 'reason': reason}
            log_entry['_client_info'] = client_info
            kinesis_batch.append(log_entry)
        elif destination == 's3':
            client_info = extract_client_info(log_entry)
            log_entry['_routing'] = {'destination': 's3', 'reason': reason}
            log_entry['_client_info'] = client_info
            s3_batch.append(log_entry)

        # Log routing decision every 10 logs
        if stats['total_received'] % 10 == 0:
            logger.info(f"Processed {stats['total_received']} | "
                       f"P26: {len(portal26_batch)}, "
                       f"Kinesis: {len(kinesis_batch)}, "
                       f"S3: {len(s3_batch)} | "
                       f"Last: {destination} ({reason})")

        # Flush if any batch is full
        flush_batches()

        # Always ACK
        message.ack()

    except Exception as e:
        stats['errors'] += 1
        logger.error(f"Error processing message: {e}")
        message.ack()

def main():
    """Main continuous pull loop with multi-destination routing"""
    global start_time

    start_time = time.time()

    logger.info("=" * 80)
    logger.info("MULTI-DESTINATION FORWARDER - Production Mode")
    logger.info("=" * 80)
    logger.info(f"GCP Project:         {PROJECT_ID}")
    logger.info(f"Subscription:        {SUBSCRIPTION_ID}")
    logger.info(f"Portal26 OTEL:       {'Enabled' if PORTAL26_ENDPOINT else 'Disabled'}")
    logger.info(f"Kinesis Stream:      {KINESIS_STREAM_NAME if KINESIS_STREAM_NAME else 'Disabled'}")
    logger.info(f"S3 Bucket:           {S3_BUCKET_NAME if S3_BUCKET_NAME else 'Disabled'}")
    logger.info(f"Small Log Threshold: {SMALL_LOG_THRESHOLD/1024:.0f} KB")
    logger.info(f"Large Log Threshold: {LARGE_LOG_THRESHOLD/1024:.0f} KB")
    logger.info(f"High Volume:         {HIGH_VOLUME_THRESHOLD} logs/min")
    logger.info("=" * 80)
    logger.info("Routing Strategy:")
    logger.info(f"  <{SMALL_LOG_THRESHOLD/1024:.0f}KB          → Portal26 (real-time)")
    logger.info(f"  {SMALL_LOG_THRESHOLD/1024:.0f}KB-{LARGE_LOG_THRESHOLD/1024:.0f}KB      → Kinesis (streaming)")
    logger.info(f"  >{LARGE_LOG_THRESHOLD/1024:.0f}KB          → S3 (archival)")
    logger.info(f"  >{HIGH_VOLUME_THRESHOLD} logs/min → Kinesis (high volume)")
    logger.info("=" * 80)

    # Initialize Pub/Sub subscriber
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    logger.info(f"Starting continuous pull from: {subscription_path}")

    # Start streaming pull
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    last_health = time.time()

    try:
        while running:
            # Periodic flush
            flush_batches()

            # Periodic health check
            if time.time() - last_health >= HEALTH_CHECK_INTERVAL:
                health_check()
                last_health = time.time()

            time.sleep(1)

    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        logger.info("Shutting down...")

        # Flush all remaining logs
        flush_batches(force=True)

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
        logger.info(f"Total Received:  {stats['total_received']}")
        logger.info(f"Portal26:        {stats['portal26_sent']}")
        logger.info(f"Kinesis:         {stats['kinesis_sent']}")
        logger.info(f"S3:              {stats['s3_sent']}")
        logger.info(f"Errors:          {stats['errors']}")
        logger.info(f"Uptime:          {(time.time() - start_time) / 3600:.1f} hours")
        logger.info("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
