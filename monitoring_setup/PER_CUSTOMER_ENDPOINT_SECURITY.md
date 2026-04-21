# Per-Customer Endpoint Security Requirements

## Architecture: One Endpoint Per Customer

```
Customer 1 (GCP Pub/Sub) ──> https://api.example.com/webhook/customer1 ──┐
Customer 2 (GCP Pub/Sub) ──> https://api.example.com/webhook/customer2 ──┼──> Single Lambda ──> Portal26
Customer 3 (GCP Pub/Sub) ──> https://api.example.com/webhook/customer3 ──┘
```

**Key Difference from Shared Endpoint:**
- Shared: All customers → `https://api.example.com/webhook` (customer identified by auth token)
- Per-customer: Each customer → `https://api.example.com/webhook/{customer_id}` (customer identified by URL path)

---

## Critical Security Question

### ❌ Common Misconception:
> "If each customer has their own endpoint URL, we don't need authentication, right?"

### ✅ Reality:
**NO! You MUST still authenticate. The URL path is NOT security.**

**Why:**
- URL is not a secret - it's visible in logs, network traffic, DNS queries
- Attacker can enumerate endpoints: `/webhook/customer1`, `/webhook/customer2`, etc.
- Customer can accidentally expose URL in documentation, support tickets, screenshots
- Anyone who knows the URL can send malicious data to that endpoint

---

## Security Requirements for Per-Customer Endpoints

### 1. URL Path Does NOT Replace Authentication

**Insecure (NEVER DO THIS):**
```python
# ❌ BAD: Trust the URL path without authentication
@app.route('/webhook/<customer_id>', methods=['POST'])
def webhook(customer_id):
    # Attacker can call /webhook/customer1 and inject fake data
    process_log(customer_id, request.json)
```

**Secure:**
```python
# ✅ GOOD: Validate authentication FIRST, then check URL matches
@app.route('/webhook/<customer_id>', methods=['POST'])
def webhook(customer_id):
    # Step 1: Authenticate (OIDC token, API key, mTLS)
    authenticated_customer = authenticate_request(request)
    
    # Step 2: Authorize - ensure authenticated customer matches URL path
    if authenticated_customer != customer_id:
        return 403  # Customer1 trying to access customer2's endpoint
    
    # Step 3: Process
    process_log(customer_id, request.json)
```

---

## Required Security Layers

### Layer 1: Network Security

**Requirements:**
- ✅ TLS 1.2+ encryption (HTTPS only)
- ✅ Rate limiting per endpoint: 1000 req/sec per customer
- ✅ IP allowlisting per customer (optional but recommended)
- ✅ WAF rules to block common attacks
- ✅ DDoS protection

**Implementation:**
```yaml
API Gateway Configuration:
  - HTTPS only (no HTTP)
  - Rate limit: 1000 req/sec per path
  - Usage plan per customer endpoint
  - CloudFront in front for DDoS protection
```

**Why per-customer endpoints increase risk:**
- More URL paths = larger attack surface
- Attacker can target specific customers
- Must configure rate limiting for EACH endpoint

---

### Layer 2: Authentication (Required for Each Endpoint)

You MUST implement ONE of these authentication methods for EACH endpoint:

#### Option A: OIDC Token (Recommended)

**Configuration:**
```python
# Each customer has unique service account
customer_allowlist = {
    "customer1@project.iam.gserviceaccount.com": "customer1",
    "customer2@project.iam.gserviceaccount.com": "customer2",
    "customer3@project.iam.gserviceaccount.com": "customer3"
}

def authenticate(request, customer_id_from_url):
    # Extract JWT from Authorization header
    token = request.headers.get('Authorization')
    
    # Verify JWT signature
    decoded = verify_jwt_signature(token)
    
    # Extract service account email
    service_account = decoded['email']
    
    # Check service account is in allowlist
    if service_account not in customer_allowlist:
        raise AuthenticationError("Unknown service account")
    
    # Verify service account matches URL customer ID
    expected_customer = customer_allowlist[service_account]
    if expected_customer != customer_id_from_url:
        raise AuthorizationError(f"Service account {service_account} cannot access {customer_id_from_url}")
    
    return expected_customer
```

**GCP Customer Setup:**
```bash
# Customer 1 creates service account
gcloud iam service-accounts create customer1-pubsub \
  --display-name "Customer 1 Pub/Sub Forwarder"

# Customer 1 creates push subscription to their specific endpoint
gcloud pubsub subscriptions create customer1-telemetry \
  --topic vertex-telemetry-topic \
  --push-endpoint https://api.example.com/webhook/customer1 \
  --push-auth-service-account customer1-pubsub@project.iam.gserviceaccount.com
```

#### Option B: API Key Per Customer

**Configuration:**
```python
# Each customer has unique API key
customer_api_keys = {
    "customer1": "cust1_key_abc123def456ghi789",
    "customer2": "cust2_key_xyz789abc123def456",
    "customer3": "cust3_key_mno456pqr789stu012"
}

def authenticate(request, customer_id_from_url):
    # Extract API key from X-API-Key header
    api_key = request.headers.get('X-API-Key')
    
    # Check if customer exists
    if customer_id_from_url not in customer_api_keys:
        raise AuthenticationError("Unknown customer")
    
    # Verify API key matches
    expected_key = customer_api_keys[customer_id_from_url]
    if api_key != expected_key:
        raise AuthenticationError("Invalid API key")
    
    return customer_id_from_url
```

