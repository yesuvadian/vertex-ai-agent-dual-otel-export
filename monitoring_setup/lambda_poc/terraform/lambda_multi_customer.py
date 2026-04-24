"""
AWS Lambda - Multi-Customer Log Processor with Shared Secret Authentication
Handles logs from multiple GCP customers with shared secret verification
"""
import json
import base64
import boto3
import os
from datetime import datetime
from typing import Dict, List, Any

# AWS Clients
secrets_manager = boto3.client('secretsmanager')
s3_client = boto3.client('s3')
kinesis_client = boto3.client('kinesis')

# Configuration
SHARED_SECRET_ARN = os.environ.get('SHARED_SECRET_ARN')
PORTAL26_ENDPOINTS = json.loads(os.environ.get('PORTAL26_ENDPOINTS', '{}'))
SIZE_THRESHOLD_KB = 100  # Route to S3 if larger than 100 KB


def lambda_handler(event, context):
    """
    Main Lambda handler for processing GCP Pub/Sub messages
    """
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] === Multi-Customer Log Processor ===")

    try:
        # 1. Extract message from Pub/Sub
        message = event.get('message', {})
        encoded_data = message.get('data', '')
        attributes = message.get('attributes', {})

        print(f"[INFO] Received message ID: {message.get('messageId')}")

        # 2. Verify shared secret
        shared_secret_from_message = attributes.get('shared_secret')
        if not verify_shared_secret(shared_secret_from_message):
            print(f"[ERROR] Shared secret verification failed")
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Forbidden',
                    'message': 'Invalid shared secret'
                })
            }

        print(f"[OK] Shared secret verified")

        # 3. Decode and parse log data
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        log_entry = json.loads(decoded_data)

        # 4. Identify customer
        customer_id = identify_customer(log_entry, attributes)
        print(f"[INFO] Customer identified: {customer_id}")

        # 5. Build consolidated structure
        consolidated_data = build_consolidated_structure(log_entry, customer_id)

        # 6. Route to appropriate destination
        route_to_destinations(consolidated_data, customer_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'customer_id': customer_id,
                'logs_count': len(consolidated_data.get('logs', [])),
                'traces_count': len(consolidated_data.get('traces', [])),
                'timestamp': timestamp
            })
        }

    except Exception as e:
        print(f"[ERROR] Processing failed: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e)
            })
        }


def verify_shared_secret(provided_secret: str) -> bool:
    """
    Verify shared secret from message against AWS Secrets Manager
    """
    if not provided_secret:
        print(f"[ERROR] No shared secret provided in message")
        return False

    try:
        # Retrieve secret from AWS Secrets Manager
        response = secrets_manager.get_secret_value(SecretId=SHARED_SECRET_ARN)
        secret_data = json.loads(response['SecretString'])
        expected_secret = secret_data.get('secret_key')

        # Compare secrets (constant-time comparison to prevent timing attacks)
        return secrets_compare(provided_secret, expected_secret)

    except Exception as e:
        print(f"[ERROR] Failed to verify shared secret: {str(e)}")
        return False


