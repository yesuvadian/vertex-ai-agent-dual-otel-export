# Architecture 1: One Lambda Per Customer

## Overview

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

## Key Characteristics

- ✅ **Complete Isolation**: Each customer has dedicated Lambda function
- ✅ **Independent Configuration**: Different memory, timeout, env vars per customer
- ✅ **Per-Customer IAM Roles**: Fine-grained security policies
- ✅ **Reserved Concurrency**: Guaranteed capacity per customer
- ✅ **Separate Monitoring**: Dedicated CloudWatch logs per customer
- ✅ **Blast Radius Containment**: Bug in customer1 only affects customer1

---

## API Gateway Options

### Option 1: Single API Gateway (Recommended)

```
┌─────────────────────────────────────────────────────────────────┐
│ Single API Gateway                                              │
│ https://api.example.com                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Routes:                                                        │
│  POST /webhook/customer1 → Lambda-customer1                    │
│  POST /webhook/customer2 → Lambda-customer2                    │
│  POST /webhook/customer3 → Lambda-customer3                    │
│  POST /webhook/customer4 → Lambda-customer4                    │
│  ... (30 routes)                                               │
│                                                                 │
│  Configuration:                                                 │
│  - 30 API Gateway resources                                    │
│  - 30 API Gateway methods                                      │
│  - 30 Lambda integrations                                      │
│  - 1 domain name (api.example.com)                            │
│  - 1 SSL certificate                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Cost (30 customers, 300K requests/month):**

| Service | Calculation | Cost |
|---------|-------------|------|
| API Gateway | 300K requests × $3.50/million | $1.05 |
| Custom Domain | 1 domain | $0.00 |
| SSL Certificate (ACM) | 1 cert | $0.00 |
| **TOTAL** | | **$1.05/month** |

**Pros:**
- ✅ **Lowest cost** - Single API Gateway ($1.05/month)
- ✅ **Simple management** - One API to configure/monitor
- ✅ **Single SSL certificate** - One domain, one cert
- ✅ **Easy deployment** - Add route = add customer
- ✅ **Shared rate limiting** - Can set global limits
- ✅ **Single dashboard** - One API Gateway dashboard

**Cons:**
- ❌ **Shared domain** - All customers use api.example.com
- ❌ **No customer-specific domains** - Can't give customer1.api.example.com
- ❌ **Shared rate limits** - Hard to do per-customer without Usage Plans

**When to Use:**
- Standard SaaS with all customers using same domain
- Cost is important
- Simple operations preferred
- **Recommended for 99% of use cases**

#### Security Architecture for Single API Gateway

**Security Model:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Customer 1 (GCP Pub/Sub)                                        │
│ Service Account: customer1@project.iam.gserviceaccount.com     │
└────────────┬────────────────────────────────────────────────────┘
             │ HTTPS POST + OIDC Token
             │ Authorization: Bearer eyJhbGc...
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Single API Gateway (api.example.com)                           │
│                                                                 │
│ Security Layer 1: Network                                      │
│ ├─ TLS 1.2+ encryption                                         │
│ ├─ WAF rules (optional)                                        │
│ └─ IP allowlisting per route (optional)                        │
│                                                                 │
│ Security Layer 2: Lambda Authorizer (OIDC)                    │
│ ├─ Extracts JWT from Authorization header                     │
│ ├─ Verifies JWT signature (Google's public keys)              │
│ ├─ Validates claims (iss, aud, exp)                           │
│ ├─ Checks service account in allowlist                        │
│ ├─ Maps service account → customer_id                         │
│ └─ Returns: Allow/Deny + customer context                     │
│                                                                 │
│ Security Layer 3: Route-Based Authorization                    │
│ ├─ Validates customer_id matches route                        │
│ ├─ Ensures customer1 token can only access /webhook/customer1 │
│ └─ Returns 403 if mismatch                                    │
│                                                                 │
└────────────┬────────────────────────────────────────────────────┘
             │ If authorized
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda-customer1                                                │
│ ├─ Receives validated customer_id from authorizer             │
│ ├─ Processes message                                           │
│ └─ Forwards to Portal26                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Security Layers:**

1. **Network Security**
   - TLS 1.2+ encryption for all requests
   - API Gateway SSL certificate (ACM)
   - Optional: WAF rules to block common attacks
   - Optional: IP allowlisting per route

2. **Authentication (OIDC Token)**
   - Customer's GCP Pub/Sub sends OIDC token
   - Lambda Authorizer validates token cryptographically
   - Token signed by Google (cannot be forged)
   - Token auto-rotates every 1 hour

3. **Authorization (Route Validation)**
   - Authorizer extracts customer_id from token
   - Validates customer_id matches URL route
   - Example: customer1 token can only access /webhook/customer1
   - Prevents customer1 from accessing customer2's endpoint

4. **Lambda Isolation**
   - Even after authorization, each customer invokes separate Lambda
   - Lambda-customer1 cannot access Lambda-customer2
   - IAM policies enforce Lambda-level isolation

**Security Flow Example:**

```
Request 1: Customer 1 sends to /webhook/customer1
├─ Token: customer1@project.iam.gserviceaccount.com
├─ Authorizer validates: ✅ Valid token
├─ Authorizer checks: ✅ customer1 = customer1 (route matches)
├─ Result: ✅ Allowed → Lambda-customer1
└─ Status: 200 OK

