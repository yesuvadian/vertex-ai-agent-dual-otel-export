# Cross-Cloud Observability Architecture wirh Security enabled 
## GCP Vertex AI Agent → AWS Lambda → Portal26 OTEL

**Document Version:** 1.0  
**Date:** 2026-04-22  
**Prepared For:** Architecture Review  
**System:** AI Agent Observability & Monitoring Pipeline

---

## Executive Summary

This document describes a production-ready, secure cross-cloud architecture that captures observability data from Google Cloud Platform's Vertex AI Reasoning Engine and forwards it to AWS-hosted observability platform (Portal26) using industry-standard OIDC authentication.

**Key Architectural Decisions:**
- **Authentication Pattern**: OIDC (OpenID Connect) with JWT tokens for cross-cloud security
- **Data Pipeline**: Asynchronous, push-based architecture using GCP Pub/Sub
- **Processing Layer**: AWS Lambda for lightweight transformation and forwarding
- **Final Destination**: Portal26 OTEL endpoint with S3 storage and Kinesis streaming

**Security Posture:**
- Cryptographically signed JWT tokens from Google Cloud IAM
- Audience and issuer validation on every request
- No shared secrets or API keys
- Complete audit trail across both cloud platforms

---

## Architecture Overview

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   GCP        │         │   GCP        │         │   AWS        │
│   Vertex AI  │────────▶│   Pub/Sub    │────────▶│   Lambda     │
│   Agent      │         │   + OIDC     │         │   Function   │
└──────────────┘         └──────────────┘         └──────────────┘
                                                           │
                                                           ▼
                                                   ┌──────────────┐
                                                   │   Portal26   │
                                                   │   OTEL/S3/   │
                                                   │   Kinesis    │
                                                   └──────────────┘
```

### Data Flow Summary

1. **Source**: Vertex AI Reasoning Engine executes AI agent queries and generates operational logs
2. **Collection**: GCP Cloud Logging automatically captures all agent activity
3. **Routing**: Log Sink filters and forwards relevant logs to Pub/Sub topic
4. **Authentication**: Pub/Sub obtains JWT token from GCP IAM for each message batch
5. **Transport**: Pub/Sub sends authenticated HTTPS POST to AWS Lambda Function URL
6. **Verification**: Lambda validates JWT token with Google OAuth API
7. **Processing**: Lambda extracts and processes log data
8. **Forwarding**: Lambda sends processed data to Portal26 OTEL endpoint
9. **Storage**: Portal26 stores in S3 and streams to Kinesis for analytics

**End-to-End Latency:** ~60-90 seconds (from agent execution to AWS processing)

---

## OIDC Authentication Chain

The architecture implements industry-standard OIDC authentication for cross-cloud security. This eliminates the need for shared secrets while providing cryptographic proof of identity.

### Authentication Flow

```
1. GCP Service Account → Generates identity token
   └─ Service Account: pubsub-oidc-invoker@{project}.iam.gserviceaccount.com
   └─ Role: Service Account Token Creator

2. JWT Token Structure → Signed by Google's private key
   └─ Issuer: https://accounts.google.com
   └─ Audience: {AWS Lambda Function URL}
   └─ Subject: Service Account unique ID
   └─ Expiration: 1 hour

3. GCP Pub/Sub → Adds token to HTTP request
   └─ Header: Authorization: Bearer {JWT}
   └─ Method: HTTPS POST
   └─ Destination: AWS Lambda Function URL

4. AWS Lambda → Receives request
   └─ Extracts JWT from Authorization header
   └─ Calls Google OAuth API for verification

5. Google OAuth API → Validates token
   └─ Verifies signature using Google's public key
   └─ Confirms token not expired
   └─ Returns token claims to Lambda

6. Lambda Validation → Two-step verification
   └─ Step 1: Audience matches Lambda URL
   └─ Step 2: Issuer is Google

7. Processing Decision → Based on validation result
   └─ ✅ Success: Process message and forward to Portal26
   └─ ❌ Failure: Return 403 Forbidden, log security event

8. Audit Trail → Complete logging
   └─ GCP: Pub/Sub delivery logs, IAM token generation logs
   └─ AWS: Lambda CloudWatch logs with authentication details
