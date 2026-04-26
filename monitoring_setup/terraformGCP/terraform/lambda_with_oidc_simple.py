"""
AWS Lambda function with OIDC (JWT) authentication - Simplified
Uses requests library to verify JWT with Google's tokeninfo endpoint
No cryptography library needed
"""
import json
import base64
from datetime import datetime
import os
import urllib.request
import urllib.error

# Expected JWT audience
EXPECTED_AUDIENCE = os.environ.get('LAMBDA_URL', '')
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def verify_jwt_token_simple(token, audience):
    """
    Verify Google Cloud OIDC JWT token using Google's tokeninfo endpoint
    Simpler approach - no cryptography library needed
    """
    try:
        # Call Google's tokeninfo endpoint
        url = f"{GOOGLE_TOKENINFO_URL}?id_token={token}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            token_info = json.loads(response.read().decode())

        # Verify audience
        if token_info.get('aud') != audience:
            return None, f"Invalid audience. Expected: {audience}, Got: {token_info.get('aud')}"

        # Verify issuer
        issuer = token_info.get('iss')
        if issuer not in ['https://accounts.google.com', 'accounts.google.com']:
            return None, f"Invalid issuer: {issuer}"

        # Check if token is expired (Google returns error if expired)
        if 'error' in token_info:
            return None, token_info.get('error_description', 'Token validation failed')

        return token_info, None

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        return None, f"Token verification failed: HTTP {e.code} - {error_body}"
    except Exception as e:
        return None, f"Token verification failed: {str(e)}"


def lambda_handler(event, context):
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] === Lambda with OIDC Auth (Simple) ===")

    # Get Authorization header
    headers = event.get('headers', {})
    auth_header = headers.get('authorization') or headers.get('Authorization')

    if not auth_header:
        print(f"[ERROR] Missing Authorization header")
        return {
            'statusCode': 401,
            'body': json.dumps({
                'error': 'Unauthorized',
                'message': 'Missing Authorization header'
            })
        }

    # Extract Bearer token
    if not auth_header.startswith('Bearer '):
        print(f"[ERROR] Invalid Authorization header format")
        return {
            'statusCode': 401,
            'body': json.dumps({
                'error': 'Unauthorized',
                'message': 'Invalid Authorization header format. Expected: Bearer <token>'
            })
        }

    token = auth_header.replace('Bearer ', '')
    print(f"[INFO] Received JWT token (length: {len(token)})")

    # Verify JWT token
    token_info, error = verify_jwt_token_simple(token, EXPECTED_AUDIENCE)

    if error:
        print(f"[ERROR] JWT verification failed: {error}")
        return {
            'statusCode': 403,
            'body': json.dumps({
                'error': 'Forbidden',
                'message': f'JWT verification failed: {error}'
            })
        }

    print(f"[OK] JWT token validated successfully")
    print(f"[OK] Token issuer: {token_info.get('iss')}")
    print(f"[OK] Token subject: {token_info.get('sub')}")
    print(f"[OK] Token email: {token_info.get('email', 'N/A')}")
    print(f"[OK] Token audience: {token_info.get('aud')}")

    # Process Pub/Sub message
    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        message = body.get('message', {})
        encoded_data = message.get('data', '')

        if encoded_data:
            decoded_bytes = base64.b64decode(encoded_data)
            message_data = decoded_bytes.decode('utf-8')
            print(f"[OK] Message Data: {message_data[:200]}")
        else:
            message_data = "No data in message"
            print(f"[WARN] Empty message received")

        # Log successful processing
        print(f"[OK] Message processed successfully")
        print(f"[OK] Message ID: {message.get('messageId', 'unknown')}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'Message received and processed with OIDC auth',
                'messageId': message.get('messageId'),
                'dataPreview': message_data[:100] if message_data else None,
                'tokenSubject': token_info.get('sub'),
                'tokenEmail': token_info.get('email'),
                'timestamp': timestamp
            })
        }

    except Exception as e:
        print(f"[ERROR] Processing failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e)
            })
        }