Request 2: Customer 1 tries to send to /webhook/customer2
├─ Token: customer1@project.iam.gserviceaccount.com
├─ Authorizer validates: ✅ Valid token
├─ Authorizer checks: ❌ customer1 ≠ customer2 (route mismatch)
├─ Result: ❌ Denied
└─ Status: 403 Forbidden
```

**Attack Vector Analysis:**

| Attack | Mitigation | Effectiveness |
|--------|-----------|---------------|
| **Token Forgery** | JWT signature verification using Google's public keys | ⭐⭐⭐⭐⭐ Cannot forge without Google's private key |
| **Token Replay** | Short token expiry (1 hour) + timestamp validation | ⭐⭐⭐⭐⭐ Old tokens rejected automatically |
| **Customer Impersonation** | Service account allowlist + route validation | ⭐⭐⭐⭐⭐ Customer1 cannot access customer2's route |
| **DDoS Attack** | API Gateway rate limiting + Usage Plans | ⭐⭐⭐⭐☆ Per-customer throttles prevent abuse |
| **Man-in-the-Middle** | TLS 1.2+ encryption | ⭐⭐⭐⭐⭐ All traffic encrypted |
| **Endpoint Enumeration** | Generic error responses | ⭐⭐⭐⭐☆ Don't leak customer existence |
| **Credential Leakage** | No long-lived credentials (OIDC auto-rotates) | ⭐⭐⭐⭐⭐ Tokens expire in 1 hour |

**Security Best Practices:**

1. **Enable OIDC Authentication (Required)**
   - Do NOT rely on URL path alone
   - Always validate OIDC token
   - Cost: +$1.50/month for authorizer

2. **Implement Route Validation (Required)**
   - Authorizer must check token matches route
   - Prevents cross-customer access
   - Zero cost (part of authorizer logic)

3. **Use Usage Plans for Rate Limiting (Recommended)**
   - Prevent one customer from DDoSing others
   - Set per-customer limits
   - Cost: $0 (free feature)

4. **Enable CloudWatch Alarms (Recommended)**
   - Alert on high error rates per customer
   - Alert on unauthorized access attempts
   - Cost: $0.10 per alarm

5. **Optional: Add IP Allowlisting**
   - Restrict to customer's GCP IP ranges
   - Additional security layer
   - Requires customer to provide IPs

6. **Optional: Enable API Gateway Logging**
   - Log all requests for audit trail
   - Detect suspicious patterns
   - Cost: ~$0.50/month per customer

**Security Comparison: Single API Gateway vs Separate API Gateways**

| Security Aspect | Single API Gateway | Separate API Gateways |
|----------------|--------------------|-----------------------|
| **Authentication** | ✅ Same (OIDC required for both) | ✅ Same |
| **Customer Isolation** | ✅ Route + Lambda isolation | ✅ API + Lambda isolation |
| **Attack Surface** | ⚠️ Single API endpoint | ✅ Isolated API endpoints |
| **DDoS Risk** | ⚠️ One customer can impact others (without Usage Plans) | ✅ Customer isolated by API |
| **Credential Exposure** | ✅ Same token validation | ✅ Same |
| **Blast Radius** | ⚠️ API Gateway issue affects all | ✅ API Gateway issue affects one |
| **Security Level** | ⭐⭐⭐⭐☆ High | ⭐⭐⭐⭐⭐ Maximum |

**Security Level: HIGH ⭐⭐⭐⭐☆**

With OIDC authentication + route validation + Usage Plans:
- ✅ Cryptographic authentication (cannot forge tokens)
- ✅ Per-customer authorization (cannot access others' routes)
- ✅ Per-customer rate limiting (cannot DDoS others)
- ✅ Lambda isolation (separate functions per customer)
- ⚠️ Shared API Gateway (single point of failure)

**Upgrade to Maximum Security:**
- Add separate API Gateways per customer (+$15/month)
- Add IP allowlisting per customer route ($0)
- Add WAF rules ($5-10/month)
- Enable API Gateway request validation ($0)

**Recommendation:**
Single API Gateway with OIDC + Usage Plans provides **sufficient security for 99% of SaaS applications**. Only upgrade to separate API Gateways if compliance requires complete API-level isolation.

---

### Option 2: One API Gateway Per Customer

```
┌─────────────────────────────────────────────────────────────────┐
│ API Gateway 1 (customer1.api.example.com)                      │
├─────────────────────────────────────────────────────────────────┤
│  POST /webhook → Lambda-customer1                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ API Gateway 2 (customer2.api.example.com)                      │
├─────────────────────────────────────────────────────────────────┤
│  POST /webhook → Lambda-customer2                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ API Gateway 3 (customer3.api.example.com)                      │
├─────────────────────────────────────────────────────────────────┤
│  POST /webhook → Lambda-customer3                              │
└─────────────────────────────────────────────────────────────────┘