```

### Security Benefits

**Cryptographic Assurance:**
- JWT tokens signed with Google's private RSA key
- Cannot be forged without access to Google's private key infrastructure
- Signature verified using Google's public key

**Scope Limitation:**
- Each token valid only for specific Lambda URL (audience claim)
- Token cannot be reused for different endpoints
- Time-limited validity (1 hour expiration)

**No Credential Management:**
- No API keys to rotate
- No shared secrets to secure
- No credentials in environment variables or configuration files

**Audit Compliance:**
- Every request logged with service account identity
- Token generation events captured in GCP IAM logs
- Authentication success/failure logged in AWS CloudWatch
- Complete data lineage from source to destination

---

## Component Architecture

### GCP Components

#### 1. Vertex AI Reasoning Engine
- **Service**: aiplatform.googleapis.com/ReasoningEngine
- **Engine ID**: 8213677864684355584
- **Agent Type**: SimpleADKAgent
- **Function**: Executes user queries, calls tools, generates responses
- **Logging**: Automatic stdout/stderr capture to Cloud Logging

#### 2. Cloud Logging
- **Service**: logging.googleapis.com
- **Retention**: 30 days (default)
- **Log Format**: Structured JSON with timestamps and metadata
- **Automatic Capture**: All agent print statements, errors, and system events

#### 3. Log Sink
- **Name**: reasoning-engine-to-pubsub
- **Filter**: `resource.type="aiplatform.googleapis.com/ReasoningEngine" AND reasoning_engine_id="8213677864684355584"`
- **Function**: Routes matching logs to Pub/Sub topic
- **Latency**: 1-2 seconds

#### 4. Pub/Sub Topic
- **Name**: reasoning-engine-logs-topic
- **Purpose**: Message queue for log entries
- **Retention**: 7 days
- **Encoding**: Base64-encoded message data

#### 5. Pub/Sub Subscription
- **Name**: reasoning-engine-to-oidc
- **Type**: Push subscription
- **Endpoint**: AWS Lambda Function URL
- **Authentication**: OIDC with service account
- **Configuration**:
  - Ack deadline: 10 seconds
  - Retry policy: Exponential backoff
  - Dead letter queue: Not configured (optional enhancement)

#### 6. Service Account
- **Email**: pubsub-oidc-invoker@{project}.iam.gserviceaccount.com
- **Role**: roles/iam.serviceAccountTokenCreator
- **Purpose**: Generate OIDC tokens for Pub/Sub push authentication
- **Key Management**: No JSON keys required (token-based auth)

### AWS Components

#### 1. Lambda Function
- **Name**: gcp-pubsub-oidc
- **Runtime**: Python 3.11
- **Memory**: 256 MB
- **Handler**: lambda_with_oidc_simple.lambda_handler
- **Timeout**: 30 seconds (default)
- **Concurrency**: On-demand scaling

**Function URL Configuration:**
- **URL**: https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor.lambda-url.us-east-1.on.aws/
- **Auth Type**: NONE (authentication handled in code)
- **CORS**: Not required (server-to-server)

**Environment Variables:**
- `LAMBDA_URL`: Function URL (used as expected JWT audience)

**Processing Steps:**
1. Extract JWT token from Authorization header
2. Verify token with Google OAuth API
3. Validate audience matches Lambda URL
4. Validate issuer is Google
5. Decode and process message data
6. Forward to Portal26 OTEL endpoint
7. Return 200 OK or appropriate error code

#### 2. CloudWatch Logs
- **Log Group**: /aws/lambda/gcp-pubsub-oidc
- **Retention**: Configurable (default: Never expire)
- **Contents**: Authentication events, message processing, errors
- **Integration**: Portal26 can consume CloudWatch logs if needed

### Portal26 Integration

#### OpenTelemetry (OTEL) Endpoint
- **Protocol**: OTLP (OpenTelemetry Protocol)
- **Format**: Traces, Logs, and Metrics
- **Authentication**: Portal26-specific (configured per customer)

#### Storage Layer
- **S3**: Long-term archival and compliance
  - Compressed storage
  - Lifecycle policies for cost optimization
  - Cross-region replication (optional)

#### Streaming Layer
- **Kinesis**: Real-time analytics and alerting
  - Low-latency event streaming
  - Multiple consumer support
  - Integration with analytics platforms

#### Observability Features
- Multi-tenant dashboards
- Custom alerting rules
- Query and analysis tools
- Data retention policies per customer

---

## Security Architecture

### Threat Model & Mitigations

| Threat | Risk | Mitigation |
|--------|------|------------|
| **Unauthorized access to Lambda** | Attacker sends fake messages | OIDC JWT validation rejects tokens not from GCP |
| **Token replay attack** | Attacker reuses captured token | Token expiration (1 hour), audience validation |
| **Token forgery** | Attacker creates fake token | Google signature verification, private key security |
| **Man-in-the-middle** | Attacker intercepts messages | HTTPS/TLS encryption for all communication |
| **Service account compromise** | Attacker gains SA credentials | Token creator role limited to GCP IAM, no exportable keys |
| **Excessive permissions** | Service account over-privileged | Principle of least privilege: only token creator role |

### Network Security

```
┌─────────────────────────────────────────────────────────────┐
│                         GCP Network                          │
│                                                              │
│  Vertex AI ──▶ Cloud Logging ──▶ Pub/Sub                    │
│                                    │                         │
│                                    │ HTTPS (TLS 1.2+)       │
└────────────────────────────────────┼──────────────────────────┘
                                     │
                                     │ Public Internet
                                     │ (encrypted)
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                         AWS Network                          │
│                                                              │
│  Lambda (Public endpoint with JWT auth)                     │
│    │                                                         │
│    │ HTTPS (TLS 1.2+)                                       │
│    ▼                                                         │
│  Portal26 OTEL Endpoint                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Considerations:**
- Lambda Function URL is public but secured by JWT validation
- No VPC peering required (serverless architecture)
- TLS encryption for all network communication
- Optional: Place Lambda in VPC if Portal26 requires private connectivity

