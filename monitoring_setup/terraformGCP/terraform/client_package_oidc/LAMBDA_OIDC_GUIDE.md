# AWS Lambda OIDC Implementation Guide

## Overview

Your Lambda function MUST validate OIDC JWT tokens sent by GCP Pub/Sub. This guide shows you how to implement OIDC validation in your Lambda.

---

## Quick Start - Lambda Code

### Python Lambda with OIDC Validation

```python
import json
import base64
from google.oauth2 import id_token
from google.auth.transport import requests

# Your Lambda URL - must match the audience in the JWT
EXPECTED_AUDIENCE = "https://your-lambda-url.lambda-url.us-east-1.on.aws"

def lambda_handler(event, context):
    """
    Lambda handler with OIDC authentication
    """
    try:
        # Step 1: Extract OIDC token from Authorization header
        auth_header = event.get('headers', {}).get('authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Missing or invalid Authorization header'})
            }
        
        token = auth_header.replace('Bearer ', '')
        
        # Step 2: Validate OIDC token
        try:
            # Verify the token with Google's public keys
            id_info = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                EXPECTED_AUDIENCE
            )
            
            # Step 3: Verify issuer
            if id_info['iss'] not in ['https://accounts.google.com', 'accounts.google.com']:
                return {
                    'statusCode': 401,
                    'body': json.dumps({'error': 'Invalid token issuer'})
                }
            
            # Step 4: Verify audience
            if id_info['aud'] != EXPECTED_AUDIENCE:
                return {
                    'statusCode': 401,
                    'body': json.dumps({'error': 'Invalid token audience'})
                }
            
            # Token is valid! Extract service account email
            service_account_email = id_info.get('email', 'unknown')
            print(f"Authenticated request from: {service_account_email}")
            
        except ValueError as e:
            # Token validation failed
            print(f"Token validation failed: {str(e)}")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid OIDC token'})
            }
        
        # Step 5: Process the Pub/Sub message
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', {})
        
        # Decode the base64 Pub/Sub data
        if 'data' in message:
            log_data = base64.b64decode(message['data']).decode('utf-8')
            log_entry = json.loads(log_data)
            
            # Process your log entry here
            print(f"Received log: {log_entry}")
            
            # Forward to your observability platform (Portal26, etc.)
            # forward_to_observability(log_entry)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success'})
        }
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

---

## Requirements

### 1. Lambda Dependencies (requirements.txt)

```txt
google-auth>=2.0.0
cryptography>=41.0.0
```

### 2. Lambda Configuration

**Runtime**: Python 3.11 or later  
**Timeout**: 30 seconds (recommended)  
**Memory**: 256 MB (minimum)

### 3. Environment Variables

```bash
EXPECTED_AUDIENCE=https://your-lambda-url.lambda-url.us-east-1.on.aws
```

---

## Deployment

### Package Lambda with Dependencies

```bash
# Create deployment package
mkdir lambda-package
cd lambda-package

# Copy your Lambda code
cp ../lambda_function.py .

# Install dependencies
pip install -r requirements.txt -t .

# Create ZIP
zip -r lambda-deployment.zip .
```

### Deploy with AWS CLI

```bash
aws lambda update-function-code \
  --function-name your-lambda-function \
  --zip-file fileb://lambda-deployment.zip
```

---

## OIDC Token Structure

### What the Token Contains

```json
{
  "iss": "https://accounts.google.com",
  "sub": "SERVICE_ACCOUNT_UNIQUE_ID",
  "aud": "https://your-lambda-url.lambda-url.us-east-1.on.aws",
  "email": "pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com",
  "email_verified": true,
  "iat": 1234567890,
  "exp": 1234571490
}
```

### Key Claims to Validate

| Claim | Expected Value | Purpose |
|-------|----------------|---------|
| `iss` | `https://accounts.google.com` | Verify token is from Google |
| `aud` | Your Lambda URL | Verify token is for your Lambda |
| `email` | Service account email | Identify the sender |
| `exp` | Future timestamp | Verify token hasn't expired |

---

## Testing

### Test with curl (Simulated OIDC Request)

**Note**: You'll need a real OIDC token from GCP for this test.

```bash
# Get a test token (requires gcloud CLI)
TOKEN=$(gcloud auth print-identity-token \
  --impersonate-service-account=pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com \
  --audiences=https://your-lambda-url.lambda-url.us-east-1.on.aws)

# Test Lambda with token
curl -X POST https://your-lambda-url.lambda-url.us-east-1.on.aws \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":{"data":"dGVzdCBtZXNzYWdl"}}'
```

### Expected Responses

**✅ Success (200)**
```json
{"status": "success"}
```

**❌ Missing Token (401)**
```json
{"error": "Missing or invalid Authorization header"}
```

**❌ Invalid Token (401)**
```json
{"error": "Invalid OIDC token"}
```

---

## Troubleshooting

### Lambda returns 401 even with token

**Check:**
1. ✅ Token audience matches Lambda URL exactly (no trailing slash!)
2. ✅ Token issuer is `https://accounts.google.com`
3. ✅ Service account has `Token Creator` role
4. ✅ Token hasn't expired (valid for 1 hour)

### "Unable to verify token signature"

**Solutions:**
- ✅ Ensure `google-auth` package is installed
- ✅ Check Lambda has internet access (to fetch Google's public keys)
- ✅ Verify Lambda VPC configuration if in VPC

### "Token issuer mismatch"

**Check:**
- ✅ Verify issuer is exactly `https://accounts.google.com` (with https://)
- ✅ Some tokens may use `accounts.google.com` (without https://)
- ✅ Accept both in your validation code

---

## Security Best Practices

### ✅ DO:
- Validate **all three**: signature, issuer, and audience
- Log authentication failures for monitoring
- Use short token expiration (1 hour default is good)
- Rotate service account keys regularly
- Monitor for suspicious authentication patterns

### ❌ DON'T:
- Skip token validation
- Accept tokens with wrong audience
- Accept expired tokens
- Log the actual token value (sensitive!)
- Allow tokens from untrusted issuers

---

## Advanced: Custom Validation

### Add IP Whitelisting

```python
ALLOWED_GOOGLE_IPS = [
    '35.191.0.0/16',  # Google Cloud Platform
    # Add more ranges as needed
]

def validate_source_ip(event):
    source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp')
    # Check if source_ip is in ALLOWED_GOOGLE_IPS
    # Return True/False
```

### Add Rate Limiting

```python
import redis

def check_rate_limit(service_account_email):
    # Implement rate limiting per service account
    # e.g., max 1000 requests per minute
    pass
```

---

## Monitoring

### CloudWatch Metrics to Track

- `AuthenticationFailures` - 401 responses
- `TokenValidationErrors` - Invalid tokens
- `SuccessfulRequests` - 200 responses
- `ProcessingTime` - Lambda duration

### CloudWatch Alarms

```bash
# Create alarm for auth failures
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-auth-failures \
  --metric-name AuthenticationFailures \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## Complete Example

See the reference implementation:
- `lambda_poc/lambda_with_oidc.py` - Full implementation
- `lambda_poc/lambda_with_oidc_simple.py` - Simplified version
- `lambda_poc/requirements_oidc.txt` - Dependencies

---

## Next Steps

1. ✅ Implement OIDC validation in your Lambda
2. ✅ Deploy Lambda with dependencies
3. ✅ Deploy GCP Terraform (client_package_oidc)
4. ✅ Test with sample logs
5. ✅ Monitor for authentication errors
6. ✅ Set up CloudWatch alarms

**Questions?** Check the troubleshooting section or review the reference implementations.