**Security Risk with API Keys:**
- ⚠️ If attacker gets customer1's API key, they can only attack customer1's endpoint
- ⚠️ But they can still send fake data to customer1
- ⚠️ Must implement IP allowlisting to mitigate

#### Option C: mTLS Certificate Per Customer

**Configuration:**
```python
# Each customer has unique client certificate
customer_certificates = {
    "CN=customer1.example.com": "customer1",
    "CN=customer2.example.com": "customer2",
    "CN=customer3.example.com": "customer3"
}

def authenticate(request, customer_id_from_url):
    # Extract client certificate from TLS handshake
    client_cert_cn = request.environ.get('SSL_CLIENT_S_DN_CN')
    
    # Check certificate is in allowlist
    if client_cert_cn not in customer_certificates:
        raise AuthenticationError("Unknown certificate")
    
    # Verify certificate matches URL customer ID
    expected_customer = customer_certificates[client_cert_cn]
    if expected_customer != customer_id_from_url:
        raise AuthorizationError(f"Certificate {client_cert_cn} cannot access {customer_id_from_url}")
    
    return expected_customer
```

---

### Layer 3: Authorization (Path-to-Customer Validation)

**Critical Security Check:**
```python
def authorize(authenticated_customer_id, url_path_customer_id):
    """
    Prevent customer1 from calling customer2's endpoint
    even if customer1 has valid authentication
    """
    if authenticated_customer_id != url_path_customer_id:
        logger.warning(
            f"Authorization violation: {authenticated_customer_id} "
            f"tried to access {url_path_customer_id} endpoint"
        )
        raise AuthorizationError(
            "You are not authorized to access this endpoint"
        )
    
    return True
```

**Attack Scenario this Prevents:**
1. Customer 1 has valid OIDC token for their service account
2. Customer 1 tries to call `/webhook/customer2` with their token
3. Authentication passes (valid token)
4. Authorization FAILS (token is for customer1, not customer2)
5. Request rejected with 403 Forbidden

---

### Layer 4: Input Validation

**Requirements:**
```python
def validate_input(request, customer_id):
    """
    Validate incoming Pub/Sub message structure
    """
    # Check Content-Type
    if request.content_type != 'application/json':
        raise ValidationError("Invalid content type")
    
    # Parse JSON
    try:
        data = request.get_json()
    except:
        raise ValidationError("Invalid JSON")
    
    # Validate Pub/Sub message structure
    if 'message' not in data:
        raise ValidationError("Missing 'message' field")
    
    if 'data' not in data['message']:
        raise ValidationError("Missing 'message.data' field")
    
    # Validate message age (prevent replay)
    message_age = get_message_age(data['message'])
    if message_age > 600:  # 10 minutes
        raise ValidationError("Message too old (possible replay attack)")
    
    # Decode and validate log entry
    log_entry = decode_pubsub_message(data['message']['data'])
    
    # Validate log entry structure
    if 'resource' not in log_entry:
        raise ValidationError("Invalid log entry: missing 'resource'")
    
    # Optional: Validate customer ID in log matches URL customer ID
    if 'customer_id' in log_entry.get('labels', {}):
        if log_entry['labels']['customer_id'] != customer_id:
            raise ValidationError("Customer ID mismatch in log entry")
    
    return log_entry
```

---

### Layer 5: Endpoint Enumeration Prevention

**Attack: Endpoint Discovery**
```bash
# Attacker tries to discover customer endpoints
curl https://api.example.com/webhook/customer1  # 200 OK?
curl https://api.example.com/webhook/customer2  # 200 OK?
curl https://api.example.com/webhook/customer999  # 404 Not Found?
```

**Security Requirement:**
```python
# ✅ GOOD: Return same response for valid and invalid customer IDs
@app.route('/webhook/<customer_id>', methods=['POST'])
def webhook(customer_id):
    try:
        # Authenticate
        authenticated_customer = authenticate_request(request)
        
        # Authorize
        if authenticated_customer != customer_id:
            # Don't reveal if customer_id exists or not
            return jsonify({"status": "error"}), 401
        
        # Process
        process_log(customer_id, request.json)
        return jsonify({"status": "success"}), 200
        
    except AuthenticationError:
        # Same response whether customer exists or not
        return jsonify({"status": "error"}), 401
    
    except Exception as e:
        # Generic error, don't leak information
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error"}), 500

# ❌ BAD: Different responses leak information
@app.route('/webhook/<customer_id>', methods=['POST'])
def webhook_insecure(customer_id):
    if customer_id not in valid_customers:
        return jsonify({"error": "Customer not found"}), 404  # Leaks info!
    
    # ... rest of processing
```

**Why this matters:**
- Attacker can enumerate all customer IDs
- Attacker learns how many customers you have
- Attacker can target specific customers with social engineering