---

## Operational Characteristics

### Scalability

**GCP Pub/Sub:**
- Automatic scaling to handle any message volume
- No provisioning required
- Supports up to 1,000,000 messages/second per topic

**AWS Lambda:**
- Concurrent execution scales automatically
- Regional quota: 1,000 concurrent executions (default)
- Can request quota increases for higher throughput
- Average invocation: ~500ms (including Google OAuth verification)

**Portal26:**
- Designed for multi-tenant scale
- S3 unlimited storage
- Kinesis up to 1 MB/sec per shard (scalable with more shards)

### Reliability

**Message Delivery Guarantees:**
- Pub/Sub: At-least-once delivery
- Lambda: Automatic retries on transient failures
- Dead Letter Queue: Can be configured for failed messages

**Failure Scenarios:**

| Scenario | Behavior | Recovery |
|----------|----------|----------|
| Lambda unavailable | Pub/Sub retries with exponential backoff | Automatic when Lambda recovers |
| JWT verification fails | Lambda returns 403, Pub/Sub retries | Manual investigation required |
| Portal26 unavailable | Lambda returns 500, Pub/Sub retries | Automatic when Portal26 recovers |
| Network partition | Message queued in Pub/Sub | Delivered when connectivity restored |

**Monitoring:**
- GCP: Pub/Sub metrics (undelivered messages, oldest unacked message age)
- AWS: Lambda metrics (invocation count, error rate, duration)
- Portal26: Data ingestion rate, processing lag

### Cost Structure

**GCP Costs:**
- Cloud Logging: $0.50/GB ingested (first 50 GB/month free)
- Pub/Sub: $0.06/GB data, $0.40 per million requests
- Estimated: $5-20/month for typical agent workload

**AWS Costs:**
- Lambda invocations: $0.20 per million requests
- Lambda compute: $0.0000166667/GB-second
- Data transfer OUT: $0.09/GB
- Estimated: $5-15/month for typical workload

**Portal26 Costs:**
- S3 storage: $0.023/GB/month
- Kinesis: $0.015/hour per shard
- Data ingestion: Per customer agreement

**Total Estimated Cost:** $15-50/month (varies with volume)

---

## API Gateway Integration

The OIDC authentication pattern described in this architecture is **fully compatible with AWS API Gateway**. This provides an alternative deployment model with additional benefits:

### Architecture with API Gateway

```
GCP Pub/Sub ──▶ AWS API Gateway ──▶ AWS Lambda ──▶ Portal26
                     │
                     └──▶ JWT Authorizer (validates token)
```

