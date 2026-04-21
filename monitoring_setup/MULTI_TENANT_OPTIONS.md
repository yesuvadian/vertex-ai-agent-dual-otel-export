# Multi-Tenant AWS Lambda Webhook - All Options

## Architecture Overview

### Shared Multi-Tenant (Recommended)
```
Customer 1 (GCP Pub/Sub) ──┐
Customer 2 (GCP Pub/Sub) ──┼──> Single AWS Lambda ──> Single Portal26 OTEL
Customer 3 (GCP Pub/Sub) ──┘     (webhook handler)
```

### Per-Customer Containers (Not Recommended)
```
Customer 1 → Container 1 (/webhook/customer-1) → OTEL endpoint 1
Customer 2 → Container 2 (/webhook/customer-2) → OTEL endpoint 2
Customer 3 → Container 3 (/webhook/customer-3) → OTEL endpoint 3
```

---

## Authentication Options

### Option 1: OIDC Token Authentication (Recommended for Production)

#### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│ Customer Setup (GCP)                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Customer creates Service Account                           │
│     └─> customer1@project.iam.gserviceaccount.com             │
│                                                                 │
│  2. Customer creates Pub/Sub Push Subscription                 │
│     └─> Push endpoint: https://api.example.com/webhook        │
│     └─> OIDC authentication enabled                           │
│     └─> Service account: customer1@project...                 │
│                                                                 │
│  3. GCP auto-generates OIDC tokens                             │
│     └─> Signed JWT by Google                                   │
│     └─> Auto-rotates every 1 hour                             │
│     └─> Contains: iss, aud, email, exp                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS POST with JWT in Authorization header
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ AWS Security Layer                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: API Gateway                                          │
│  └─> Rate limiting: 1000 req/sec                              │
│  └─> IP allowlist (optional)                                   │
│  └─> WAF rules                                                 │
│                                                                 │
│  Layer 2: Lambda Authorizer                                    │
│  └─> Extracts JWT from Authorization header                    │
│  └─> Fetches Google's public keys (jwks)                       │
│  └─> Verifies JWT signature cryptographically                  │
│  └─> Validates: iss=accounts.google.com, aud=correct, not expired │
│  └─> Checks service account in allowlist                       │
│  └─> Returns: Allow/Deny + customer context                   │
│                                                                 │
│  Layer 3: Main Lambda Handler                                 │
│  └─> Receives validated customer identity                      │
│  └─> Extracts customer_id from authorizer context             │
│  └─> Decodes Pub/Sub message                                  │
│  └─> Validates message structure                              │
│  └─> Adds customer.id attribute to logs                       │
│  └─> Forwards to Portal26 with customer isolation             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ OTEL logs with customer.id attribute
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Portal26 OTEL Endpoint                                          │
├─────────────────────────────────────────────────────────────────┤
│  - Receives logs with customer.id                              │
│  - Customer 1 queries: WHERE customer.id = "customer1"         │
│  - Customer 2 queries: WHERE customer.id = "customer2"         │
│  - Complete data isolation at query level                      │
└─────────────────────────────────────────────────────────────────┘
```

#### Security Analysis

**Security Level: HIGH**

| Security Aspect | Rating | Details |
|----------------|--------|---------|
| Authentication | ⭐⭐⭐⭐⭐ | Cryptographic JWT verification using Google's public keys |
| Token Rotation | ⭐⭐⭐⭐⭐ | Automatic every 1 hour, no manual management |
| Replay Protection | ⭐⭐⭐⭐⭐ | Short expiry (1 hour), timestamp validation |
| Spoofing Protection | ⭐⭐⭐⭐⭐ | Cryptographic signature, impossible to forge without Google's private key |
| Customer Isolation | ⭐⭐⭐⭐⭐ | Service account email uniquely identifies customer |
| Credential Leakage Risk | ⭐⭐⭐⭐⭐ | No long-lived credentials stored anywhere |
| Revocation | ⭐⭐⭐⭐☆ | Remove service account from allowlist (takes effect in 5 min cache TTL) |

**Security Layers:**
1. **Network**: TLS 1.2+, IP allowlisting, WAF
2. **Authentication**: OIDC JWT cryptographic verification
3. **Authorization**: Service account allowlist check
4. **Validation**: Message structure, age, format checks
5. **Encryption**: All data in transit encrypted

**Attack Vectors & Mitigations:**
- ❌ Token forgery → Prevented by cryptographic signature verification
- ❌ Token replay → Prevented by short expiry + timestamp validation
- ❌ Customer impersonation → Prevented by unique service account per customer
- ❌ Man-in-the-middle → Prevented by TLS encryption
- ❌ DDoS → Mitigated by rate limiting + auto-scaling

#### Cost Analysis

**Monthly Cost (30 customers, 300K requests/month):**

| Service | Calculation | Cost |
|---------|-------------|------|
| API Gateway | 300K requests × $3.50/million | $1.05 |
| Lambda Authorizer | 300K invocations × 200ms × $0.0000000167/ms | $1.00 |
| Lambda Authorizer Memory | 300K × 512MB-ms × $0.0000000167 | $0.56 |
| Lambda Main Handler | 300K invocations × 500ms × $0.0000000167/ms | $2.50 |
| Lambda Main Memory | 300K × 512MB-ms × $0.0000000167 | $0.50 |
| CloudWatch Logs | 2GB storage + queries | $0.50 |
| **TOTAL** | | **$6.11/month** |

**Cost per Customer:** $0.20/month

**Cost Scaling:**

| Customers | Requests/Month | Monthly Cost | Cost per Customer |
|-----------|----------------|--------------|-------------------|
| 10 | 100K | $2.50 | $0.25 |
| 30 | 300K | $6.11 | $0.20 |
| 100 | 1M | $15.00 | $0.15 |
| 500 | 5M | $65.00 | $0.13 |
| 1000 | 10M | $125.00 | $0.13 |

**Cost scales logarithmically** - the more customers, the cheaper per customer.

#### Pros & Cons

**Pros:**
- ✅ **Highest security** - Cryptographic verification, no credential storage
- ✅ **Zero credential management** - Google handles token generation and rotation
- ✅ **Auto-rotation** - New token every hour automatically
- ✅ **Audit trail** - Every request tied to specific service account
- ✅ **Scalable** - Handles 1000+ customers with no architecture changes
- ✅ **Low cost** - $0.13-0.25 per customer/month at scale
- ✅ **Fast onboarding** - Add customer = 1 line in allowlist (2 minutes)
- ✅ **Google-recommended** - Official best practice for Pub/Sub push
- ✅ **No secrets in code** - Public key verification only
- ✅ **Compliance-friendly** - Meets SOC2, ISO27001 requirements

**Cons:**
- ❌ **Initial complexity** - Requires understanding JWT/OIDC concepts
- ❌ **Authorizer overhead** - Adds ~100-200ms latency per request
- ❌ **Google dependency** - Requires Google's JWKS endpoint to be available
- ❌ **5-minute cache** - Service account removal takes up to 5 min to propagate
- ❌ **Debugging** - Token validation errors can be cryptic

**When to Use:**
- ✅ Production SaaS with multiple customers
- ✅ Security/compliance is critical
- ✅ Need audit trail per customer
- ✅ Want zero credential management overhead
- ✅ Planning to scale to 100+ customers

---

### Option 2: API Key Authentication

#### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│ Customer Setup (GCP)                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. You generate unique API key for customer                   │
│     └─> customer1_key_abc123def456                             │
│                                                                 │
│  2. Customer creates Pub/Sub Push Subscription                 │
│     └─> Push endpoint: https://api.example.com/webhook        │
│     └─> Custom header: X-API-Key: customer1_key_abc123def456  │
│                                                                 │
│  3. Customer stores API key in Pub/Sub config                  │
│     └─> Manually added to push subscription                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS POST with X-API-Key header
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ AWS Security Layer                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: API Gateway                                          │
│  └─> Rate limiting                                             │
│  └─> IP allowlist (recommended)                               │
│                                                                 │
│  Layer 2: Lambda Authorizer                                    │
│  └─> Extracts X-API-Key from headers                          │
│  └─> Loads API key mapping from AWS Secrets Manager           │
│  └─> Simple string comparison: key == stored_key?             │
│  └─> Returns: Allow/Deny + customer_id                        │
│                                                                 │
│  Layer 3: Main Lambda Handler                                 │
│  └─> Receives customer_id from authorizer                     │
│  └─> Processes message                                         │
│  └─> Adds customer.id attribute                               │
│  └─> Forwards to Portal26                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                      Portal26 OTEL
```