... (30 separate API Gateways)
```

**Cost (30 customers, 300K requests/month = 10K per customer):**

| Service | Calculation | Cost |
|---------|-------------|------|
| API Gateway | 30 gateways × (10K requests × $3.50/million) | $1.05 |
| Custom Domains | 30 domains × $0 | $0.00 |
| SSL Certificates (ACM) | 30 certs × $0 | $0.00 |
| Route53 DNS | 30 hosted zones × $0.50 | $15.00 |
| **TOTAL** | | **$16.05/month** |

**Pros:**
- ✅ **Customer-specific domains** - customer1.api.example.com
- ✅ **Complete isolation** - Separate API per customer
- ✅ **Independent rate limiting** - Per-customer API Gateway throttles
- ✅ **Customer branding** - Can use customer's domain
- ✅ **Blast radius containment** - API Gateway issue affects only one customer

**Cons:**
- ❌ **15× more expensive** - $16.05 vs $1.05
- ❌ **Complex management** - 30 API Gateways to configure
- ❌ **30 SSL certificates** - Must manage 30 ACM certs
- ❌ **30 DNS records** - Route53 overhead
- ❌ **Deployment complexity** - Must update 30 APIs for changes
- ❌ **Monitoring overhead** - 30 API Gateway dashboards

**When to Use:**
- Enterprise customers require branded domains
- Customer contract specifies dedicated API Gateway
- Customer pays premium ($5-10/month extra)
- Need complete API-level isolation

---

### Option 3: Hybrid - Single API Gateway with Usage Plans (Optimal)

```
┌─────────────────────────────────────────────────────────────────┐
│ Single API Gateway (api.example.com)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Routes with Usage Plans:                                       │
│                                                                 │
│  /webhook/customer1 → Lambda-customer1                         │
│    └─ Usage Plan: customer1-plan (1000 req/sec)               │
│                                                                 │
│  /webhook/customer2 → Lambda-customer2                         │
│    └─ Usage Plan: customer2-plan (500 req/sec)                │
│                                                                 │
│  /webhook/customer3 → Lambda-customer3                         │
│    └─ Usage Plan: customer3-plan (2000 req/sec - enterprise)  │
│                                                                 │
│  ... (30 routes with 30 usage plans)                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Cost (30 customers, 300K requests/month):**