**Mitigation:**
- ✅ Return 401 for both "customer doesn't exist" and "invalid auth"
- ✅ Don't leak customer IDs in error messages
- ✅ Use generic error responses
- ✅ Log attempted enumerations for monitoring

---

### Layer 6: Rate Limiting Per Customer

**Requirements:**
```python
# Configure per-customer rate limits
rate_limits = {
    "customer1": 1000,  # req/sec
    "customer2": 500,   # req/sec (smaller customer)
    "customer3": 2000   # req/sec (enterprise customer)
}

def check_rate_limit(customer_id):
    """
    Prevent one customer from affecting others
    """
    current_rate = get_current_rate(customer_id)
    limit = rate_limits.get(customer_id, 100)  # Default 100 req/sec
    
    if current_rate > limit:
        raise RateLimitError(f"Rate limit exceeded: {current_rate}/{limit}")
```

**Why per-customer rate limiting is critical:**
- Customer 1 can't DDoS Customer 2's endpoint
- Compromised customer can't affect others
- Can offer tiered rate limits (basic vs enterprise)

**Implementation in API Gateway:**
```yaml
API Gateway Usage Plans:
  customer1-plan:
    quota: 1000 requests per second
    throttle: 1000 requests per second burst
    api_key: customer1-key
    
  customer2-plan:
    quota: 500 requests per second
    throttle: 500 requests per second burst
    api_key: customer2-key
```

---

### Layer 7: Monitoring & Alerting Per Endpoint

**Requirements:**
```python
# Monitor each customer endpoint separately
metrics = {
    "customer1": {
        "requests": 150000,
        "errors": 12,
        "latency_p95": 250,  # ms
        "error_rate": 0.008  # 0.8%
    },
    "customer2": {
        "requests": 50000,
        "errors": 500,  # High error rate!
        "latency_p95": 300,
        "error_rate": 0.01  # 1% - needs investigation
    }
}

# Alert if customer-specific issues
def check_customer_health(customer_id):
    if metrics[customer_id]["error_rate"] > 0.05:  # >5%
        alert(f"High error rate for {customer_id}: {metrics[customer_id]['error_rate']}")
    
    if metrics[customer_id]["latency_p95"] > 1000:  # >1s
        alert(f"High latency for {customer_id}: {metrics[customer_id]['latency_p95']}ms")
```

**CloudWatch Dashboards:**
```yaml
Per-Customer Metrics:
  - customer1/requests
  - customer1/errors
  - customer1/latency
  - customer2/requests
  - customer2/errors
  - customer2/latency
  ...
```

**Why this is harder with per-customer endpoints:**
- Must create N customer-specific dashboards
- Must configure N customer-specific alarms
- Harder to see cross-customer patterns

---

## Complete Security Flow

### Request Processing with Per-Customer Endpoints

```python
"""
Complete secure webhook handler for per-customer endpoints
"""
from flask import Flask, request, jsonify
import jwt
import time

app = Flask(__name__)

# Configuration
customer_allowlist = {
    "customer1@project.iam.gserviceaccount.com": "customer1",
    "customer2@project.iam.gserviceaccount.com": "customer2",
    "customer3@project.iam.gserviceaccount.com": "customer3"
}

@app.route('/webhook/<customer_id>', methods=['POST'])
def webhook(customer_id):
    """
    Secure webhook handler with per-customer endpoints
    """
    start_time = time.time()
    
    try:
        # LAYER 1: RATE LIMITING
        check_rate_limit(customer_id)
        
        # LAYER 2: AUTHENTICATION (verify OIDC token)
        authenticated_customer = authenticate_oidc_token(request)
        
        # LAYER 3: AUTHORIZATION (verify token matches URL)
        if authenticated_customer != customer_id:
            log_security_event(
                event="authorization_violation",
                authenticated_customer=authenticated_customer,
                requested_customer=customer_id,
                ip=request.remote_addr
            )
            return jsonify({"status": "error"}), 403
        
        # LAYER 4: INPUT VALIDATION
        log_entry = validate_and_parse_pubsub_message(request)
        
        # LAYER 5: BUSINESS LOGIC
        otel_log = convert_to_otel_format(log_entry, customer_id)
        
        # LAYER 6: FORWARD TO PORTAL26
        success = send_to_portal26(otel_log, customer_id)
        
        # LAYER 7: METRICS & LOGGING
        latency = (time.time() - start_time) * 1000
        record_metrics(customer_id, success, latency)
        
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 500
            
    except RateLimitError:
        record_metrics(customer_id, success=False, error_type="rate_limit")
        return jsonify({"status": "error"}), 429
        
    except AuthenticationError as e:
        log_security_event(
            event="authentication_failure",
            customer_id=customer_id,
            error=str(e),
            ip=request.remote_addr
        )
        # Generic error - don't leak information
        return jsonify({"status": "error"}), 401
        
    except ValidationError as e:
        record_metrics(customer_id, success=False, error_type="validation")
        return jsonify({"status": "error"}), 400
        
    except Exception as e:
        logger.error(f"Unexpected error for {customer_id}: {e}")
        record_metrics(customer_id, success=False, error_type="internal")
        return jsonify({"status": "error"}), 500

def authenticate_oidc_token(request):
    """
    Authenticate OIDC token from GCP Pub/Sub
    """
    # Extract Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise AuthenticationError("Missing or invalid Authorization header")
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    # Verify JWT signature using Google's public keys
    try:
        decoded = jwt.decode(
            token,
            options={"verify_signature": True},
            algorithms=["RS256"],
            audience="https://api.example.com/webhook"
        )
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}")
    
    # Extract service account email
    service_account = decoded.get('email')
    if not service_account:
        raise AuthenticationError("Token missing 'email' claim")
    
    # Check if service account is in allowlist
    if service_account not in customer_allowlist:
        raise AuthenticationError("Service account not authorized")
    
    # Return customer ID
    return customer_allowlist[service_account]

def check_rate_limit(customer_id):
    """
    Check if customer exceeded rate limit
    """
    # Implementation depends on rate limiting backend (Redis, DynamoDB, etc.)
    pass

def validate_and_parse_pubsub_message(request):
    """
    Validate and parse Pub/Sub message
    """
    # Check Content-Type
    if request.content_type != 'application/json':
        raise ValidationError("Invalid content type")
    
    # Parse JSON
    data = request.get_json()
    if not data or 'message' not in data:
        raise ValidationError("Invalid Pub/Sub message structure")
    
    # Decode base64 data
    import base64
    message_data = base64.b64decode(data['message']['data'])
    log_entry = json.loads(message_data)
    
    return log_entry

def send_to_portal26(otel_log, customer_id):
    """
    Send log to Portal26 with customer isolation
    """
    # Add customer.id attribute for isolation
    otel_log['attributes'].append({
        "key": "customer.id",
        "value": {"stringValue": customer_id}
    })
    
    # Send to Portal26
    # Implementation...
    return True

def record_metrics(customer_id, success, latency=None, error_type=None):
    """
    Record per-customer metrics
    """
    # CloudWatch or other metrics backend
    pass

def log_security_event(event, **kwargs):
    """
    Log security events for audit trail
    """
    logger.warning(f"SECURITY: {event} - {kwargs}")
```

