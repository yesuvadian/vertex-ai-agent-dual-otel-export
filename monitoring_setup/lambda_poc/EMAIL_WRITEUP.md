# Email: Cross-Cloud AI Agent Observability Architecture

---

**Subject:** GCP Vertex AI to AWS Lambda Observability Architecture - OIDC Authentication

---

**Hi Team,**

I'm sharing the complete architecture documentation for our cross-cloud observability pipeline that securely forwards AI agent logs from Google Cloud Platform to AWS Lambda and Portal26.

## Overview

This architecture captures operational logs from our Vertex AI Reasoning Engine (AI Agent) running on GCP and securely forwards them to AWS Lambda, which then routes to Portal26's OTEL endpoint for storage (S3) and real-time streaming (Kinesis).

**Key Highlights:**

✅ **Secure Cross-Cloud Communication** - Uses industry-standard OIDC (OpenID Connect) authentication with JWT tokens  
✅ **No Shared Secrets** - Authentication via cryptographically signed tokens from Google Cloud IAM  
✅ **Complete Audit Trail** - Full logging across both GCP and AWS platforms  
✅ **Scalable & Serverless** - Automatic scaling with GCP Pub/Sub and AWS Lambda  
✅ **Production-Ready** - Currently deployed and operational  

## Architecture Flow

```
Vertex AI Agent → Cloud Logging → Log Sink → Pub/Sub → AWS Lambda → Portal26 OTEL
                                                   ↓
                                            JWT Authentication
                                            (Google OAuth API)
```

## OIDC Authentication Chain (8 Steps)

1. **GCP Service Account** → Generates JWT token
2. **JWT Token** → Signed by Google's private key
3. **Pub/Sub** → Adds token to Authorization header
4. **AWS Lambda** → Receives token
5. **Google OAuth API** → Verifies token signature
6. **Lambda** → Validates audience matches Lambda URL
7. **Lambda** → Validates issuer is Google
8. **Result** → ✅ Authenticated and processed OR ❌ Rejected

## Portal26 Integration

The processed data flows to Portal26 observability platform with:
- **OTEL Endpoint**: Standardized OpenTelemetry format for traces, logs, and metrics
- **S3 Storage**: Long-term archival and compliance
- **Kinesis Streaming**: Real-time analytics and alerting

## Why OIDC Authentication?

**Security Benefits:**
- JWT tokens cannot be forged (signed with Google's private key)
- Each token is valid only for our specific Lambda URL (audience validation)
- No API keys or shared secrets to manage or rotate
- Time-limited tokens (1-hour expiration)
- Complete audit trail of all authentication attempts

**Originally Attempted:**
- Custom HTTP headers (X-API-Key, X-Shared-Secret)
- **Issue**: GCP Pub/Sub does not support arbitrary custom headers
- **Solution**: Implemented OIDC, which is natively supported by Pub/Sub

## AWS API Gateway Compatibility

This OIDC authentication pattern is **fully compatible with AWS API Gateway**. The same JWT tokens can be validated by API Gateway's built-in JWT authorizer, providing:
- Centralized authentication before Lambda invocation
- Additional throttling and rate limiting
- Reduced Lambda execution time and cost
- API versioning and management features

Migration to API Gateway is straightforward - just update the Pub/Sub endpoint URL and configure the JWT authorizer.

## Technical Details

**GCP Configuration:**
- Project: agentic-ai-integration-490716
- Vertex AI Engine ID: 8213677864684355584
- Pub/Sub Topic: reasoning-engine-logs-topic
- Pub/Sub Subscription: reasoning-engine-to-oidc (Push type with OIDC)
- Service Account: pubsub-oidc-invoker@agentic-ai-integration-490716.iam.gserviceaccount.com

**AWS Configuration:**
- Region: us-east-1
- Lambda Function: gcp-pubsub-oidc (Python 3.11, 256 MB)
- Function URL: https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor.lambda-url.us-east-1.on.aws/
- Authentication: OIDC with Google OAuth API verification

**End-to-End Latency:** ~60-90 seconds from agent execution to AWS processing

## What's in the Attached Document

The attached `COMPLETE_ARCHITECTURE_DIAGRAM.md` includes:

1. **OIDC Authentication Chain** - Step-by-step breakdown of security flow
2. **High-Level Architecture Diagram** - Visual representation of all components
3. **Detailed Component Flows** - How each service interacts
4. **Authentication Flow Detail** - Deep dive into JWT token lifecycle
5. **Data Flow Timeline** - Timestamp-based progression through the system
6. **Component Summary Table** - Quick reference for all services
7. **Configuration URLs** - Direct links to GCP and AWS consoles

## Current Status

✅ **Deployed and Operational**
✅ **Successfully tested end-to-end**
✅ **Security validated** (JWT verification working)
✅ **Monitoring in place** (CloudWatch logs capturing all events)

## Next Steps / Recommendations

1. Review the architecture diagram for completeness
2. Validate security posture aligns with organizational policies
3. Consider API Gateway migration for enhanced features
4. Configure CloudWatch alarms for Lambda failures
5. Set up Portal26 dashboards for agent observability

## Questions?

Please review the attached architecture diagram and let me know if you need:
- Additional details on any component
- Security review from InfoSec team
- Cost analysis for production scale
- Performance optimization recommendations
- Alternative deployment options

---

**Attachments:**
- `COMPLETE_ARCHITECTURE_DIAGRAM.md` - Full technical architecture documentation

**Related Files:**
- `lambda_with_oidc_simple.py` - AWS Lambda function code
- `setup_gcp_oidc.sh` - GCP configuration script
- `oidc_lambda_config.txt` - Lambda configuration reference

---

**Best regards,**  
[Your Name]  
[Your Title]

---

**Quick Links:**
- GCP Vertex AI Agent: https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/8213677864684355584
- GCP Pub/Sub Subscription: https://console.cloud.google.com/cloudpubsub/subscription/detail/reasoning-engine-to-oidc?project=agentic-ai-integration-490716
- AWS Lambda Function: https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/gcp-pubsub-oidc
