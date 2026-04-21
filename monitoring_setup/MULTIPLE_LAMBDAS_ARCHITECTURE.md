# Multiple Lambda Architecture - Complete Guide

## What "Multiple Lambdas" Means

There are several ways to implement multiple Lambda functions:

### Architecture 1: One Lambda Per Customer
```
Customer 1 → Lambda-customer1 → Portal26
Customer 2 → Lambda-customer2 → Portal26
Customer 3 → Lambda-customer3 → Portal26
```

### Architecture 2: Separate Authorizer + Handler Lambdas
```
All Customers → Lambda-Authorizer (validates token) → Lambda-Handler (processes message) → Portal26
```

### Architecture 3: One Lambda Per Region/Environment
```
US Customers → Lambda-US → Portal26
EU Customers → Lambda-EU → Portal26
APAC Customers → Lambda-APAC → Portal26
```

### Architecture 4: Functional Separation (Microservices)
```
All Customers → Lambda-Receiver → SQS → Lambda-Processor → Lambda-Forwarder → Portal26
```

Let me cover all options in detail.

---

## Architecture 1: One Lambda Per Customer

### Overview
```
┌─────────────────────────────────────────────────────────────────┐
│ API Gateway                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST /webhook/customer1 → Lambda-customer1                    │
│  POST /webhook/customer2 → Lambda-customer2                    │
│  POST /webhook/customer3 → Lambda-customer3                    │
│  ...                                                            │
│  POST /webhook/customer30 → Lambda-customer30                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                     │
                     │ 30 separate Lambda functions
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda Functions (One Per Customer)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  webhook-customer1:                                             │
│    - Memory: 512MB                                              │
│    - Timeout: 60s                                               │
│    - Env: CUSTOMER_ID=customer1                                 │
│    - Concurrency: Unlimited                                     │
│    - IAM Role: customer1-lambda-role                            │
│                                                                 │
│  webhook-customer2:                                             │
│    - Memory: 256MB (smaller customer)                           │
│    - Timeout: 60s                                               │
│    - Env: CUSTOMER_ID=customer2                                 │
│    - Concurrency: Reserved 50                                   │
│    - IAM Role: customer2-lambda-role                            │
│                                                                 │
│  webhook-customer3:                                             │
│    - Memory: 1024MB (enterprise customer)                       │
│    - Timeout: 120s                                              │
│    - Env: CUSTOMER_ID=customer3, PORTAL26_ENDPOINT=custom       │
│    - Concurrency: Reserved 200                                  │
│    - IAM Role: customer3-lambda-role                            │
│                                                                 │
│  ... (27 more functions)                                        │
│                                                                 │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
            Portal26 OTEL
```



#### Do You Still Need Authentication?

**Option A: No Authentication (Lambda = Identity)**
```
Since each customer has dedicated Lambda:
- API Gateway route /webhook/customer1 → Lambda-customer1
- Customer1 cannot call Lambda-customer2 (different endpoint)
- Lambda function itself is the identity

Security relies on:
✅ API Gateway path-based routing
✅ AWS IAM (who can invoke which Lambda)
⚠️ Anyone with the URL can send to that customer's endpoint

Acceptable when:
- API Gateway has IP allowlisting per route
- URL is kept secret (not published)
- Low security requirements
```

**Option B: OIDC Authentication (Defense in Depth)**
```
Even with dedicated Lambda, still validate OIDC token:
- Prevents unauthorized parties from sending fake data
- Validates requests actually come from customer's GCP
- Provides audit trail (token includes timestamp, issuer)

Required when:
- Production SaaS with external customers
- Compliance requirements
- Customer data is sensitive
- Need proof of origin
```

**Recommendation:**
- **Low/Medium Security:** No authentication (Lambda = identity) + IP allowlisting
- **High Security:** OIDC authentication + Lambda isolation (defense in depth)

### Cost Analysis

**Monthly Cost (30 customers, 300K requests/month = 10K per customer):**

