# GCP Pub/Sub Custom Header Limitation

## Problem Discovered

GCP Pub/Sub push subscriptions **do not support arbitrary custom HTTP headers**.

The `attributes` field in `PushConfig` is for **Pub/Sub message attributes**, not HTTP headers.

## What We Tried

1. ✅ Created subscriptions with `attributes` in PushConfig
2. ❌ Headers not sent to Lambda endpoints
3. ❌ gcloud CLI doesn't support custom headers
4. ❌ REST API doesn't support custom headers
5. ❌ Python API attributes don't translate to HTTP headers

## GCP Pub/Sub Push Authentication Options

### Supported Authentication Methods:

1. **No Authentication** (current setup)
   - Auth type: NONE
   - Anyone can call the endpoint
   - ❌ Not secure

2. **OIDC Token Authentication**
   - GCP adds `Authorization: Bearer <JWT>` header
   - Lambda must verify JWT signature
   - ✅ Secure
   - ⚠️ Complex setup

3. **OAuth2 Token** (deprecated)
   - Legacy authentication
   - Not recommended

## Solution Options

### Option 1: Use OIDC Authentication (Recommended)

**Architecture:**
```
Pub/Sub → Adds OIDC JWT token → Lambda verifies JWT → Process message
```

**Pros:**
- Native GCP support
- Secure (signed tokens)
- No custom headers needed

**Cons:**
- More complex Lambda code
- Need to verify JWT signature
- Need service account setup

**Implementation:**
1. Create GCP service account
2. Grant service account permission to invoke Lambda
3. Configure Pub/Sub to use OIDC with service account
4. Update Lambda to verify JWT tokens

### Option 2: Use AWS API Gateway with API Key

**Architecture:**
```
Pub/Sub → API Gateway (validates API Key) → Lambda
```

**Pros:**
- AWS-native API Key management
- No code changes needed in Lambda
- API Gateway handles auth

**Cons:**
- Additional AWS component
- Extra cost (~$3.50/million requests)
- More infrastructure to manage

### Option 3: Use Query Parameters (Workaround)

**Architecture:**
```
Pub/Sub → Lambda URL?key=xxx → Lambda validates query param
```

**Pros:**
- Simple implementation
- Works with current setup
- No custom headers needed

**Cons:**
- API key visible in URLs/logs
- Less secure than headers
- Not best practice

### Option 4: Keep Current Setup (No Auth)

**Architecture:**
```
Pub/Sub → Lambda (no auth) → Process all messages
```

**Pros:**
- Simple
- No changes needed
- Working now

**Cons:**
- ❌ No authentication
- ❌ Anyone with URL can send messages
- ❌ Not production-ready

## Recommendation

**For Production: Use Option 1 (OIDC)**

For your use case (GCP internal logs → AWS Lambda), OIDC authentication is the best solution:

1. GCP natively supports it
2. Industry-standard JWT tokens
3. Secure without custom headers
4. Can verify token issuer is GCP

**For Development/Testing: Keep Current Setup (Option 4)**

Since these are internal logs from your own Reasoning Engine:
- Low security risk (internal telemetry data)
- Lambda URLs are obscured (hard to guess)
- Can add CloudWatch alarms for unusual patterns

## Current Status

**✅ Working:**
- 2 Lambda functions deployed
- 2 Pub/Sub subscriptions created
- Messages flowing GCP → AWS
- Logs captured in CloudWatch

**❌ Not Working:**
- Custom header authentication
- API Key validation
- Shared Secret validation

**Why:**
- GCP Pub/Sub doesn't support arbitrary HTTP headers in push subscriptions
- Only supports OIDC/OAuth authentication headers

## Next Steps

### Immediate (Keep working setup):
1. Continue using current setup without auth
2. Monitor Lambda CloudWatch logs
3. Add CloudWatch alarms for anomalies

### Short-term (Add security):
1. Implement OIDC authentication (see OIDC_SETUP.md)
2. Update Lambda to verify JWT tokens
3. Test end-to-end

### Long-term (Production):
1. Use AWS API Gateway with API Keys
2. Add rate limiting
3. Add monitoring and alerting
4. Implement IAM-based access control

## Files Status

**Working:**
- `lambda_with_api_key.py` - Lambda code (works with curl, not Pub/Sub)
- `lambda_with_shared_secret.py` - Lambda code (works with curl, not Pub/Sub)
- Current Pub/Sub → Lambda flow (no auth)

**Not Working:**
- Custom header injection from Pub/Sub
- GCP → AWS authentication

**Solution:**
- Need to implement OIDC or use API Gateway
- Or accept no auth for internal logs