---

## Security Comparison: Shared vs Per-Customer Endpoints

| Security Aspect | Shared Endpoint | Per-Customer Endpoints |
|----------------|-----------------|------------------------|
| **Authentication Required** | ✅ Yes | ✅ Yes (SAME) |
| **Authorization Logic** | Token identifies customer | Token + URL path validation |
| **Attack Surface** | 1 endpoint | N endpoints (larger) |
| **Enumeration Risk** | None (single URL) | High (can enumerate customer IDs) |
| **Rate Limiting** | Per-token | Per-endpoint (more complex) |
| **Monitoring Complexity** | 1 dashboard | N dashboards |
| **Configuration Overhead** | 1 endpoint config | N endpoint configs |
| **URL Secret Reliance** | ❌ No | ⚠️ Tempting (dangerous!) |
| **Customer Isolation** | Token-based | Token + Path-based |
| **DDoS Impact** | All customers | Can target specific customer |

**Key Insight:** Per-customer endpoints do NOT reduce security requirements. You still need all the same authentication/authorization, PLUS additional path validation.

---

## Cost Impact of Per-Customer Endpoints

### Shared Endpoint Cost (30 customers, 300K requests/month)
```
API Gateway: $1.05/month
Lambda: $4.00/month
Total: $5.05/month
```

### Per-Customer Endpoints Cost (30 customers, 300K requests/month)
```
API Gateway: $1.05/month (same)
Lambda: $4.00/month (same)
API Gateway Usage Plans: 30 plans × $0 = $0 (free but management overhead)
CloudWatch Dashboards: 30 dashboards × $3 = $90/month
CloudWatch Alarms: 60 alarms (2 per customer) × $0.10 = $6/month

Total: $101.05/month
```

**Per-customer endpoints cost 20× more** due to monitoring overhead.

---

## When to Use Per-Customer Endpoints

### ✅ Use Per-Customer Endpoints If:
1. **Customer-specific rate limiting is critical**
   - Enterprise customer needs 10,000 req/sec
   - Small customer limited to 100 req/sec
   - Can't implement token-based rate limiting

2. **Customer-specific WAF rules required**
   - Customer A needs specific IP allowlist
   - Customer B needs different security rules
   - Can't apply rules based on authentication token

3. **Customer-specific monitoring is worth the cost**
   - Need separate CloudWatch dashboards per customer
   - Customers want their own observability portals
   - Worth $90/month extra for 30 customers

4. **Contractual requirement**
   - Customer contract specifies dedicated endpoint
   - Compliance requires URL-based isolation
   - Customer pays for premium tier with dedicated URL

### ❌ Do NOT Use Per-Customer Endpoints If:
1. **You think URL = security**
   - ❌ You still need authentication
   - ❌ URL doesn't replace auth token
   - ❌ Customer ID in URL is not secret

2. **You want to simplify authentication**
   - ❌ Per-customer endpoints are MORE complex
   - ❌ Must validate both token AND path
   - ❌ Adds authorization layer

3. **You want to save cost**
   - ❌ Per-customer endpoints cost 20× more
   - ❌ Due to monitoring overhead
   - ❌ Shared endpoint is cheaper