#### Security Analysis

**Security Level: MEDIUM**

| Security Aspect | Rating | Details |
|----------------|--------|---------|
| Authentication | ⭐⭐⭐☆☆ | Simple string comparison, no cryptographic verification |
| Token Rotation | ⭐☆☆☆☆ | Manual rotation required, customers must update config |
| Replay Protection | ⭐⭐☆☆☆ | No built-in protection, same key works forever |
| Spoofing Protection | ⭐⭐☆☆☆ | If key leaks, attacker can impersonate customer |
| Customer Isolation | ⭐⭐⭐⭐☆ | API key maps to customer_id |
| Credential Leakage Risk | ⭐⭐☆☆☆ | Long-lived credentials stored in AWS Secrets Manager and customer's GCP |
| Revocation | ⭐⭐⭐⭐☆ | Delete key from Secrets Manager (instant) |

**Security Risks:**
- ⚠️ **API key leakage** - If customer accidentally logs key, commits to Git, or includes in error messages
- ⚠️ **No rotation** - Same key used indefinitely unless manually rotated
- ⚠️ **Credential sprawl** - Keys stored in multiple places (AWS Secrets Manager, customer's GCP, logs)
- ⚠️ **Limited audit** - Can't distinguish between legitimate use and compromised key use

**Security Layers:**
1. **Network**: TLS 1.2+, IP allowlisting (CRITICAL for API keys)
2. **Authentication**: API key string comparison
3. **Authorization**: Key-to-customer mapping check
4. **Validation**: Message structure checks
5. **Encryption**: TLS encryption

#### Cost Analysis

**Monthly Cost (30 customers, 300K requests/month):**

| Service | Calculation | Cost |
|---------|-------------|------|
| API Gateway | 300K requests × $3.50/million | $1.05 |
| Lambda Authorizer | 300K invocations × 100ms × $0.0000000167/ms | $0.50 |
| Lambda Authorizer Memory | 300K × 256MB-ms × $0.0000000167 | $0.28 |
| Lambda Main Handler | 300K invocations × 500ms × $0.0000000167/ms | $2.50 |
| Lambda Main Memory | 300K × 512MB-ms × $0.0000000167 | $0.50 |
| AWS Secrets Manager | 30 secrets × $0.40/month | $12.00 |
| CloudWatch Logs | 2GB storage | $0.50 |
| **TOTAL** | | **$17.33/month** |

**Cost per Customer:** $0.58/month

**Note:** Secrets Manager is expensive at scale ($0.40 per secret per month).

#### Pros & Cons

**Pros:**
- ✅ **Simple to implement** - No JWT/OIDC knowledge required
- ✅ **Fast validation** - Simple string comparison (~50ms)
- ✅ **Easy to debug** - API key mismatch errors are straightforward
- ✅ **No external dependencies** - Doesn't rely on Google's JWKS endpoint
- ✅ **Instant revocation** - Delete key from Secrets Manager immediately
- ✅ **Works with any client** - Not limited to GCP Pub/Sub

**Cons:**
- ❌ **Security risk** - Keys can leak, no cryptographic protection
- ❌ **Manual rotation** - You must generate new keys and coordinate with customers
- ❌ **Higher cost** - $12/month for Secrets Manager (30 customers)
- ❌ **Credential management overhead** - Must securely share keys with customers
- ❌ **No audit trail** - Can't distinguish between users of same key
- ❌ **Compliance issues** - Doesn't meet SOC2/ISO27001 requirements for key rotation
- ❌ **Requires IP allowlisting** - Must restrict by IP to mitigate key leakage
- ❌ **Customer coordination** - Must update key in customer's Pub/Sub config during rotation

**When to Use:**
- ✅ Development/testing environments only
- ✅ Internal use (not for external customers)
- ✅ Short-term proof-of-concept
- ✅ When combined with strict IP allowlisting

**NOT Recommended For:**
- ❌ Production SaaS
- ❌ External customers
- ❌ Compliance-sensitive environments
- ❌ Long-term deployment

---

### Option 3: Mutual TLS (mTLS) Authentication

#### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│ Customer Setup (GCP)                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Customer generates client certificate                      │
│     └─> customer1.crt + customer1.key                          │
│     └─> Signed by your CA or self-signed                       │
│                                                                 │
│  2. Customer uploads certificate to GCP Pub/Sub                │
│     └─> Push subscription with mTLS config                     │
│                                                                 │
│  3. Customer sends client cert in TLS handshake                │
│     └─> Two-way TLS authentication                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS POST with client certificate
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ AWS Security Layer                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: Application Load Balancer (ALB)                      │
│  └─> Requires client certificate in TLS handshake             │
│  └─> Verifies certificate against your CA                      │
│  └─> Rejects if certificate invalid/expired/untrusted         │
│  └─> Passes certificate details to Lambda                      │
│                                                                 │
│  Layer 2: Lambda Authorizer                                    │
│  └─> Extracts certificate CN (Common Name)                    │
│  └─> Maps CN to customer_id                                   │
│  └─> Validates certificate is not revoked (CRL check)         │
│  └─> Returns: Allow/Deny + customer context                   │
│                                                                 │
│  Layer 3: Main Lambda Handler                                 │
│  └─> Receives customer_id from authorizer                     │
│  └─> Processes and forwards to Portal26                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                      Portal26 OTEL
```

#### Security Analysis

**Security Level: VERY HIGH**

| Security Aspect | Rating | Details |
|----------------|--------|---------|
| Authentication | ⭐⭐⭐⭐⭐ | Cryptographic certificate verification at TLS layer |
| Token Rotation | ⭐⭐⭐☆☆ | Manual certificate renewal (typically 1-year validity) |
| Replay Protection | ⭐⭐⭐⭐⭐ | Certificate-based, works at TLS layer before application |
| Spoofing Protection | ⭐⭐⭐⭐⭐ | Impossible without customer's private key |
| Customer Isolation | ⭐⭐⭐⭐⭐ | Certificate CN uniquely identifies customer |
| Credential Leakage Risk | ⭐⭐⭐⭐☆ | Private key must be protected, but not transmitted |
| Revocation | ⭐⭐⭐☆☆ | Requires CRL (Certificate Revocation List) management |

**Security Layers:**
1. **Network**: TLS 1.3 with mutual authentication
2. **Authentication**: Certificate verification at TLS handshake
3. **Authorization**: Certificate CN allowlist check
4. **Validation**: CRL (revocation) check, expiry validation
5. **Encryption**: End-to-end TLS encryption

**Security Strengths:**
- ✅ **Maximum security** - Authentication happens at TLS layer, before application
- ✅ **Cryptographic** - Based on public key cryptography
- ✅ **Industry standard** - Used in banking, government, high-security systems
- ✅ **No bearer tokens** - Private key never transmitted over network

**Security Challenges:**
- ⚠️ **Certificate management** - Must handle generation, distribution, renewal, revocation
- ⚠️ **CRL overhead** - Must maintain Certificate Revocation List
- ⚠️ **Customer burden** - Customers must securely store private keys

#### Cost Analysis

**Monthly Cost (30 customers, 300K requests/month):**

| Service | Calculation | Cost |
|---------|-------------|------|
| Application Load Balancer | $16.20/month + $0.008/LCU-hour | $35.00 |
| Lambda Authorizer | 300K invocations × 150ms × $0.0000000167/ms | $0.75 |
| Lambda Authorizer Memory | 300K × 512MB-ms × $0.0000000167 | $0.56 |
| Lambda Main Handler | 300K invocations × 500ms × $0.0000000167/ms | $2.50 |
| Lambda Main Memory | 300K × 512MB-ms × $0.0000000167 | $0.50 |
| AWS Certificate Manager | Free for public certs | $0.00 |
| CloudWatch Logs | 2GB storage | $0.50 |
| **TOTAL** | | **$39.81/month** |

**Cost per Customer:** $1.33/month

**Note:** ALB is expensive ($35/month fixed cost) regardless of traffic.

#### Pros & Cons

**Pros:**
- ✅ **Maximum security** - TLS-layer authentication, industry best practice
- ✅ **Cryptographic protection** - Based on public key infrastructure
- ✅ **No bearer tokens** - Private key never leaves customer's system
- ✅ **Authentication before application** - Rejected connections don't reach Lambda
- ✅ **Industry standard** - Well-understood, mature technology
- ✅ **Audit trail** - Certificate CN identifies customer
- ✅ **Compliance-friendly** - Meets highest security standards

**Cons:**
- ❌ **Very complex setup** - Requires CA infrastructure, certificate distribution
- ❌ **High cost** - ALB adds $35/month fixed cost
- ❌ **Certificate management** - Must handle generation, renewal, revocation
- ❌ **Customer burden** - Customers must manage private keys securely
- ❌ **Renewal coordination** - Must coordinate certificate renewals (typically yearly)
- ❌ **CRL maintenance** - Must maintain Certificate Revocation List
- ❌ **Debugging difficulty** - TLS errors are cryptic, hard to troubleshoot
- ❌ **Slower onboarding** - Certificate generation and distribution takes hours/days

**When to Use:**
- ✅ Banking, finance, healthcare (maximum security required)
- ✅ Government, defense contractors
- ✅ Enterprise customers with PKI infrastructure already
- ✅ Compliance requires certificate-based authentication
- ✅ Very high-value data ($millions at risk)

**NOT Recommended For:**
- ❌ Typical SaaS applications
- ❌ Startups or small businesses
- ❌ When rapid customer onboarding is important
- ❌ When cost is a concern

---

## Architecture Comparison: Shared vs Per-Customer

### Shared Multi-Tenant (Recommended)

**Monthly Cost (30 customers):**
- OIDC: $6.11/month ($0.20 per customer)
- API Key: $17.33/month ($0.58 per customer)
- mTLS: $39.81/month ($1.33 per customer)

**Scaling:**
- Add customer: 1 line config change (2 minutes)
- Supports: 1000+ customers without infrastructure changes
- AWS quotas: No concerns until 5000+ customers

**Operational Overhead:**
- Deploy: Once
- Monitor: Single set of metrics
- Debug: Single code path
- Update: Deploy once, affects all customers

### Per-Customer Containers (Not Recommended)

**Monthly Cost (30 customers):**

| Service | Per Customer | 30 Customers |
|---------|--------------|--------------|
| ECS Fargate (0.25 vCPU, 0.5GB) | $5.00 | $150.00 |
| Application Load Balancer (shared) | - | $35.00 |
| CloudWatch Logs | $0.50 | $15.00 |
| **TOTAL** | $5.50 | **$200.00** |

**Cost per Customer:** $6.67/month

**Scaling:**
- Add customer: Deploy new container, configure ALB, setup monitoring (30-60 minutes)
- Supports: 200-500 customers before hitting AWS service quotas
- AWS quotas: ECS service limits, ALB target group limits, CloudWatch namespace limits

**Operational Overhead:**
- Deploy: 30 times (one per customer)
- Monitor: 30 sets of metrics
- Debug: Must check specific customer's container
- Update: Deploy 30 times

### Cons of Per-Customer Architecture

1. **Cost: 650% more expensive**
   - Shared: $6.11/month total (OIDC)
   - Per-customer: $200/month total
   - **You pay 33× more for the same functionality**

2. **Operational Complexity: N× management**
   - 30 containers to deploy, monitor, update
   - 30 CloudWatch log groups
   - 30 sets of environment variables
   - 30 potential failure points

3. **Scalability: Hits AWS limits**
   - ECS service limit: 1000 per account
   - ALB target group limit: 1000 per ALB
   - CloudWatch custom metrics: 10,000 per account
   - At 500+ customers, you need multi-account strategy

4. **Debugging: Fragmented**
   - Must identify which customer's container failed
   - Can't see cross-customer patterns easily
   - 30 separate log streams to search

5. **Deployment Time: 30× slower**
   - Shared: Deploy once (5 minutes)
   - Per-customer: Deploy 30 times (2.5 hours)
   - Code fix requires 30 deployments

6. **Monitoring: 30× metrics**
   - 30 dashboards to check
   - 30 alarm configurations
   - 30 sets of performance metrics

7. **Security: Larger attack surface**
   - 30 containers = 30 potential vulnerabilities
   - 30 network configurations to secure
   - 30 IAM roles to audit

8. **Development: Slower iteration**
   - Must test across multiple containers
   - Harder to reproduce bugs
   - Can't easily test multi-customer scenarios

9. **Portal26 Integration: Complex**
   - 30 OTEL endpoints to manage
   - Or 30 separate tenants in Portal26
   - Harder to aggregate cross-customer metrics

10. **Business Impact: Slower onboarding**
    - New customer: 30-60 minutes to deploy new container
    - Shared: 2 minutes to add config line
    - **Shared is 15-30× faster time-to-revenue**

---

## Recommendation Matrix

| Use Case | Recommended Option | Monthly Cost | Security | Setup Time |
|----------|-------------------|--------------|----------|------------|
| **Production SaaS (most common)** | Shared + OIDC | $6/month | Very High | 2 hours |
| **Development/Testing** | Shared + API Key (with IP allowlist) | $17/month | Medium | 1 hour |
| **Banking/Finance/Healthcare** | Shared + mTLS | $40/month | Maximum | 1 week |
| **Internal monitoring (single company)** | Shared + API Key | $17/month | Medium | 1 hour |
| **Enterprise customers with PKI** | Shared + mTLS | $40/month | Maximum | 1 week |

**DO NOT USE:**
- ❌ Per-Customer Containers (expensive, complex, doesn't scale)
- ❌ API Key in production without IP allowlist (security risk)

---

## Quick Decision Guide

### Choose OIDC Token (Option 1) if:
- ✅ Building production SaaS
- ✅ Want Google-recommended security
- ✅ Need zero credential management
- ✅ Want lowest cost ($0.20/customer/month)
- ✅ Planning to scale to 100+ customers
- ✅ Need compliance (SOC2, ISO27001)

### Choose API Key (Option 2) if:
- ✅ Development/testing environment
- ✅ Internal use only (not customer-facing)
- ✅ Short-term POC
- ✅ Can enforce strict IP allowlisting
- ❌ **NOT for production customer-facing SaaS**

### Choose mTLS (Option 3) if:
- ✅ Banking, finance, healthcare, government
- ✅ Customers already have PKI infrastructure
- ✅ Compliance requires certificate-based auth
- ✅ Maximum security is worth complexity and cost
- ❌ **NOT for typical SaaS applications**

### Choose Shared Multi-Tenant:
- ✅ **ALWAYS** - There is no valid reason to use per-customer containers
- ✅ Lower cost (650% cheaper)
- ✅ Better scalability (1000+ customers)
- ✅ Easier operations (deploy once, not 30 times)

---

## Summary Comparison Table

| Feature | OIDC | API Key | mTLS | Per-Customer |
|---------|------|---------|------|--------------|
| **Security** | Very High | Medium | Maximum | Medium |
| **Cost (30 customers)** | $6 | $17 | $40 | $200 |
| **Cost per customer** | $0.20 | $0.58 | $1.33 | $6.67 |
| **Setup time** | 2 hours | 1 hour | 1 week | 15 hours |
| **Credential rotation** | Auto (1 hour) | Manual | Manual (yearly) | N/A |
| **Scaling (max customers)** | 1000+ | 1000+ | 1000+ | 200-500 |
| **Onboarding time** | 2 min | 5 min | 1-2 days | 30-60 min |
| **Operational overhead** | Very Low | Low | High | Very High |
| **Compliance-friendly** | Yes | No | Yes | No |
| **Google-recommended** | Yes | No | No | No |
| **Production-ready** | ✅ Yes | ❌ No | ✅ Yes | ❌ No |

---

## Final Recommendation

**For 99% of use cases:**

```
✅ Shared Multi-Tenant Lambda + OIDC Token Authentication
```

**Why:**
- ✅ **Secure**: Cryptographic JWT verification, Google-recommended
- ✅ **Cheap**: $0.20 per customer/month (vs $6.67 per-customer containers)
- ✅ **Scalable**: 1000+ customers with no changes
- ✅ **Fast onboarding**: 2 minutes to add new customer
- ✅ **Zero credential management**: Google auto-rotates tokens
- ✅ **Compliance-friendly**: SOC2, ISO27001 compatible
- ✅ **Simple operations**: Deploy once, monitor once, debug once

**Alternative for maximum security environments only:**
```
✅ Shared Multi-Tenant Lambda + mTLS
```
(Banking, healthcare, government only - willing to pay 650% more)

**NEVER use:**
```
❌ Per-Customer Containers (expensive, complex, doesn't scale)
❌ API Key in production without IP allowlist (security risk)
```