| Service | Calculation | Cost |
|---------|-------------|------|
| API Gateway | 300K requests × $3.50/million | $1.05 |
| Lambda Invocations | 300K × $0.20/million | $0.06 |
| Lambda Duration | 30 functions × (10K req × 500ms × $0.0000000167/ms) | $2.50 |
| Lambda Memory | 30 functions × (10K × 512MB × 500ms × $0.0000000167) | $2.50 |
| CloudWatch Logs | 30 log groups × $0.50 | $15.00 |
| CloudWatch Metrics | 30 functions × custom metrics | $30.00 |
| CloudWatch Dashboards | 30 dashboards × $3 | $90.00 |
| **TOTAL** | | **$141.11/month** |

**Cost per Customer:** $4.70/month

**Cost Breakdown by Customer Size:**

| Customer Tier | Requests/Month | Memory | Lambda Cost | Total Cost/Month |
|---------------|----------------|--------|-------------|------------------|
| Small (Tier 1) | 5K | 256MB | $0.50 | $3.50 |
| Medium (Tier 2) | 10K | 512MB | $1.00 | $4.70 |
| Large (Tier 3) | 50K | 1024MB | $8.00 | $11.00 |
| Enterprise (Tier 4) | 100K | 2048MB | $20.00 | $23.00 |

**Cost Scaling:**

| Customers | Total Requests/Month | Monthly Cost | Cost per Customer |
|-----------|---------------------|--------------|-------------------|
| 10 | 100K | $50.00 | $5.00 |
| 30 | 300K | $141.11 | $4.70 |
| 50 | 500K | $230.00 | $4.60 |
| 100 | 1M | $450.00 | $4.50 |
| 200 | 2M | $890.00 | $4.45 |

**Cost compared to alternatives:**

| Architecture | 30 Customers Cost | Cost per Customer |
|--------------|-------------------|-------------------|
| Shared endpoint + Single Lambda | $5.05 | $0.17 |
| Per-customer endpoint + Single Lambda | $95.05 | $3.17 |
| **One Lambda per customer** | **$141.11** | **$4.70** |
| Per-customer containers (ECS) | $200.00 | $6.67 |

**Cost Analysis:**
- ✅ **28× more expensive than shared Lambda** ($141 vs $5)
- ❌ **$4.70 per customer** vs $0.17 shared
- ⚠️ **Worth it IF** complete isolation is required (compliance, enterprise)
- ⚠️ **CloudWatch monitoring is 85% of cost** ($135 out of $141)



## Architecture 2: Separate Authorizer + Handler Lambdas

### Overview
```
┌─────────────────────────────────────────────────────────────────┐
│ All Customer Requests                                           │
│ (Customer 1, 2, 3, ..., 30)                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ API Gateway                                                     │
│ POST /webhook                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda Authorizer (Authentication & Authorization)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: Authorization header (OIDC token)                       │
│                                                                 │
│  Process:                                                       │
│  1. Extract JWT from Authorization header                      │
│  2. Verify JWT signature using Google public keys              │
│  3. Validate claims (iss, aud, exp)                            │
│  4. Check service account in allowlist                         │
│  5. Map service account → customer_id                          │
│                                                                 │
│  Output: IAM policy (Allow/Deny) + customer context            │
│  {                                                              │
│    "principalId": "customer1",                                  │
│    "policyDocument": {...},                                     │
│    "context": {                                                 │
│      "customer_id": "customer1",                                │
│      "service_account": "customer1@project.iam.gserviceaccount.com" │
│    }                                                            │
│  }                                                              │
│                                                                 │
│  Invocations: 300K/month (one per request)                     │
│  Avg Duration: 150ms (includes Google JWKS fetch)              │
│  Memory: 512MB                                                  │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ If Allow: Pass request + context to Handler
                     │ If Deny: Return 403 Forbidden
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda Handler (Business Logic)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input:                                                         │
│  - Request body (Pub/Sub message)                              │
│  - Authorizer context (customer_id, service_account)           │
│                                                                 │
│  Process:                                                       │
│  1. Extract customer_id from authorizer context                │
│  2. Decode Pub/Sub message (base64)                            │
│  3. Parse log entry (JSON)                                     │
│  4. Validate log structure                                     │
│  5. Convert to OTEL format                                     │
│  6. Add customer.id attribute                                  │
│  7. Send to Portal26                                           │
│                                                                 │
│  Output: HTTP 200/500 response                                 │
│                                                                 │
│  Invocations: 300K/month (only if authorized)                  │
│  Avg Duration: 500ms                                            │
│  Memory: 512MB                                                  │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
               Portal26 OTEL
```