4. **You want to simplify operations**
   - ❌ Per-customer endpoints are harder to manage
   - ❌ N endpoints = N configurations
   - ❌ Shared endpoint is simpler

---

## Recommended Architecture

### For 99% of Use Cases: Shared Endpoint
```
All Customers → https://api.example.com/webhook
                (customer identified by OIDC token)

✅ Simpler security (no path validation)
✅ Lower cost ($5/month vs $101/month)
✅ Easier monitoring (1 dashboard)
✅ Easier rate limiting (token-based)
✅ No enumeration risk
```

### For Enterprise with Specific Requirements: Per-Customer Endpoints
```
Customer 1 → https://api.example.com/webhook/customer1
Customer 2 → https://api.example.com/webhook/customer2
             (customer identified by OIDC token + URL validation)

Requirements:
- MUST still authenticate with OIDC/mTLS
- MUST validate token matches URL path
- MUST implement per-endpoint rate limiting
- MUST monitor each endpoint separately
- MUST prevent enumeration attacks
- Worth 20× higher cost for customer-specific features
```

---

## Critical Security Checklist for Per-Customer Endpoints

### ✅ Must Have:
- [ ] OIDC token authentication OR mTLS (not API keys alone)
- [ ] Token-to-customer validation (token must match URL customer ID)
- [ ] Input validation on all messages
- [ ] Rate limiting per customer endpoint
- [ ] Generic error messages (no information leakage)
- [ ] TLS 1.2+ encryption
- [ ] Logging of all authentication failures
- [ ] Monitoring per customer endpoint
- [ ] Alerting on customer-specific issues

### ⚠️ Should Have:
- [ ] IP allowlisting per customer (optional)
- [ ] WAF rules per customer
- [ ] DDoS protection
- [ ] Message age validation (prevent replay)
- [ ] Customer-specific dashboards
- [ ] Incident response plan per customer

### ❌ Never Do:
- [ ] ❌ Trust URL path as authentication
- [ ] ❌ Reveal customer existence in error messages
- [ ] ❌ Use different status codes for valid/invalid customers
- [ ] ❌ Skip authorization check (token matching URL)
- [ ] ❌ Use API keys without IP allowlisting

---

---

## Per-Customer Endpoint Implementation Options

### Option 1: API Gateway + Path Parameters (Recommended)

#### Architecture
```
┌───────────────────────────────────────────────────────────────┐
│ AWS API Gateway                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Route: POST /webhook/{customer_id}                          │
│                                                               │
│  Customer 1 → /webhook/customer1                             │
│  Customer 2 → /webhook/customer2                             │
│  Customer 3 → /webhook/customer3                             │
│                                                               │
│  Usage Plans:                                                 │
│  ├─ customer1-plan: 1000 req/sec                            │
│  ├─ customer2-plan: 500 req/sec                             │
│  └─ customer3-plan: 2000 req/sec                            │
│                                                               │
└─────────────────┬─────────────────────────────────────────────┘
                  │
                  │ All routes → Same Lambda function
                  │ customer_id extracted from path
                  ▼
┌───────────────────────────────────────────────────────────────┐
│ Single Lambda Function                                        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  def handler(event, context):                                │
│      customer_id = event['pathParameters']['customer_id']    │
│      authenticate(customer_id)                               │
│      authorize(token, customer_id)                           │
│      process(customer_id, event['body'])                     │
│                                                               │
└─────────────────┬─────────────────────────────────────────────┘
                  │
                  ▼
            Portal26 OTEL
```

**Pros:**
- ✅ Single Lambda function handles all customers
- ✅ Easy to deploy and update
- ✅ Per-customer rate limiting via Usage Plans
- ✅ Per-customer API keys (if using API key auth)
- ✅ Lower cost (1 Lambda, N routes)

**Cons:**
- ❌ All customers share same Lambda concurrency
- ❌ One customer's spike can impact others
- ❌ Harder to monitor per-customer Lambda performance

**Cost (30 customers, 300K requests/month):**
```
API Gateway: $1.05
Lambda: $4.00
Usage Plans: $0 (free, but management overhead)
CloudWatch per-customer metrics: $90.00
Total: $95.05/month
```

---

### Option 2: API Gateway + Lambda Aliases

#### Architecture
```
┌───────────────────────────────────────────────────────────────┐
│ AWS API Gateway                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  /webhook/customer1 → Lambda:customer1 (alias)               │
│  /webhook/customer2 → Lambda:customer2 (alias)               │
│  /webhook/customer3 → Lambda:customer3 (alias)               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                  │
                  │ Each route → Different Lambda alias
                  │ (all aliases point to same function version)
                  ▼
┌───────────────────────────────────────────────────────────────┐
│ Lambda Function with Aliases                                  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  webhook:customer1 → Reserved concurrency: 100                │
│  webhook:customer2 → Reserved concurrency: 50                 │
│  webhook:customer3 → Reserved concurrency: 200                │
│                                                               │
│  Same code, different concurrency per customer                │
│                                                               │
└─────────────────┬─────────────────────────────────────────────┘
                  │
                  ▼
            Portal26 OTEL
```