| Service | Calculation | Cost |
|---------|-------------|------|
| API Gateway | 300K requests × $3.50/million | $1.05 |
| Usage Plans | 30 plans × $0 (free feature) | $0.00 |
| Custom Domain | 1 domain | $0.00 |
| SSL Certificate | 1 cert | $0.00 |
| **TOTAL** | | **$1.05/month** |

**Pros:**
- ✅ **Same cost as single API** - $1.05/month
- ✅ **Per-customer rate limiting** - Independent throttles
- ✅ **Simple management** - One API to deploy
- ✅ **Tiered access** - Different limits per customer tier
- ✅ **Best of both worlds** - Cost efficiency + customer isolation

**Cons:**
- ❌ **Still shared domain** - All use api.example.com
- ❌ **Usage Plan overhead** - Must configure 30 plans

**When to Use:**
- Need per-customer rate limiting
- Want cost efficiency of single API
- Don't need customer-specific domains
- **Recommended for most production use cases**

---

## Cost Comparison: API Gateway Options

| Option | Monthly Cost | Cost per Customer | Complexity | Use Case |
|--------|--------------|-------------------|------------|----------|
| **Single API Gateway** | $1.05 | $0.035 | Low | ✅ Standard SaaS (recommended) |
| **Single API + Usage Plans** | $1.05 | $0.035 | Medium | ✅ Production SaaS with rate limits |
| **One API Gateway per Customer** | $16.05 | $0.54 | Very High | ⚠️ Enterprise with custom domains only |

---

## Updated Total Cost with API Gateway

### Single API Gateway (Recommended)

| Component | Cost |
|-----------|------|
| API Gateway | $1.05 |
| 30 Lambda Functions | $6.06 |
| CloudWatch Logs | $15.00 |
| CloudWatch Metrics | $30.00 |
| CloudWatch Dashboards | $90.00 |
| **TOTAL** | **$142.11/month** |
| **Cost per Customer** | **$4.74/month** |

### One API Gateway per Customer

| Component | Cost |
|-----------|------|
| 30 API Gateways | $1.05 |
| Route53 (30 zones) | $15.00 |
| 30 Lambda Functions | $6.06 |
| CloudWatch Logs | $15.00 |
| CloudWatch Metrics | $30.00 |
| CloudWatch Dashboards | $90.00 |
| **TOTAL** | **$157.11/month** |
| **Cost per Customer** | **$5.24/month** |

**Difference:** $15/month extra for separate API Gateways (due to Route53)

---

## Recommendation

### Use Single API Gateway with Usage Plans

**Why:**
- ✅ **Lowest cost** - $1.05/month (vs $16.05 with separate)
- ✅ **Per-customer rate limiting** - Via Usage Plans (free)
- ✅ **Simple operations** - One API to deploy/monitor
- ✅ **Scalable** - Easy to add new customers (add route + usage plan)
- ✅ **99% of use cases** - Works for standard SaaS

**Configuration Example:**
```
Customer Tier 1 (Small): 100 req/sec limit
Customer Tier 2 (Medium): 500 req/sec limit  
Customer Tier 3 (Large): 1000 req/sec limit
Customer Tier 4 (Enterprise): 5000 req/sec limit
```

### Only Use Separate API Gateways If:

1. **Customer requires branded domain**
   - customer1.yourservice.com instead of yourservice.com/customer1
   - Customer pays $10-20/month premium