### Why Separate Authorizer and Handler?

**Benefits of Separation:**

1. **Caching** - Authorizer results cached by API Gateway (5 min TTL)
   ```
   Request 1: Authorizer runs (150ms) → Handler runs (500ms) = 650ms
   Request 2: Authorizer cached (0ms) → Handler runs (500ms) = 500ms
   Request 3: Authorizer cached (0ms) → Handler runs (500ms) = 500ms
   ...
   Request 50: Authorizer cached (0ms) → Handler runs (500ms) = 500ms
   
   Savings: 49 authorizer invocations avoided = ~$0.02 saved per 50 requests
   ```

2. **Security isolation** - Authentication logic separate from business logic
   ```
   Authorizer Lambda:
   - Only has permissions to read JWKS
   - Cannot access secrets, databases, Portal26
   - Blast radius limited to authentication
   
   Handler Lambda:
   - Only has permissions to send to Portal26
   - Cannot modify authentication logic
   - Blast radius limited to message processing
   ```

3. **Independent scaling** - Authorizer and Handler can scale independently
   ```
   Scenario: Lots of invalid auth attempts (DDoS)
   - Authorizer scales up to handle load
   - Handler doesn't scale (unauthorized requests blocked)
   - Cost savings (Handler not invoked for unauthorized requests)
   ```

4. **Easier testing** - Can test authentication separately from business logic
   ```
   Test authorizer:
   - Mock Google JWKS endpoint
   - Test valid/invalid/expired tokens
   - No need to test message processing
   
   Test handler:
   - Mock authorizer context
   - Test message parsing, OTEL conversion
   - No need to test authentication
   ```

5. **Reusability** - Authorizer can be used by other APIs
   ```
   Authorizer validates OIDC tokens
   
   Can be reused for:
   - Webhook API (/webhook)
   - Status API (/status)
   - Config API (/config)
   - All use same authentication logic
   ```

### Cost Analysis

**Monthly Cost (30 customers, 300K requests/month):**

| Service | Calculation | Cost |
|---------|-------------|------|
| API Gateway | 300K requests × $3.50/million | $1.05 |
| Lambda Authorizer Invocations | 60K invocations × $0.20/million (80% cached) | $0.01 |
| Lambda Authorizer Duration | 60K × 150ms × $0.0000000167/ms | $0.15 |
| Lambda Authorizer Memory | 60K × 512MB × 150ms × $0.0000000167 | $0.15 |
| Lambda Handler Invocations | 300K × $0.20/million | $0.06 |
| Lambda Handler Duration | 300K × 500ms × $0.0000000167/ms | $2.50 |
| Lambda Handler Memory | 300K × 512MB × 500ms × $0.0000000167 | $2.50 |
| CloudWatch Logs | 2 log groups × $0.50 | $1.00 |
| CloudWatch Metrics | Minimal custom metrics | $2.00 |
| **TOTAL** | | **$9.42/month** |

**Cost per Customer:** $0.31/month

**Cost Comparison:**

| Architecture | Monthly Cost | Cost per Customer | Authorizer Caching |
|--------------|--------------|-------------------|--------------------|
| Single Lambda (no authorizer) | $5.05 | $0.17 | N/A |
| **Authorizer + Handler** | **$9.42** | **$0.31** | ✅ Yes (80% hit rate) |
| One Lambda per customer | $141.11 | $4.70 | N/A |

**Cost Analysis:**
- ⚠️ **1.9× more expensive than single Lambda** ($9.42 vs $5.05)
- ✅ **15× cheaper than per-customer Lambdas** ($9.42 vs $141)
- ✅ **Caching saves ~$1.50/month** (80% of auth invocations avoided)
- ✅ **Better security architecture** worth $4.37/month extra

### Caching Benefits

