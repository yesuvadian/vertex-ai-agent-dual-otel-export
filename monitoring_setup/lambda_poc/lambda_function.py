"""
GCP Pub/Sub to AWS Lambda - Proof of Concept
Simple Lambda function to receive and log GCP Pub/Sub messages
"""
import json
import base64
from datetime import datetime

def lambda_handler(event, context):
    """
    Lambda handler for GCP Pub/Sub push messages

    Args:
        event: API Gateway event containing Pub/Sub message
        context: Lambda context object

    Returns:
        Response with status code and body
    """
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] === Received event from GCP Pub/Sub ===")

    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body'])
            print(f"Request body parsed successfully")
        else:
            # Direct invocation (not via API Gateway)
            body = event
            print(f"Direct Lambda invocation detected")

        # Extract Pub/Sub message
        if 'message' not in body:
            print(f"ERROR: No 'message' field in body")
            print(f"Body keys: {list(body.keys())}")
            return error_response(400, "Invalid message format: missing 'message' field")

        message = body['message']
        print(f"Message extracted successfully")

        # Extract and decode message data
        message_data = None
        if 'data' in message:
            try:
                encoded_data = message['data']
                decoded_bytes = base64.b64decode(encoded_data)
                message_data = decoded_bytes.decode('utf-8')
                print(f"[OK] Message Data: {message_data}")
            except Exception as e:
                print(f"ERROR decoding message data: {str(e)}")
                message_data = f"[Error decoding: {str(e)}]"
        else:
            print(f"WARNING: No 'data' field in message")

        # Extract message metadata
        message_id = message.get('messageId', 'unknown')
        publish_time = message.get('publishTime', 'unknown')
        attributes = message.get('attributes', {})

        print(f"[INFO] Message ID: {message_id}")
        print(f"[INFO] Publish Time: {publish_time}")

        if attributes:
            print(f"[INFO] Attributes: {json.dumps(attributes, indent=2)}")
        else:
            print(f"[INFO] Attributes: None")

        # Log full event for debugging
        print(f"\n[DEBUG] Full Event:")
        print(json.dumps(event, indent=2, default=str))

        # Success response
        response_body = {
            'status': 'success',
            'message': 'Message received and processed',
            'messageId': message_id,
            'publishTime': publish_time,
            'dataPreview': message_data[:100] if message_data else None,
            'timestamp': timestamp
        }

        print(f"\n[SUCCESS] Message processed")
        print(f"Response: {json.dumps(response_body, indent=2)}")

        return success_response(response_body)

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode failed: {str(e)}")
        print(f"Raw body: {event.get('body', 'No body')[:500]}")
        return error_response(400, f"Invalid JSON: {str(e)}")

    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return error_response(500, f"Internal error: {str(e)}")


def success_response(body):
    """Return success response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'X-Processing-Status': 'success'
        },
        'body': json.dumps(body)
    }


def error_response(status_code, message):
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'X-Processing-Status': 'error'
        },
        'body': json.dumps({
            'status': 'error',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