2. **Complete API isolation required**
   - Compliance mandates separate API endpoints
   - Customer contract specifies dedicated API Gateway

3. **Customer pays for it**
   - Enterprise customer willing to pay $5.24/month vs $4.74/month
   - $0.50/month difference covers Route53 cost

---

## Authentication Options

### Option A: No Authentication (Lambda = Identity)

Since each customer has dedicated Lambda:
- API Gateway route `/webhook/customer1` → `Lambda-customer1` only
- Customer1 cannot reach Lambda-customer2 (different endpoint)
- Lambda function itself is the identity

**Security Model:**
- ✅ API Gateway path-based routing
- ✅ AWS IAM (who can invoke which Lambda)
- ⚠️ Anyone with the URL can send to that customer's endpoint

**Acceptable When:**
- API Gateway has IP allowlisting per route
- URL is kept secret (not published)
- Low-medium security requirements
- Internal use case

**Risk:**
- If URL leaks, attacker can inject fake data
- Must rely on IP allowlisting for security

**Cost:** $0 (no authorizer Lambda needed)

---

### Option B: OIDC Authentication (Defense in Depth - Recommended)

Even with dedicated Lambda, still validate OIDC token:
- Prevents unauthorized parties from sending fake data
- Validates requests actually come from customer's GCP
- Provides audit trail (token includes timestamp, issuer)

**Security Model:**
- Customer's GCP Pub/Sub sends OIDC token in Authorization header
- Lambda Authorizer validates token before allowing request
- Cryptographic proof of origin

**Benefits:**
- ✅ Cryptographic proof of origin
- ✅ Cannot forge without Google's private key
- ✅ Audit trail (token includes timestamp)
- ✅ Defense in depth

**Cost:** +$1.50/month (shared authorizer Lambda for all customers)

**Required When:**
- Production SaaS with external customers
- Compliance requirements
- Customer data is sensitive
- Need proof of origin

---

### Option C: API Key (Simple but Less Secure)

**Security Model:**
- Customer's GCP Pub/Sub sends X-API-Key header
- API Gateway validates key before invoking Lambda
- Simple string comparison

**Benefits:**
- ✅ Simple to implement
- ✅ No Lambda Authorizer needed
- ✅ API Gateway handles validation

**Risks:**
- ⚠️ Key can leak (logs, Git commits)
- ⚠️ No auto-rotation
- ⚠️ Must manually rotate keys

**Cost:** +$0.40/month per customer (Secrets Manager storage)

---

## Recommendation by Security Level

| Security Level | Recommended Approach | Cost | Complexity |
|---------------|---------------------|------|------------|
| **Low (Internal)** | IP Allowlisting only | $0 | Low |
| **Medium (Standard SaaS)** | OIDC Token | +$1.50/month | Medium |
| **High (Enterprise)** | OIDC + IP Allowlisting | +$1.50/month | Medium |
| **Maximum (Banking/Healthcare)** | mTLS | +$35/month (ALB) | High |

---

## Cost Analysis

### Monthly Cost (30 customers, 300K requests/month = 10K per customer)

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

---

### Cost Breakdown by Customer Tier

| Customer Tier | Requests/Month | Memory | Lambda Cost | Total Cost/Month |
|---------------|----------------|--------|-------------|------------------|
| Small (Tier 1) | 5K | 256MB | $0.50 | $3.50 |
| Medium (Tier 2) | 10K | 512MB | $1.00 | $4.70 |
| Large (Tier 3) | 50K | 1024MB | $8.00 | $11.00 |
| Enterprise (Tier 4) | 100K | 2048MB | $20.00 | $23.00 |

---

### Cost Scaling Analysis

| Customers | Total Requests/Month | Monthly Cost | Cost per Customer |
|-----------|---------------------|--------------|-------------------|
| 10 | 100K | $50.00 | $5.00 |
| 30 | 300K | $141.11 | $4.70 |
| 50 | 500K | $230.00 | $4.60 |
| 100 | 1M | $450.00 | $4.50 |
| 200 | 2M | $890.00 | $4.45 |

