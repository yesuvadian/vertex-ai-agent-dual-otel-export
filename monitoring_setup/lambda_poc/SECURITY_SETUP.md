# Security Setup - API Key and Shared Secret Authentication

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCP Environment                               │
│                                                                  │
│  Vertex AI Reasoning Engine                                     │
│            ↓                                                     │
│  Cloud Logging                                                   │
│            ↓                                                     │
│  Log Sink                                                        │
│            ↓                                                     │
│  Pub/Sub Topic: reasoning-engine-logs-topic                     │
│            ↓                                                     │
│  ┌──────────────────────┬──────────────────────┐               │
│  │                      │                      │               │
│  │ Subscription 1       │ Subscription 2       │               │
│  │ (API Key)            │ (Shared Secret)      │               │
│  │                      │                      │               │
│  │ Header:              │ Header:              │               │
│  │ X-API-Key: xxx       │ X-Shared-Secret: yyy │               │
│  └──────────┬───────────┴──────────┬───────────┘               │
│             │                      │                            │
└─────────────┼──────────────────────┼────────────────────────────┘
              │                      │
              │ HTTPS Push           │ HTTPS Push
              │ with header          │ with header
              ↓                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Environment                               │
│                                                                  │
│  ┌──────────────────────┐    ┌──────────────────────┐          │
│  │ Lambda Function 1     │    │ Lambda Function 2     │          │
│  │ gcp-pubsub-api-key    │    │ gcp-pubsub-shared-    │          │
│  │                       │    │ secret                │          │
│  │ Validates:            │    │ Validates:            │          │
│  │ X-API-Key header      │    │ X-Shared-Secret       │          │
│  │                       │    │ header                │          │
│  │ Returns:              │    │ Returns:              │          │
│  │ 200 if valid          │    │ 200 if valid          │          │
│  │ 401/403 if invalid    │    │ 401/403 if invalid    │          │
│  └───────────┬───────────┘    └───────────┬───────────┘          │
│              │                            │                      │
│              ↓                            ↓                      │
│  CloudWatch Logs                  CloudWatch Logs               │
│  /aws/lambda/                     /aws/lambda/                  │
│  gcp-pubsub-api-key               gcp-pubsub-shared-secret      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Steps

### Step 1: Deploy AWS Lambda Functions

Run the deployment script:

```bash
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup\lambda_poc
bash deploy_secured_lambdas.sh
```

**This creates:**
- Lambda function: `gcp-pubsub-api-key` with API Key validation
- Lambda function: `gcp-pubsub-shared-secret` with Shared Secret validation
- Function URLs for both Lambdas (public endpoints)
- Credentials file: `lambda_credentials.txt`

**Output:**
```
Function Name: gcp-pubsub-api-key
Function URL: https://abc123.lambda-url.us-east-1.on.aws/
API Key: gcp-to-aws-api-key-1234567890

Function Name: gcp-pubsub-shared-secret
Function URL: https://xyz789.lambda-url.us-east-1.on.aws/
Shared Secret: gcp-to-aws-shared-secret-0987654321
```

### Step 2: Create GCP Pub/Sub Subscriptions

Run the GCP setup script:

```bash
bash setup_gcp_pubsub_with_auth.sh
```

**This creates:**
- Pub/Sub subscription: `reasoning-engine-to-api-key`
- Pub/Sub subscription: `reasoning-engine-to-shared-secret`
- Secret Manager secrets for credentials
- Service account for push authentication
- Manual setup instructions: `MANUAL_HEADER_SETUP.md`

### Step 3: Add Custom Headers (Manual)

**GCP Console doesn't support custom headers via CLI, so add them manually:**

#### For API Key Subscription:

1. Open: https://console.cloud.google.com/cloudpubsub/subscription/list?project=agentic-ai-integration-490716

2. Click: `reasoning-engine-to-api-key`

3. Click: **EDIT**

4. Scroll to "Push endpoint" section

5. Click: **Add header**

6. Enter:
   - **Name**: `X-API-Key`
   - **Value**: `[Copy from lambda_credentials.txt]`

7. Click: **UPDATE**

#### For Shared Secret Subscription:

1. Click: `reasoning-engine-to-shared-secret`