**Without Caching (Every request runs authorizer):**
```
300K requests/month
× 150ms authorizer duration
× $0.0000000167/ms
= $0.75 authorizer cost

Total: $5.05 + $0.75 = $5.80/month
```

**With Caching (80% hit rate, 5 min TTL):**
```
60K authorizer invocations (20% of requests)
× 150ms authorizer duration
× $0.0000000167/ms
= $0.15 authorizer cost

Cached: 240K requests (80%) = $0 cost

Total: $5.05 + $0.15 = $5.20/month

Savings: $0.60/month (10% reduction)
```

**How Caching Works:**
```
API Gateway caches authorizer response for 5 minutes (300 seconds)

Request 1 (00:00): customer1 → Authorizer runs → Cached for 5 min
Request 2 (00:01): customer1 → Cache hit → No authorizer invocation
Request 3 (00:02): customer1 → Cache hit → No authorizer invocation
...
Request 50 (00:04): customer1 → Cache hit → No authorizer invocation
Request 51 (00:06): customer1 → Cache expired → Authorizer runs → Re-cached

Cache key: Authorization header value
- Same token = cache hit
- Different token = cache miss (new customer or rotated token)
```

---

## Architecture 3: Lambda Per Region/Environment

### Overview
```
┌─────────────────────────────────────────────────────────────────┐
│ Customer Requests (Geo-distributed)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  US Customers (1-10) → us-east-1                               │
│  EU Customers (11-20) → eu-west-1                              │
│  APAC Customers (21-30) → ap-southeast-1                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Lambda-US        │  │ Lambda-EU        │  │ Lambda-APAC      │
│ (us-east-1)      │  │ (eu-west-1)      │  │ (ap-southeast-1) │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ - 10 customers   │  │ - 10 customers   │  │ - 10 customers   │
│ - 100K req/month │  │ - 100K req/month │  │ - 100K req/month │
│ - Latency: ~50ms │  │ - Latency: ~100ms│  │ - Latency: ~150ms│
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
                        Portal26 OTEL
                   (or regional Portal26 instances)
```

### Why Regional Lambdas?

1. **Latency** - Deploy Lambda closer to customers
2. **Compliance** - Data residency requirements (GDPR, regional laws)
3. **Availability** - Multi-region redundancy
4. **Cost** - Reduce data transfer costs

### Cost Analysis

**Monthly Cost (30 customers, 300K requests, 3 regions):**

| Service | US Region | EU Region | APAC Region | Total |
|---------|-----------|-----------|-------------|-------|
| API Gateway | $0.35 | $0.35 | $0.35 | $1.05 |
| Lambda | $1.67 | $1.67 | $1.67 | $5.01 |
| CloudWatch | $1.00 | $1.00 | $1.00 | $3.00 |
| **Regional Total** | **$3.02** | **$3.02** | **$3.02** | **$9.06** |

**Cost per Customer:** $0.30/month

**Cost Comparison:**

| Architecture | Monthly Cost | Cost per Customer | Regions |
|--------------|--------------|-------------------|---------|
| Single Lambda (us-east-1) | $5.05 | $0.17 | 1 |
| **3 Regional Lambdas** | **$9.06** | **$0.30** | 3 |
| Per-customer Lambdas | $141.11 | $4.70 | 1 |

**Cost Analysis:**
- ⚠️ **1.8× more expensive than single region** ($9.06 vs $5.05)
- ✅ **Adds redundancy** - Multi-region availability
- ✅ **Reduces latency** - Customers connect to closest region
- ✅ **Meets compliance** - Data stays in region

### Latency Benefits

**Single Region (us-east-1):**
```
US customer → us-east-1 Lambda: ~50ms
EU customer → us-east-1 Lambda: ~150ms (transatlantic)
APAC customer → us-east-1 Lambda: ~250ms (transpacific)

Average latency: ~150ms
```

**Multi-Region:**
```
US customer → us-east-1 Lambda: ~50ms
EU customer → eu-west-1 Lambda: ~50ms
APAC customer → ap-southeast-1 Lambda: ~50ms

Average latency: ~50ms (3× improvement)
```

---

## Architecture 4: Microservices (Receiver → Processor → Forwarder)