**Observation:** Cost per customer decreases slightly with scale due to shared services (API Gateway, authorizer).

---

### Cost Comparison vs Other Architectures

| Architecture | 30 Customers Cost | Cost per Customer | Isolation Level |
|--------------|-------------------|-------------------|----------------|
| Shared endpoint + Single Lambda | $5.05 | $0.17 | Logical |
| Per-customer endpoint + Single Lambda | $95.05 | $3.17 | Logical |
| **One Lambda per customer** | **$141.11** | **$4.70** | Physical |
| Per-customer ECS containers | $200.00 | $6.67 | Physical |

---

### Cost Analysis Summary

- ⚠️ **28× more expensive than shared Lambda** ($141 vs $5)
- ❌ **$4.70 per customer** vs $0.17 shared
- ✅ **30% cheaper than ECS containers** ($141 vs $200)
- ⚠️ **CloudWatch monitoring is 85% of total cost** ($135 out of $141)
- ✅ **Worth it IF** complete isolation is required (compliance, enterprise)

---

## Cost Optimization Strategies

### Strategy 1: Reduce CloudWatch Costs (85% of total cost)

**Option A: Single Aggregate Dashboard**
- Instead of 30 dashboards ($90/month)
- Use 1 dashboard with all customers ($3/month)
- **Savings: $87/month (62% reduction)**

**Option B: Reduce Log Retention**
- Instead of 30 days retention
- Use 7 days retention
- **Savings: ~$10/month**

**Option C: Sample Logs**
- Log only 10% of successful requests
- Log 100% of errors
- **Savings: ~$12/month**

**Combined Optimization:**
```
Original Cost: $141.11/month
- Single dashboard: -$87.00
- Reduced retention: -$10.00
- Log sampling: -$12.00
Optimized Cost: $32.11/month ($1.07 per customer)
```

---

### Strategy 2: Right-Size Lambda Memory

**Current:** All customers use 512MB default

**Optimized:**
- Small customers: 256MB instead of 512MB
  - Savings: ~$1/customer/month
- Monitor performance and adjust:
  - If latency <500ms: Consider reducing memory
  - If latency >1000ms: Consider increasing memory

**Potential Savings:** $10-15/month for mixed customer sizes

---

### Strategy 3: Tiered Pricing Model

Pass costs through to customers:

| Customer Tier | Monthly Cost | Your Price | Margin |
|---------------|-------------|-----------|--------|
| Small | $1.00 | $5.00 | $4.00 |
| Medium | $4.70 | $10.00 | $5.30 |
| Large | $11.00 | $25.00 | $14.00 |
| Enterprise | $23.00 | $50.00 | $27.00 |

---

## When This Architecture Makes Sense

### ✅ Use One Lambda Per Customer If:

1. **Compliance Requires Physical Separation**
   - HIPAA, PCI-DSS, FedRAMP mandates
   - Regulations require dedicated compute resources
   - Auditors require proof of air-gapped environments

2. **Enterprise Customers Demand It**
   - SLA guarantees require dedicated resources
   - Customer contract specifies "no shared infrastructure"
   - Customer pays premium ($10-50/month extra)

3. **Customers Have Very Different Requirements**
   - Customer A needs 10GB memory, Customer B needs 128MB
   - Different timeout requirements per customer (30s vs 5min)
   - Different Portal26 endpoints per customer

4. **High Blast Radius Risk**
   - Customer data is extremely sensitive (financial, health, government)
   - One customer compromise must not affect others
   - Need provable isolation for insurance/liability

5. **Budget Allows 28× Cost Increase**
   - $5/month → $141/month is acceptable
   - Customer pays for dedicated resources
   - Cost passed through to customer

6. **Plan to Scale to <200 Customers**
   - Operational overhead manageable
   - Under AWS Lambda function limits (~1000 per region)
   - Monitoring cost acceptable

---