2. Click: **EDIT**

3. Scroll to "Push endpoint" section

4. Click: **Add header**

5. Enter:
   - **Name**: `X-Shared-Secret`
   - **Value**: `[Copy from lambda_credentials.txt]`

6. Click: **UPDATE**

### Step 4: Test End-to-End

Run the agent test:

```bash
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup\lambda_poc
python test_local.py
```

**Check AWS Lambda logs (wait 1-2 minutes):**

```bash
# Check API Key Lambda
aws logs tail /aws/lambda/gcp-pubsub-api-key --since 5m --region us-east-1 --format short

# Check Shared Secret Lambda
aws logs tail /aws/lambda/gcp-pubsub-shared-secret --since 5m --region us-east-1 --format short
```

**Expected output:**
```
[OK] API Key validated successfully
[OK] Message Data: [AGENT] Query called...
[OK] Message processed successfully
```

---

## Authentication Methods

### Method 1: API Key

**How it works:**
1. GCP Pub/Sub adds `X-API-Key` header to push request
2. Lambda validates header matches environment variable
3. Returns 200 if valid, 401/403 if invalid

**Lambda code:**
```python
VALID_API_KEY = os.environ.get('API_KEY')

headers = event.get('headers', {})
api_key = headers.get('x-api-key') or headers.get('X-API-Key')

if api_key != VALID_API_KEY:
    return {'statusCode': 403, 'body': 'Invalid API Key'}
```

**Pros:**
- Simple implementation
- Easy to rotate (update env variable)
- Standard HTTP header

**Cons:**
- Symmetric key (both sides know the secret)
- No request signing (replay attacks possible)

### Method 2: Shared Secret

**How it works:**
1. GCP Pub/Sub adds `X-Shared-Secret` header to push request
2. Lambda validates header matches environment variable
3. Returns 200 if valid, 401/403 if invalid

**Lambda code:**
```python
SHARED_SECRET = os.environ.get('SHARED_SECRET')

headers = event.get('headers', {})
shared_secret = headers.get('x-shared-secret') or headers.get('X-Shared-Secret')

if shared_secret != SHARED_SECRET:
    return {'statusCode': 403, 'body': 'Invalid Shared Secret'}
```

**Pros:**
- Simple implementation
- Easy to rotate
- Can use HMAC for request signing (enhanced version)

**Cons:**
- Symmetric key
- Basic version has no request signing

### Method 3: HMAC Signature (Enhanced Shared Secret)

**For enhanced security, modify Lambda to verify HMAC signature:**

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

# In Lambda handler:
body = event.get('body', '')
signature = headers.get('x-signature')
if not verify_signature(body, signature, SHARED_SECRET):
    return {'statusCode': 403, 'body': 'Invalid signature'}
