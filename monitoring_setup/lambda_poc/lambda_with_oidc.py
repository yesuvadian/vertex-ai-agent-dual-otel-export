"""
AWS Lambda function with OIDC (JWT) authentication
Validates Google Cloud JWT tokens from Pub/Sub push subscriptions
"""
import json
import base64
from datetime import datetime
import os
import jwt
import requests
from functools import lru_cache

# Expected JWT issuer and audience
EXPECTED_ISSUER = "https://accounts.google.com"
EXPECTED_AUDIENCE = os.environ.get('LAMBDA_URL', '')  # Set to Lambda Function URL

# Cache Google's public keys for 1 hour
@lru_cache(maxsize=1)
def get_google_public_keys():
    """
    Fetch Google's public keys for JWT verification
    """
    response = requests.get('https://www.googleapis.com/oauth2/v3/certs')
    return response.json()


def verify_jwt_token(token, audience):
    """
    Verify Google Cloud OIDC JWT token
    """
    try:
        # Get Google's public keys
        jwks = get_google_public_keys()

        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')

        if not kid:
            return None, "Missing key ID in token header"

        # Find the matching public key
        public_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break

        if not public_key:
            return None, f"Public key not found for kid: {kid}"

        # Verify and decode the token
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=audience,
            issuer=EXPECTED_ISSUER
        )

        return decoded, None

    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError as e:
        return None, f"Invalid token: {str(e)}"
    except Exception as e:
        return None, f"Token verification failed: {str(e)}"


def lambda_handler(event, context):
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] === Lambda with OIDC Auth ===")

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
    decoded_token, error = verify_jwt_token(token, EXPECTED_AUDIENCE)

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
    print(f"[OK] Token issuer: {decoded_token.get('iss')}")
    print(f"[OK] Token subject: {decoded_token.get('sub')}")
    print(f"[OK] Token email: {decoded_token.get('email', 'N/A')}")

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
                'tokenSubject': decoded_token.get('sub'),
                'tokenEmail': decoded_token.get('email'),
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