### ❌ Do NOT Use One Lambda Per Customer If:

1. **Cost is a Concern**
   - Cannot justify 28× cost increase
   - Customers won't pay for dedicated Lambda
   - Startup/small business with tight budget

2. **Want Simple Operations**
   - Don't want to manage 30+ Lambda functions
   - Small team, limited DevOps resources
   - Want to deploy updates quickly (single Lambda = 2 min, 30 Lambdas = 30 min)

3. **Plan to Scale to 500+ Customers**
   - AWS Lambda limit ~1000 functions per region
   - Operational overhead grows linearly
   - Monitoring cost becomes prohibitive ($300+/month)

4. **All Customers Have Similar Requirements**
   - All use same memory, timeout, configuration
   - No special isolation requirements
   - Standard SaaS use case

---

## Use Case Examples

### Example 1: Healthcare SaaS (Perfect Fit)

**Scenario:**
- 20 hospital customers
- HIPAA compliance required
- Customer data cannot comingle
- Each customer pays $50/month

**Cost:**
- AWS cost: $100/month (20 customers × $5/customer)
- Revenue: $1000/month (20 × $50)
- **Margin: $900/month (90%)**

**Why it works:** Compliance requirement + customers pay for dedicated resources

---

### Example 2: Standard SaaS (Wrong Fit)

**Scenario:**
- 100 small business customers
- No special compliance requirements
- Customers pay $10/month

**Cost:**
- One Lambda per customer: $450/month (100 × $4.50)
- Revenue: $1000/month (100 × $10)
- **Margin: $550/month (55%)**

**Better option:**
- Shared Lambda: $15/month (100 customers)
- Revenue: $1000/month
- **Margin: $985/month (98.5%)**

**Why it's wrong:** No compliance need, costs eat into margins

---

### Example 3: Hybrid Approach (Optimal)

**Scenario:**
- 25 standard customers + 5 enterprise customers
- Standard customers share infrastructure
- Enterprise customers get dedicated Lambdas

**Cost:**
- Shared Lambda (25 customers): $5/month
- Dedicated Lambdas (5 enterprise): $23.50/month (5 × $4.70)
- **Total: $28.50/month for 30 customers**

**vs All Dedicated:**
- All dedicated: $141/month
- **Savings: $112.50/month (80% reduction)**

**Why it's optimal:** Only enterprises who need/pay for it get dedicated resources

---

## Summary

### Key Takeaways

1. **Cost**: 28× more expensive than shared Lambda
   - $141/month for 30 customers vs $5/month
   - CloudWatch monitoring is 85% of cost

2. **Optimization**: Can reduce to ~$32/month
   - Single aggregate dashboard (-$87)
   - Reduced log retention (-$10)
   - Log sampling (-$12)

3. **When to Use**: Only for compliance or enterprise requirements
   - HIPAA, PCI-DSS mandates
   - Enterprise customers who pay for it
   - <200 customers

4. **Hybrid Model**: Best of both worlds
   - Shared Lambda for standard customers
   - Dedicated Lambda for enterprise only
   - 80% cost savings vs all-dedicated

### Cost Comparison at a Glance

| Approach | 30 Customers Cost | Cost per Customer | Recommended For |
|----------|-------------------|-------------------|----------------|
| **Shared Lambda** | $5.05 | $0.17 | ✅ Standard SaaS (recommended for 99%) |
| **Hybrid (25 shared + 5 dedicated)** | $28.50 | $0.95 avg | ✅ SaaS with few enterprise customers |
| **All Dedicated** | $141.11 | $4.70 | ⚠️ Compliance-driven only |
| **ECS Containers** | $200.00 | $6.67 | ❌ Not recommended |

### Final Recommendation

**Start with shared Lambda ($5/month)**

Only add per-customer Lambdas for:
- Enterprise customers who explicitly require it
- Compliance mandates (HIPAA, PCI-DSS)
- Customers who pay premium ($10-50/month extra)

This gives you flexibility without overcommitting to expensive infrastructure.