**Pros:**
- ✅ Per-customer concurrency limits (isolation)
- ✅ Customer 1 spike won't affect Customer 2
- ✅ Per-customer Lambda metrics automatically
- ✅ Single function code, multiple aliases
- ✅ Easy to adjust concurrency per customer

**Cons:**
- ❌ More complex configuration (N aliases)
- ❌ Reserved concurrency costs more
- ❌ AWS account concurrency limit shared across aliases

**Cost (30 customers, 300K requests/month):**
```
API Gateway: $1.05
Lambda: $4.00
Reserved concurrency overhead: $10.00 (estimate)
CloudWatch metrics: $45.00 (reduced due to built-in per-alias metrics)
Total: $60.05/month
```

---

### Option 3: Separate Lambda Functions Per Customer

#### Architecture
```
┌───────────────────────────────────────────────────────────────┐
│ AWS API Gateway                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  /webhook/customer1 → Lambda-customer1                        │
│  /webhook/customer2 → Lambda-customer2                        │
│  /webhook/customer3 → Lambda-customer3                        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                  │
                  │ Each route → Separate Lambda function
                  │ (30 different functions)
                  ▼
┌───────────────────────────────────────────────────────────────┐
│ 30 Separate Lambda Functions                                 │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  webhook-customer1 (dedicated function)                       │
│  webhook-customer2 (dedicated function)                       │
│  webhook-customer3 (dedicated function)                       │
│  ...                                                          │
│                                                               │
│  Each function has own logs, metrics, config                  │
│                                                               │
└─────────────────┬─────────────────────────────────────────────┘
                  │
                  ▼
            Portal26 OTEL
```

**Pros:**
- ✅ Complete isolation per customer
- ✅ Per-customer configuration (env vars, timeouts, memory)
- ✅ Can deploy updates to single customer
- ✅ Easy to debug per customer
- ✅ Per-customer IAM roles
- ✅ No shared concurrency issues

**Cons:**
- ❌ Very high operational overhead (30 functions)
- ❌ 30 separate deployments
- ❌ 30 separate monitoring dashboards
- ❌ Code updates require 30 deployments
- ❌ Higher AWS costs (30 functions = 30 cold starts)
- ❌ Hits AWS Lambda function limits at ~500 customers

**Cost (30 customers, 300K requests/month):**
```
API Gateway: $1.05
Lambda invocations: 30 functions × $0.20 = $6.00
Lambda duration: 30 functions × $0.10 = $3.00
CloudWatch Logs: 30 log groups × $0.50 = $15.00
CloudWatch Dashboards: 30 × $3 = $90.00
Total: $115.05/month
```

---

### Option 4: Application Load Balancer + Path Routing

#### Architecture
```
┌───────────────────────────────────────────────────────────────┐
│ Application Load Balancer (ALB)                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Listener Rules:                                              │
│  ├─ /webhook/customer1 → Target Group 1 → Lambda             │
│  ├─ /webhook/customer2 → Target Group 2 → Lambda             │
│  └─ /webhook/customer3 → Target Group 3 → Lambda             │
│                                                               │
│  Per-rule configuration:                                      │
│  - Custom headers injection                                   │
│  - Path-based routing                                         │
│  - Health checks                                              │
│                                                               │
└─────────────────┬─────────────────────────────────────────────┘
                  │
                  ▼
        Single Lambda Function
                  │
                  ▼
            Portal26 OTEL
```

**Pros:**
- ✅ Advanced routing capabilities
- ✅ Can inject custom headers per path
- ✅ Health checks per customer endpoint
- ✅ WebSocket support (if needed)
- ✅ Fixed IP addresses (easier for customer IP allowlisting)

**Cons:**
- ❌ Expensive ($35/month fixed cost for ALB)
- ❌ More complex than API Gateway
- ❌ Harder to configure per-customer rate limiting
- ❌ Overkill for simple webhooks

**Cost (30 customers, 300K requests/month):**
```
ALB: $35.00/month fixed + $0.008/LCU
Lambda: $4.00
CloudWatch: $50.00
Total: $89.00/month
```

---

## Complete Cost Comparison Table

| Architecture | Setup Time | Monthly Cost (30 customers) | Cost per Customer | Operational Overhead | Isolation Level |
|--------------|-----------|---------------------------|------------------|---------------------|----------------|
| **Shared Endpoint + OIDC** | 2 hours | $5.05 | $0.17 | Very Low | High (token-based) |
| Per-Customer URL + Single Lambda | 4 hours | $95.05 | $3.17 | Medium | Medium (path + token) |
| Per-Customer URL + Lambda Aliases | 6 hours | $60.05 | $2.00 | Medium-High | High (concurrency isolation) |
| Per-Customer URL + Separate Lambdas | 15 hours | $115.05 | $3.84 | Very High | Maximum (complete isolation) |
| Per-Customer URL + ALB | 8 hours | $89.00 | $2.97 | High | Medium (routing isolation) |

---

## Security Comparison Matrix