def secrets_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks
    """
    if not a or not b:
        return False

    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)

    return result == 0


def identify_customer(log_entry: Dict, attributes: Dict) -> str:
    """
    Identify customer from log entry metadata
    """
    # Method 1: From message attributes
    if 'customer_id' in attributes:
        return attributes['customer_id']

    # Method 2: From GCP project ID
    resource = log_entry.get('resource', {})
    labels = resource.get('labels', {})
    project_id = labels.get('project_id', '')

    # Map project IDs to customer IDs
    project_to_customer = {
        'agentic-ai-integration-490716': 'customer1',
        'another-project-id': 'customer2',
    }

    customer_id = project_to_customer.get(project_id, 'default')

    # Method 3: From reasoning engine ID
    engine_id = labels.get('reasoning_engine_id', '')
    if engine_id:
        # You can map engine IDs to customers if needed
        pass

    return customer_id


def build_consolidated_structure(log_entry: Dict, customer_id: str) -> Dict:
    """
    Build consolidated JSON structure with logs, traces, and metrics
    """
    resource = log_entry.get('resource', {})
    labels = resource.get('labels', {})
    payload = log_entry.get('jsonPayload', {})

    consolidated = {
        "version": "1.0",
        "timestamp": log_entry.get('timestamp'),
        "customer_id": customer_id,
        "source": {
            "provider": "gcp",
            "service": "vertex-ai-reasoning-engine",
            "reasoning_engine_id": labels.get('reasoning_engine_id'),
            "project_id": labels.get('project_id'),
            "location": labels.get('location')
        },
        "logs": [],
        "traces": [],
        "metrics": []
    }

    # Add log entry
    log_data = {
        "log_id": log_entry.get('insertId'),
        "timestamp": log_entry.get('timestamp'),
        "severity": log_entry.get('severity'),
        "message": payload.get('message', ''),
        "attributes": {k: v for k, v in payload.items() if k != 'message'}
    }
    consolidated['logs'].append(log_data)

    # Extract trace data
    trace_data = extract_trace_from_log(log_entry)
    if trace_data:
        consolidated['traces'].append(trace_data)

    # Extract metrics
    metrics = extract_metrics_from_log(log_entry)
    consolidated['metrics'].extend(metrics)

    return consolidated


def extract_trace_from_log(log_entry: Dict) -> Dict:
    """
    Extract trace information from log entry
    """
    payload = log_entry.get('jsonPayload', {})
    resource = log_entry.get('resource', {})
    labels = resource.get('labels', {})

    trace_id = payload.get('request_id', log_entry.get('insertId'))
    message = payload.get('message', '')

    trace = {
        "trace_id": trace_id,
        "trace_name": get_trace_name(message),
        "start_time": log_entry.get('timestamp'),
        "end_time": log_entry.get('timestamp'),
        "duration_ms": payload.get('duration_ms', 0),
        "status": "error" if log_entry.get('severity') == 'ERROR' else "success",
        "service": {
            "name": "vertex-ai-reasoning-engine",
            "instance_id": labels.get('reasoning_engine_id')
        },
        "tags": {
            "user_id": payload.get('user_id'),
            "query": extract_query(message)
        },
        "events": [
            {
                "event_id": log_entry.get('insertId'),
                "timestamp": log_entry.get('timestamp'),
                "name": get_event_name(message),
                "attributes": {k: v for k, v in payload.items() if k != 'message'}
            }
        ],
        "spans": [
            {
                "span_id": log_entry.get('insertId'),
                "parent_span_id": payload.get('parent_request_id'),
                "name": get_span_name(message),
                "start_time": log_entry.get('timestamp'),
                "end_time": log_entry.get('timestamp'),
                "duration_ms": payload.get('duration_ms', 0),
                "status": "error" if log_entry.get('severity') == 'ERROR' else "success",
                "attributes": extract_span_attributes(payload)
            }
        ]
    }

    return trace


def extract_metrics_from_log(log_entry: Dict) -> List[Dict]:
    """
    Extract metrics from log entry
    """
    payload = log_entry.get('jsonPayload', {})
    resource = log_entry.get('resource', {})
    labels = resource.get('labels', {})

    metrics = []

    # Duration metric
    if 'duration_ms' in payload:
        metrics.append({
            "name": "agent.request.duration",
            "value": payload['duration_ms'],
            "type": "histogram",
            "unit": "milliseconds",
            "timestamp": log_entry.get('timestamp'),
            "tags": {
                "reasoning_engine_id": labels.get('reasoning_engine_id'),
                "status": "error" if log_entry.get('severity') == 'ERROR' else "success"
            }
        })

    # Tool execution count
    if 'tool_name' in payload:
        metrics.append({
            "name": "agent.tool.execution_count",
            "value": 1,
            "type": "counter",
            "unit": "count",
            "timestamp": log_entry.get('timestamp'),
            "tags": {
                "tool_name": payload['tool_name']
            }
        })

    return metrics


def get_trace_name(message: str) -> str:
    """Determine trace name from message"""
    if '[AGENT]' in message:
        return 'agent.query.execution'
    elif '[TOOL]' in message:
        return 'agent.tool.execution'
    return 'agent.operation'


def get_event_name(message: str) -> str:
    """Determine event name from message"""
    if '[AGENT]' in message and 'Query received' in message:
        return 'agent.query.start'
    elif '[RESULT]' in message:
        return 'agent.query.complete'
    elif '[TOOL]' in message:
        return 'tool.execution'
    return 'agent.event'


def get_span_name(message: str) -> str:
    """Determine span name from message"""
    if '[AGENT]' in message:
        return 'agent.query'
    elif '[TOOL]' in message:
        tool_name = extract_tool_name(message)
        return f'tool.{tool_name}' if tool_name else 'tool.execution'
    return 'agent.operation'


def extract_query(message: str) -> str:
    """Extract query from message"""
    if 'Query received:' in message:
        return message.split('Query received:')[1].strip()
    return ''


def extract_tool_name(message: str) -> str:
    """Extract tool name from message"""
    if 'Calling' in message and '(' in message:
        tool = message.split('Calling')[1].split('(')[0].strip()
        return tool
    return ''


def extract_span_attributes(payload: Dict) -> Dict:
    """Extract relevant attributes for span"""
    attributes = {}

    if 'tool_name' in payload:
        attributes['tool_name'] = payload['tool_name']

    if 'tool_params' in payload:
        attributes['tool_params'] = payload['tool_params']

    if 'result' in payload:
        attributes['result'] = payload['result']

    return attributes


def route_to_destinations(data: Dict, customer_id: str):
    """
    Route data to appropriate destination based on size
    """
    data_size = len(json.dumps(data))
    data_size_kb = data_size / 1024

    print(f"[INFO] Data size: {data_size_kb:.2f} KB")

    # Get customer-specific endpoints
    customer_config = PORTAL26_ENDPOINTS.get(customer_id, PORTAL26_ENDPOINTS.get('default', {}))

    if not customer_config:
        print(f"[ERROR] No configuration found for customer: {customer_id}")
        return

    # Route based on size
    if data_size_kb < SIZE_THRESHOLD_KB:
        # Small traces → OTEL endpoint
        send_to_otel(data, customer_config.get('otel_endpoint'))
    else:
        # Large traces → S3
        send_to_s3(data, customer_config.get('s3_bucket'))

    # Always send to Kinesis for streaming
    send_to_kinesis(data, customer_config.get('kinesis_stream'))


def send_to_otel(data: Dict, endpoint: str):
    """Send to Portal26 OTEL endpoint"""
    import requests

    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(endpoint, json=data, headers=headers, timeout=10)
        print(f"[OTEL] Status: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] OTEL send failed: {str(e)}")


def send_to_s3(data: Dict, bucket_name: str):
    """Send to S3 for large traces"""
    try:
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H')
        trace_id = data['traces'][0]['trace_id'] if data['traces'] else 'unknown'
        key = f"traces/{timestamp}/{trace_id}.json"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        print(f"[S3] Stored: s3://{bucket_name}/{key}")
    except Exception as e:
        print(f"[ERROR] S3 send failed: {str(e)}")


def send_to_kinesis(data: Dict, stream_name: str):
    """Send to Kinesis stream"""
    try:
        trace_id = data['traces'][0]['trace_id'] if data['traces'] else 'unknown'

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(data),
            PartitionKey=trace_id
        )
        print(f"[KINESIS] Sent to stream: {stream_name}")
    except Exception as e:
        print(f"[ERROR] Kinesis send failed: {str(e)}")