### Overview
```
┌───────────────────────────────────────────────────────────────┐
│ All Customer Requests                                         │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda 1: Receiver (Fast, Async)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Responsibilities:                                              │
│  1. Authenticate OIDC token (100ms)                            │
│  2. Basic validation (message structure)                       │
│  3. Push message to SQS queue                                  │
│  4. Return 200 OK immediately                                  │
│                                                                 │
│  Duration: ~150ms                                               │
│  Memory: 256MB (lightweight)                                    │
│                                                                 │
│  Benefits:                                                      │
│  - Fast response to customer (150ms vs 650ms)                  │
│  - Decouples reception from processing                         │
│  - No timeout risk (returns before processing)                 │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ SQS Message
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ SQS Queue (Buffer)                                              │
├─────────────────────────────────────────────────────────────────┤
│  - Retries: 3 attempts                                          │
│  - Visibility timeout: 5 minutes                                │
│  - DLQ: After 3 failures → Dead Letter Queue                   │
│  - Batching: Process 10 messages at once                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Batch of 10 messages
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda 2: Processor (Heavy Lifting)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Responsibilities:                                              │
│  1. Decode Pub/Sub messages                                    │
│  2. Parse log entries                                          │
│  3. Convert to OTEL format                                     │
│  4. Enrich with customer metadata                              │
│  5. Push to output queue                                       │
│                                                                 │
│  Duration: ~500ms per batch (10 messages)                      │
│  Memory: 512MB                                                  │
│                                                                 │
│  Benefits:                                                      │
│  - Batch processing (efficient)                                │
│  - Can retry failures independently                            │
│  - Scalable (processes 30 messages in parallel)                │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Processed OTEL logs
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ SQS Queue (Output Buffer)                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Batch of processed logs
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda 3: Forwarder (Portal26 Integration)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Responsibilities:                                              │
│  1. Batch OTEL logs (up to 100)                                │
│  2. Build Portal26 payload                                     │
│  3. Send to Portal26 API                                       │
│  4. Handle Portal26 errors/retries                             │
│                                                                 │
│  Duration: ~300ms per batch                                     │
│  Memory: 512MB                                                  │
│                                                                 │
│  Benefits:                                                      │
│  - Isolates Portal26 integration                               │
│  - Can retry Portal26 failures without re-processing           │
│  - Can batch efficiently (100 logs per API call)               │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
               Portal26 OTEL
```

### Why Microservices Architecture?

1. **Decoupling** - Reception, processing, forwarding independent
2. **Resilience** - Failure in one stage doesn't affect others
3. **Scalability** - Each Lambda scales independently
4. **Performance** - Fast response to customer (150ms vs 650ms)
5. **Retries** - Can retry processing without re-receiving message
6. **Batch efficiency** - Processor and Forwarder can batch messages

### Cost Analysis

**Monthly Cost (30 customers, 300K requests/month):**

| Service | Calculation | Cost |
|---------|-------------|------|
| API Gateway | 300K requests × $3.50/million | $1.05 |
| Lambda Receiver | 300K × 150ms × $0.0000000167/ms (256MB) | $0.75 |
| SQS Input Queue | 300K messages × $0.40/million | $0.12 |
| Lambda Processor | 30K batches × 500ms × $0.0000000167/ms (512MB) | $0.25 |
| SQS Output Queue | 300K messages × $0.40/million | $0.12 |
| Lambda Forwarder | 3K batches × 300ms × $0.0000000167/ms (512MB) | $0.02 |
| CloudWatch Logs | 3 log groups × $0.50 | $1.50 |
| CloudWatch Metrics | Minimal | $2.00 |
| **TOTAL** | | **$5.81/month** |

**Cost per Customer:** $0.19/month

**Cost Comparison:**

| Architecture | Monthly Cost | Cost per Customer | Complexity |
|--------------|--------------|-------------------|------------|
| Single Lambda | $5.05 | $0.17 | Low |
| **Microservices (3 Lambdas + SQS)** | **$5.81** | **$0.19** | Medium |
| Authorizer + Handler | $9.42 | $0.31 | Medium |
| Per-customer Lambdas | $141.11 | $4.70 | Very High |