```

---

## Security Comparison

| Feature | No Auth | API Key | Shared Secret | HMAC Signature |
|---------|---------|---------|---------------|----------------|
| **Prevents unauthorized access** | ❌ | ✅ | ✅ | ✅ |
| **Prevents replay attacks** | ❌ | ❌ | ❌ | ✅ |
| **Easy to implement** | ✅ | ✅ | ✅ | ⚠️ |
| **Easy to rotate** | N/A | ✅ | ✅ | ✅ |
| **GCP native support** | ✅ | ⚠️ | ⚠️ | ❌ |
| **Request integrity** | ❌ | ❌ | ❌ | ✅ |

**Legend:**
- ✅ Yes / Good
- ⚠️ Partial / Manual setup
- ❌ No / Not supported

---

## Credentials Management

### Current Setup

**Credentials stored in:**
1. AWS Lambda environment variables
2. GCP Secret Manager (optional)
3. Local file: `lambda_credentials.txt` (for reference)

**Rotation procedure:**
1. Update Lambda environment variable
2. Update Pub/Sub subscription headers via Console
3. No downtime required

### Best Practices

**DO:**
- Store credentials in AWS Secrets Manager or Parameter Store
- Use different keys per environment (dev/staging/prod)
- Rotate credentials regularly (90 days)
- Use separate keys for different tenants
- Log all authentication failures

**DON'T:**
- Commit credentials to Git
- Share credentials between environments
- Use weak or predictable secrets
- Log credential values

---

## Troubleshooting

### Issue 1: 401 Unauthorized

**Symptom:** Lambda returns 401

**Causes:**
- Header not configured in Pub/Sub subscription
- Header name mismatch (case-sensitive)

**Fix:**
1. Check Pub/Sub subscription config
2. Verify header is added: `X-API-Key` or `X-Shared-Secret`
3. Check Lambda logs for missing header message

### Issue 2: 403 Forbidden

**Symptom:** Lambda returns 403

**Causes:**
- Invalid credential value
- Credential mismatch between GCP and AWS

**Fix:**
1. Check `lambda_credentials.txt` for correct values
2. Verify Lambda environment variable matches
3. Update Pub/Sub subscription header with correct value

### Issue 3: Messages not reaching Lambda

**Symptom:** No logs in CloudWatch

**Causes:**
- Pub/Sub subscription not configured
- Lambda URL incorrect
- Function URL permissions not set

**Fix:**
1. Check subscription exists and is active
2. Verify push endpoint URL in subscription
3. Check Lambda Function URL is public (auth-type: NONE)

### Issue 4: Headers not being sent

**Symptom:** Lambda logs show "Missing header"

**Causes:**
- Custom headers not configured in GCP Console
- gcloud CLI doesn't support custom headers

**Fix:**
1. Follow manual setup in `MANUAL_HEADER_SETUP.md`
2. Use GCP Console to add headers
3. Verify in Lambda logs that headers are received

---

## Testing

### Test 1: Direct Lambda invocation (without GCP)

```bash
# Test API Key Lambda
curl -X POST "https://abc123.lambda-url.us-east-1.on.aws/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: gcp-to-aws-api-key-1234567890" \
  -d '{"message":{"data":"SGVsbG8=","messageId":"test-001"}}'

# Should return: {"status": "success", ...}
```

```bash
# Test without API Key (should fail)
curl -X POST "https://abc123.lambda-url.us-east-1.on.aws/" \
  -H "Content-Type: application/json" \
  -d '{"message":{"data":"SGVsbG8="}}'

# Should return: {"error": "Unauthorized", ...}
```

### Test 2: End-to-end via Reasoning Engine

```bash
python test_local.py
```

Wait 1-2 minutes, then check both Lambda logs:

```bash
aws logs tail /aws/lambda/gcp-pubsub-api-key --since 5m --region us-east-1
aws logs tail /aws/lambda/gcp-pubsub-shared-secret --since 5m --region us-east-1
```

### Test 3: Monitor authentication failures

```bash
# Watch for 401/403 errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/gcp-pubsub-api-key \
  --filter-pattern "[ERROR]" \
  --start-time $(date -d '10 minutes ago' +%s)000 \
  --region us-east-1
```

---

## Cost Impact

### Additional Costs

| Component | Before | After | Difference |
|-----------|--------|-------|------------|
| Lambda Functions | 1 | 3 | +2 |
| Lambda Invocations | 10K/month | 30K/month | +20K |
| Pub/Sub Subscriptions | 1 | 3 | +2 |
| Secret Manager | 0 | 2 secrets | +2 |

### Monthly Cost Estimate (10K messages)

**GCP:**
- Pub/Sub (2 additional subs): +$0.80
- Secret Manager (2 secrets): +$0.12
- **GCP Additional: $0.92**

**AWS:**
- Lambda invocations (20K additional): +$0.40
- Lambda duration: +$0.10
- CloudWatch logs: +$1.00
- **AWS Additional: $1.50**

**Total Additional Cost: $2.42/month**

**Grand Total: $4.57/month** (vs $2.15 without security)

---

## Summary

**Created:**
- ✅ 2 secured Lambda functions (API Key + Shared Secret)
- ✅ 2 GCP Pub/Sub subscriptions
- ✅ Credentials management setup
- ✅ Testing and troubleshooting guides

**Architecture:**
- ✅ Reasoning Engine → Cloud Logging → Pub/Sub → 2 Lambdas
- ✅ Each subscription uses different authentication
- ✅ Headers configured manually via GCP Console

**Next Steps:**
1. Run deployment scripts
2. Add headers in GCP Console
3. Test end-to-end
4. Monitor authentication logs