| Security Feature | Shared Endpoint | Per-Customer Single Lambda | Per-Customer Aliases | Per-Customer Separate Lambdas |
|-----------------|----------------|---------------------------|---------------------|------------------------------|
| **Authentication Required** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Authorization Check** | Token only | Token + Path | Token + Path | Token + Path |
| **Enumeration Risk** | None | High | High | High |
| **Rate Limiting** | Token-based | Path-based (Usage Plan) | Alias-based (Reserved concurrency) | Function-based (Separate limits) |
| **DDoS Isolation** | Shared | Shared concurrency | Reserved concurrency | Fully isolated |
| **Customer Impersonation Risk** | Low (token verification) | Medium (token + path matching) | Medium (token + path matching) | Low (separate functions) |
| **Monitoring Complexity** | 1 dashboard | N metrics in 1 dashboard | N aliases + metrics | N dashboards |
| **Attack Surface** | 1 endpoint | N endpoints | N endpoints | N endpoints |
| **URL as Security** | ❌ No | ❌ No (still need auth) | ❌ No (still need auth) | ❌ No (still need auth) |

---

## When to Use Each Option

### Use Shared Endpoint (Recommended for 99%)
```
✅ When: Production SaaS, typical use case
✅ Cost: $5/month (30 customers)
✅ Security: High (OIDC token)
✅ Complexity: Low
✅ Scalability: 1000+ customers

Perfect for: Most SaaS applications
```

### Use Per-Customer Endpoint + Single Lambda
```
✅ When: Need customer-specific rate limits
✅ Cost: $95/month (30 customers)
✅ Security: High (OIDC + path validation)
✅ Complexity: Medium
✅ Scalability: 500-1000 customers

Perfect for: Tiered pricing with different rate limits per plan
```

### Use Per-Customer Endpoint + Lambda Aliases
```
✅ When: Need hard concurrency isolation between customers
✅ Cost: $60/month (30 customers)
✅ Security: Very High (OIDC + concurrency limits)
✅ Complexity: Medium-High
✅ Scalability: 200-500 customers

Perfect for: Enterprise customers who need guaranteed capacity
```

### Use Per-Customer Endpoint + Separate Lambdas
```
✅ When: Need complete customer isolation (compliance requirement)
✅ Cost: $115/month (30 customers)
✅ Security: Maximum (complete isolation)
✅ Complexity: Very High
✅ Scalability: 100-200 customers

Perfect for: Regulated industries (finance, healthcare) requiring air-gapped customers
```

### Use Per-Customer Endpoint + ALB
```
✅ When: Need advanced routing or WebSocket support
✅ Cost: $89/month (30 customers)
✅ Security: High (OIDC + ALB features)
✅ Complexity: High
✅ Scalability: 1000+ customers

Perfect for: Complex routing needs, WebSocket, or fixed IP requirement
```

---

## Deployment Examples

### Option 1: API Gateway + Single Lambda (Path Parameters)

**Terraform Configuration:**
```hcl
# API Gateway
resource "aws_api_gateway_rest_api" "webhook" {
  name = "customer-webhook-api"
}

resource "aws_api_gateway_resource" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  parent_id   = aws_api_gateway_rest_api.webhook.root_resource_id
  path_part   = "webhook"
}

resource "aws_api_gateway_resource" "customer_id" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  parent_id   = aws_api_gateway_resource.webhook.id
  path_part   = "{customer_id}"
}

resource "aws_api_gateway_method" "post" {
  rest_api_id   = aws_api_gateway_rest_api.webhook.id
  resource_id   = aws_api_gateway_resource.customer_id.id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.oidc.id
}

# Lambda Authorizer
resource "aws_api_gateway_authorizer" "oidc" {
  name                   = "oidc-authorizer"
  rest_api_id           = aws_api_gateway_rest_api.webhook.id
  authorizer_uri        = aws_lambda_function.authorizer.invoke_arn
  authorizer_credentials = aws_iam_role.authorizer.arn
  type                  = "REQUEST"
  identity_source       = "method.request.header.Authorization"
}

# Main Lambda
resource "aws_lambda_function" "webhook" {
  function_name = "customer-webhook-handler"
  role         = aws_iam_role.lambda.arn
  handler      = "index.handler"
  runtime      = "python3.11"
  
  environment {
    variables = {
      PORTAL26_ENDPOINT = "https://otel-tenant1.portal26.in:4318"
    }
  }
}

# Per-Customer Usage Plans (Rate Limiting)
resource "aws_api_gateway_usage_plan" "customer1" {
  name = "customer1-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.webhook.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }

  throttle_settings {
    rate_limit  = 1000  # requests per second
    burst_limit = 2000
  }
}

# Repeat for each customer...
```

**Lambda Handler:**
```python
import json
import base64
import requests

def handler(event, context):
    """
    Handle per-customer webhook requests
    """
    # Extract customer_id from path
    customer_id = event['pathParameters']['customer_id']
    
    # Extract authenticated customer from authorizer context
    authenticated_customer = event['requestContext']['authorizer']['customer_id']
    
    # Authorization: verify token matches URL
    if authenticated_customer != customer_id:
        return {
            'statusCode': 403,
            'body': json.dumps({'status': 'error'})
        }
    
    # Parse Pub/Sub message
    body = json.loads(event['body'])
    message_data = base64.b64decode(body['message']['data'])
    log_entry = json.loads(message_data)
    
    # Convert to OTEL format
    otel_log = convert_to_otel(log_entry, customer_id)
    
    # Send to Portal26
    success = send_to_portal26(otel_log, customer_id)
    
    return {
        'statusCode': 200 if success else 500,
        'body': json.dumps({'status': 'success' if success else 'error'})
    }
```