### Benefits of API Gateway Integration

**Built-in JWT Authorization:**
- API Gateway can validate JWT tokens before invoking Lambda
- Reduces Lambda execution time and cost
- Centralized authentication configuration

**Additional Features:**
- Request throttling and rate limiting
- API versioning and stage management
- Request/response transformation
- Custom domain names and TLS certificates
- WAF (Web Application Firewall) integration

**Configuration:**
```
API Gateway JWT Authorizer:
  - Issuer: https://accounts.google.com
  - Audience: {API Gateway endpoint URL}
  - Token location: Authorization header
  - Token validation: Automatic with Google's JWKS endpoint
```

**When to Use:**
- Multiple Lambda functions receiving from GCP
- Need for centralized API management
- Require advanced throttling and rate limiting
- Want to offload JWT validation from Lambda code

**Migration Path:**
- Update Pub/Sub subscription endpoint to API Gateway URL
- Configure API Gateway JWT authorizer
- Lambda code can optionally skip JWT verification (already done by Gateway)
- Same service account and OIDC flow

---

## Configuration Reference

### GCP Project
- **Project ID**: agentic-ai-integration-490716
- **Region**: us-central1

### GCP Resources
- **Vertex AI Engine ID**: 8213677864684355584
- **Pub/Sub Topic**: reasoning-engine-logs-topic
- **Pub/Sub Subscription**: reasoning-engine-to-oidc
- **Service Account**: pubsub-oidc-invoker@agentic-ai-integration-490716.iam.gserviceaccount.com
- **Service Account ID**: 110137324543273212422

### AWS Resources
- **Region**: us-east-1
- **Lambda Function**: gcp-pubsub-oidc
- **Lambda ARN**: arn:aws:lambda:us-east-1:473550159910:function:gcp-pubsub-oidc
- **Function URL**: https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor.lambda-url.us-east-1.on.aws/

### Key URLs
- **GCP Console - Vertex AI**: https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/8213677864684355584
- **GCP Console - Pub/Sub Subscription**: https://console.cloud.google.com/cloudpubsub/subscription/detail/reasoning-engine-to-oidc?project=agentic-ai-integration-490716
- **AWS Console - Lambda**: https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/gcp-pubsub-oidc
- **Google OAuth API**: https://oauth2.googleapis.com/tokeninfo

---

## Future Enhancements

### Short-term (1-3 months)
1. **Dead Letter Queue**: Configure Pub/Sub DLQ for failed message analysis
2. **CloudWatch Alarms**: Alert on Lambda errors or authentication failures
3. **Message Filtering**: Add Pub/Sub message filtering to reduce unnecessary invocations
4. **Batch Processing**: Increase Lambda timeout for batch message processing

### Medium-term (3-6 months)
1. **API Gateway Migration**: Centralize JWT validation and add throttling
2. **Multi-Region**: Deploy Lambda in multiple AWS regions for HA
3. **Message Transformation**: Add schema validation and enrichment in Lambda
4. **Custom Metrics**: Publish business metrics to CloudWatch/Portal26

### Long-term (6+ months)
1. **Event-Driven Architecture**: Add SNS/EventBridge for message routing
2. **Data Lake Integration**: Archive raw logs to S3 for long-term analysis
3. **Machine Learning**: Anomaly detection on agent behavior patterns
4. **Multi-Tenant**: Support multiple GCP projects → single AWS account

---

## Appendix: Setup Scripts

### GCP Setup (setup_gcp_oidc.sh)
Creates service account, grants permissions, configures Pub/Sub subscription with OIDC authentication.

### AWS Setup
Lambda function deployed with Python 3.11 runtime, JWT verification code using Google OAuth API.

### Testing
- Local testing: `python test_local.py` (publishes message to GCP Pub/Sub)
- Log verification: `aws logs tail /aws/lambda/gcp-pubsub-oidc --since 5m --region us-east-1`
- GCP monitoring: Pub/Sub metrics and delivery logs

---

## Document Control

**Author**: AI Agent Team  
**Reviewers**: Architecture Team, Security Team  
**Approval**: Pending  
**Next Review Date**: 2026-07-22 (Quarterly)

**Change History:**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-04-22 | Initial architecture document | AI Agent Team |

---

**END OF DOCUMENT**
