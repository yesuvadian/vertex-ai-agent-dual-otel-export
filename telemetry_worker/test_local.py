"""
Local testing script for telemetry worker
Simulates Pub/Sub message delivery
"""
import base64
import json
import requests
import sys


def create_test_message(project_id: str, trace_id: str, tenant_id: str):
    """
    Create a test log entry that mimics Vertex AI logs

    Args:
        project_id: GCP project ID
        trace_id: Trace ID (must exist in Cloud Trace)
        tenant_id: Tenant identifier

    Returns:
        Pub/Sub message format
    """
    log_entry = {
        "insertId": "test-insert-123",
        "timestamp": "2026-04-03T10:00:00.000Z",
        "severity": "INFO",
        "trace": f"projects/{project_id}/traces/{trace_id}",
        "labels": {
            "tenant_id": tenant_id
        },
        "resource": {
            "type": "aiplatform.googleapis.com/ReasoningEngine",
            "labels": {
                "project_id": project_id,
                "reasoning_engine_id": "8081657304514035712",
                "location": "us-central1"
            }
        },
        "jsonPayload": {
            "message": "Test log entry for telemetry worker"
        }
    }

    # Encode as base64
    log_json = json.dumps(log_entry)
    log_base64 = base64.b64encode(log_json.encode()).decode()

    # Create Pub/Sub message format
    pubsub_message = {
        "message": {
            "data": log_base64,
            "messageId": "test-message-123",
            "publishTime": "2026-04-03T10:00:00.000Z",
            "attributes": {}
        },
        "subscription": "projects/test/subscriptions/test"
    }

    return pubsub_message


def send_test_message(endpoint: str, message: dict):
    """
    Send test message to worker endpoint

    Args:
        endpoint: Worker endpoint URL
        message: Pub/Sub message

    Returns:
        Response from worker
    """
    print(f"Sending test message to {endpoint}")
    print(f"Message: {json.dumps(message, indent=2)}")

    response = requests.post(
        endpoint,
        json=message,
        headers={'Content-Type': 'application/json'}
    )

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.text}")

    return response


def main():
    """Main test function"""
    if len(sys.argv) < 4:
        print("Usage: python test_local.py <project_id> <trace_id> <tenant_id> [endpoint]")
        print("\nExample:")
        print("  python test_local.py agentic-ai-integration-490716 abc123def456 tenant_test")
        print("  python test_local.py agentic-ai-integration-490716 abc123def456 tenant_test http://localhost:8080/process")
        sys.exit(1)

    project_id = sys.argv[1]
    trace_id = sys.argv[2]
    tenant_id = sys.argv[3]
    endpoint = sys.argv[4] if len(sys.argv) > 4 else "http://localhost:8080/process"

    print("=" * 80)
    print("Telemetry Worker - Local Test")
    print("=" * 80)
    print(f"Project ID: {project_id}")
    print(f"Trace ID: {trace_id}")
    print(f"Tenant ID: {tenant_id}")
    print(f"Endpoint: {endpoint}")
    print("=" * 80)
    print()

    # Create test message
    message = create_test_message(project_id, trace_id, tenant_id)

    # Send to worker
    try:
        response = send_test_message(endpoint, message)
        if response.status_code == 200:
            print("\n✓ Test successful!")
        else:
            print(f"\n✗ Test failed with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Failed to connect to {endpoint}")
        print("Is the worker running? Try: python main.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == '__main__':
    main()