---

### Option 2: Lambda Aliases with Reserved Concurrency

**Terraform Configuration:**
```hcl
# Main Lambda Function
resource "aws_lambda_function" "webhook" {
  function_name = "customer-webhook-handler"
  role         = aws_iam_role.lambda.arn
  handler      = "index.handler"
  runtime      = "python3.11"
}

# Customer 1 Alias with Reserved Concurrency
resource "aws_lambda_alias" "customer1" {
  name             = "customer1"
  function_name    = aws_lambda_function.webhook.arn
  function_version = aws_lambda_function.webhook.version
}

resource "aws_lambda_function_concurrency" "customer1" {
  function_name      = aws_lambda_function.webhook.function_name
  reserved_concurrent_executions = 100  # Guaranteed capacity
}

# API Gateway routes to aliases
resource "aws_api_gateway_integration" "customer1" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  resource_id = aws_api_gateway_resource.customer1.id
  http_method = aws_api_gateway_method.customer1.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = "${aws_lambda_alias.customer1.invoke_arn}"
}

# Repeat for each customer with different concurrency limits...
```

**Benefits:**
- Customer 1 spike (100 concurrent requests) won't affect Customer 2
- Each alias gets dedicated CloudWatch metrics
- Same code, different capacity per customer

---

## Monitoring & Observability

### Shared Endpoint Monitoring (Simple)
```yaml
CloudWatch Dashboard: Single dashboard
Metrics:
  - TotalRequests
  - ErrorRate
  - Latency
  - By customer_id dimension

Cost: $3/month for 1 dashboard
```

### Per-Customer Endpoint Monitoring (Complex)
```yaml
CloudWatch Dashboards: 30 separate dashboards (1 per customer)
Metrics per customer:
  - customer1/Requests
  - customer1/Errors
  - customer1/Latency
  - customer1/ThrottledRequests
  
Alarms per customer:
  - customer1-high-error-rate
  - customer1-high-latency

Cost: $90/month for 30 dashboards + $6/month for 60 alarms
```

---

## Migration Path

### If You Start with Shared Endpoint:
```
Step 1: Deploy shared endpoint (/webhook) with OIDC
  - Cost: $5/month
  - Time: 2 hours
  - Customers: All use /webhook

Step 2: (If needed) Add per-customer rate limiting
  - Add API Gateway Usage Plans
  - Cost: +$0 (free feature)
  - Time: 30 minutes
  - Customers: Still use /webhook

Step 3: (If needed) Migrate to per-customer endpoints
  - Add /webhook/{customer_id} routes
  - Redirect customers gradually
  - Cost: +$90/month (monitoring)
  - Time: 4 hours setup + customer migration time
```

### If You Start with Per-Customer Endpoints:
```
Step 1: Deploy per-customer endpoints
  - Cost: $95/month
  - Time: 4 hours
  - Customers: Each uses /webhook/customer_id

Step 2: (Hard to migrate back) Consolidate to shared
  - Must coordinate with all customers
  - Update all Pub/Sub push subscriptions
  - Risk of downtime during migration
  - Time: Days to weeks
```

**Recommendation:** Start with shared endpoint. Add per-customer endpoints only if specific requirement emerges.

---

## Summary

### Key Takeaways:

1. **URL ≠ Security**
   - Per-customer endpoints still require full authentication
   - URL path is public information, not a secret
   - Must validate token matches URL customer ID

2. **More Complex, Not Simpler**
   - Per-customer endpoints add authorization layer
   - Must validate both token AND path
   - Larger attack surface (enumeration risk)

3. **Higher Cost**
   - 18× more expensive due to monitoring overhead
   - $5/month shared vs $95/month per-customer (30 customers)
   - Each customer needs separate metrics, possibly dashboards

4. **Authentication Still Required**
   - ✅ OIDC Token (recommended)
   - ✅ mTLS (for maximum security)
   - ⚠️ API Key (only with IP allowlisting)
   - ❌ No authentication (NEVER)

5. **Operational Overhead**
   - Shared: 1 deployment, 1 dashboard, 1 code path
   - Per-customer: N configurations, N metrics, N potential issues

### Final Recommendation:

| Use Case | Recommendation | Monthly Cost | Complexity |
|----------|---------------|--------------|------------|
| **Typical SaaS (99%)** | Shared endpoint + OIDC | $5 | Low |
| Need tiered rate limits | Per-customer + Single Lambda | $95 | Medium |
| Need concurrency isolation | Per-customer + Lambda Aliases | $60 | Medium-High |
| Compliance requires complete isolation | Per-customer + Separate Lambdas | $115 | Very High |

**Start with shared endpoint. Only add per-customer endpoints if specific business requirement justifies 18× cost increase and operational complexity.**