**Cost Analysis:**
- ⚠️ **15% more expensive than single Lambda** ($5.81 vs $5.05)
- ✅ **But better resilience, scalability, performance**
- ✅ **Worth $0.76/month for production systems**

### Performance Benefits

**Single Lambda (Synchronous):**
```
Customer request → Lambda (auth + process + forward) → Response
Total time: 650ms (150ms auth + 200ms process + 300ms forward)

If Portal26 is slow (2s response):
Total time: 2.3s (customer waits 2.3 seconds!)
```

**Microservices (Async):**
```
Customer request → Receiver Lambda → SQS → Response
Total time: 150ms (customer waits only 150ms)

Background:
- Processor picks from SQS in parallel
- Forwarder sends to Portal26 in parallel
- Customer already got 200 OK

If Portal26 is slow (2s response):
Customer doesn't care! Already got 200 OK.
```

**Latency Comparison:**
- Single Lambda: 650ms (synchronous)
- Microservices: 150ms (async response) = **4.3× faster**

### Resilience Benefits

**Single Lambda Failure Scenarios:**

```
Scenario 1: Portal26 is down
- Customer request → Lambda tries to forward → Portal26 timeout
- Lambda returns 500 error
- Message LOST (no retry)

Scenario 2: Lambda crashes during processing
- Customer request → Lambda processes → Crash
- Message LOST (no retry)
```

**Microservices Failure Scenarios:**

```
Scenario 1: Portal26 is down
- Receiver → SQS → Processor → Output SQS → Forwarder → Portal26 timeout
- Forwarder fails, message returns to SQS
- SQS retries Forwarder after visibility timeout
- Customer already got 200 OK (doesn't know/care)
- Message eventually succeeds or goes to DLQ

Scenario 2: Processor crashes
- Receiver → SQS → Processor crashes
- Message returns to SQS after visibility timeout
- SQS retries (up to 3 times)
- Customer already got 200 OK
- Message eventually succeeds or goes to DLQ

Scenario 3: Receiver fails
- Customer request → Receiver crashes
- Customer gets 500 error (expected, can retry)
- Message not in SQS yet (no data loss, customer retries)
```

**Key Difference:**
- Single Lambda: Customer waits for entire pipeline, failure = customer sees error
- Microservices: Customer only waits for receiver, failures handled async

---

## Complete Comparison Table

| Architecture | Monthly Cost (30 cust) | Cost/Customer | Complexity | Security | Scalability | Use Case |
|--------------|------------------------|---------------|------------|----------|-------------|----------|
| **Single Lambda** | $5.05 | $0.17 | Low | High | High | ✅ **Recommended for most** |
| **Microservices** | $5.81 | $0.19 | Medium | High | Very High | Production SaaS |
| **Authorizer + Handler** | $9.42 | $0.31 | Medium | Very High | High | Multiple APIs, security focus |
| **Regional Lambdas** | $9.06 | $0.30 | Medium | High | Very High | Global customers, GDPR |
| **One Lambda/Customer** | $141.11 | $4.70 | Very High | Maximum | Medium | Enterprise, compliance |

---


---

## Summary

**For Multiple Lambdas, Best Approach:**

1. **Authorizer + Handler (Recommended Starting Point)**
   - Cost: $9.42/month
   - Complexity: Medium
   - Benefits: Best practices, caching, security isolation

2. **Add Microservices for Production**
   - Cost: +$0.76/month
   - Benefits: Fast response, resilience, batching

3. **Add Regions for Global Scale**
   - Cost: × 1.8 per region
   - Benefits: Low latency, compliance, redundancy

4. **Add Per-Customer Lambdas ONLY for Enterprise**
   - Cost: +$4.70 per enterprise customer
   - Benefits: Complete isolation, custom config

**Total Cost for Production Multi-Region SaaS:**
```
Authorizer + Handler: $9.42
+ Microservices: $5.81
+ 3 Regions: × 3
+ 5 Enterprise customers with dedicated Lambdas: +$23.50

= ~$50-60/month for 30 customers
= $1.67-2.00 per customer/month

Still 3× cheaper than per-customer containers ($200/month)
```

This architecture scales to 1000s of customers without major changes!