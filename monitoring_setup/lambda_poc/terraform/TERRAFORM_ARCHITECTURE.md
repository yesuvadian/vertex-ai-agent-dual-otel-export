# Terraform-Managed Architecture

## 🏗️ **Complete Infrastructure Diagram**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TERRAFORM MANAGES ALL THIS                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOOGLE CLOUD PLATFORM (GCP)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Vertex AI Reasoning Engines                                            │ │
│  │  (Not managed by Terraform - already exist)                             │ │
│  │  • Engine 1: 8213677864684355584                                        │ │
│  │  • Engine 2: 6010661182900273152                                        │ │
│  │  • Engine 3: 8019460130754002944                                        │ │
│  └────────────────────────────┬───────────────────────────────────────────┘ │
│                                │                                             │
│                                │ Auto-logs to Cloud Logging                  │
│                                ↓                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Cloud Logging                                                          │ │
│  │  (Not managed - GCP service)                                            │ │
│  │  • Captures all agent logs automatically                                │ │
│  │  • 30-day retention                                                     │ │
│  └────────────────────────────┬───────────────────────────────────────────┘ │
│                                │                                             │
│                                ↓                                             │
│  ╔════════════════════════════════════════════════════════════════════════╗ │
│  ║  LOG SINK: reasoning-engine-to-pubsub                                   ║ │
│  ║  [Terraform Resource: google_logging_project_sink]                      ║ │
│  ║  • Filter: reasoning_engine_id IN [id1, id2, id3]                       ║ │
│  ║  • Destination: Pub/Sub Topic                                           ║ │
│  ║  • Writer Identity: Auto-generated service account                      ║ │
│  ╚════════════════════════════┬═══════════════════════════════════════════╝ │
│                                │                                             │
│                                ↓                                             │
│  ╔════════════════════════════════════════════════════════════════════════╗ │
│  ║  PUB/SUB TOPIC: reasoning-engine-logs-topic                             ║ │
│  ║  [Terraform Resource: google_pubsub_topic]                              ║ │
│  ║  • Message retention: 7 days                                            ║ │
│  ║  • Labels: purpose=agent-observability                                  ║ │
│  ╚════════════════════════════┬═══════════════════════════════════════════╝ │
│                                │                                             │
│                                ↓                                             │
│  ╔════════════════════════════════════════════════════════════════════════╗ │
│  ║  PUB/SUB SUBSCRIPTION: reasoning-engine-to-oidc                         ║ │
│  ║  [Terraform Resource: google_pubsub_subscription]                       ║ │
│  ║  • Type: Push                                                           ║ │
│  ║  • Endpoint: AWS Lambda Function URL                                    ║ │
│  ║  • Attributes: shared_secret (from Secret Manager)                      ║ │
│  ║  • Ack deadline: 10 seconds                                             ║ │
│  ║  • Retry: Exponential backoff                                           ║ │
│  ╚════════════════════════════┬═══════════════════════════════════════════╝ │
│                                │                                             │
│                                │ Reads shared secret from ↓                  │
│  ╔════════════════════════════════════════════════════════════════════════╗ │
│  ║  SECRET MANAGER: aws-lambda-shared-secret                               ║ │
│  ║  [Terraform Resource: google_secret_manager_secret]                     ║ │
│  ║  • Secret: 64-character random string                                   ║ │
│  ║  • Access: Pub/Sub service account                                      ║ │
│  ╚════════════════════════════════════════════════════════════════════════╝ │
│                                │                                             │
│  ╔════════════════════════════════════════════════════════════════════════╗ │
│  ║  SERVICE ACCOUNT: pubsub-oidc-invoker                                   ║ │
│  ║  [Terraform Resource: google_service_account]                           ║ │
│  ║  • Role: serviceAccountTokenCreator                                     ║ │
│  ║  • Purpose: Authentication token generation                             ║ │
│  ╚════════════════════════════════════════════════════════════════════════╝ │
│                                                                              │
└──────────────────────────────┬───────────────────────────────────────────────┘
                               │
                               │ HTTPS POST with shared secret in attributes
                               │ Cross-cloud communication
                               ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AMAZON WEB SERVICES (AWS)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ╔════════════════════════════════════════════════════════════════════════╗ │
│  ║  LAMBDA FUNCTION: gcp-pubsub-multi-customer-processor                   ║ │
│  ║  [Terraform Resource: aws_lambda_function]                              ║ │
│  ║  • Runtime: Python 3.11                                                 ║ │
│  ║  • Memory: 512 MB                                                       ║ │
│  ║  • Timeout: 60 seconds                                                  ║ │
│  ║  • Code: lambda_multi_customer.py                                       ║ │
│  ║                                                                          ║ │
│  ║  Processing:                                                             ║ │
│  ║  1. Receives message from Pub/Sub                                       ║ │
│  ║  2. Verifies shared secret (from Secrets Manager) ──┐                   ║ │
│  ║  3. Identifies customer (project_id/engine_id)      │                   ║ │
│  ║  4. Consolidates logs → traces → metrics            │                   ║ │
│  ║  5. Routes based on size and customer               │                   ║ │
│  ╚════════════════════════════┬═══════════════════════┼═══════════════════╝ │
│                                │                       │                     │
│                                │                       │ Reads secret        │
│  ╔════════════════════════════┼═══════════════════════┼═══════════════════╗ │
│  ║  SECRETS MANAGER: gcp-pubsub-shared-secret         │                   ║ │
│  ║  [Terraform Resource: aws_secretsmanager_secret]   │                   ║ │
│  ║  • Secret: Same 64-char string as GCP ◀────────────┘                   ║ │
│  ║  • Access: Lambda execution role                                        ║ │
│  ╚════════════════════════════════════════════════════════════════════════╝ │
│                                │                                             │
│  ╔════════════════════════════┼═══════════════════════════════════════════╗ │
│  ║  LAMBDA FUNCTION URL                               │                   ║ │
│  ║  [Terraform Resource: aws_lambda_function_url]     │                   ║ │
│  ║  • URL: https://...lambda-url.us-east-1.on.aws/    │                   ║ │
│  ║  • Auth: NONE (handled in code)                    │                   ║ │
│  ╚════════════════════════════┼═══════════════════════════════════════════╝ │
│                                │                                             │
│  ╔════════════════════════════┼═══════════════════════════════════════════╗ │
│  ║  IAM ROLE: Lambda execution role                   │                   ║ │
│  ║  [Terraform Resource: aws_iam_role]                │                   ║ │
│  ║  • Permissions: S3, Kinesis, Secrets Manager, Logs │                   ║ │
│  ╚════════════════════════════┼═══════════════════════════════════════════╝ │
│                                │                                             │
│                                ↓ Routes based on size and customer           │
│                ┌───────────────┴───────────────┬──────────────┐             │
│                │                               │              │             │
│                ↓                               ↓              ↓             │
│  ╔═══════════════════════════╗  ╔═══════════════════════════╗  ╔══════════╗ │
│  ║  S3 BUCKETS               ║  ║  KINESIS STREAMS          ║  ║  OTEL    ║ │
│  ║  [Per Customer]           ║  ║  [Per Customer]           ║  ║ Endpoint ║ │
│  ║  ┌─────────────────────┐  ║  ║  ┌─────────────────────┐  ║  ║          ║ │
│  ║  │ customer1-traces    │  ║  ║  │ customer1-stream    │  ║  ║ Portal26 ║ │
│  ║  │ [aws_s3_bucket]     │  ║  ║  │ [aws_kinesis_stream]│  ║  ║ (External│ │
│  ║  │ • Large traces      │  ║  ║  │ • All traces        │  ║  ║  service)║ │
│  ║  │ • ≥ 100 KB          │  ║  ║  │ • Real-time         │  ║  ║ • Small  ║ │
│  ║  │ • Lifecycle: 90 days│  ║  ║  │ • Retention: 24h    │  ║  ║   traces ║ │
│  ║  └─────────────────────┘  ║  ║  └─────────────────────┘  ║  ║ • <100KB ║ │
│  ║  ┌─────────────────────┐  ║  ║  ┌─────────────────────┐  ║  ║          ║ │
│  ║  │ customer2-traces    │  ║  ║  │ customer2-stream    │  ║  ║          ║ │
│  ║  └─────────────────────┘  ║  ║  └─────────────────────┘  ║  ║          ║ │
│  ║  ┌─────────────────────┐  ║  ║  ┌─────────────────────┐  ║  ║          ║ │
│  ║  │ default-traces      │  ║  ║  │ default-stream      │  ║  ║          ║ │
│  ║  └─────────────────────┘  ║  ║  └─────────────────────┘  ║  ║          ║ │
│  ╚═══════════════════════════╝  ╚═══════════════════════════╝  ╚══════════╝ │
│                                                                              │
│  ╔════════════════════════════════════════════════════════════════════════╗ │
│  ║  CLOUDWATCH LOG GROUP                                                   ║ │
│  ║  [Terraform Resource: aws_cloudwatch_log_group]                         ║ │
│  ║  • Name: /aws/lambda/gcp-pubsub-multi-customer-processor                ║ │
│  ║  • Retention: 30 days                                                   ║ │
│  ║  • Logs: Lambda execution, authentication, routing                      ║ │
│  ╚════════════════════════════════════════════════════════════════════════╝ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         TERRAFORM STATE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Tracks all resource IDs, ARNs, attributes                                │
│  • Recommended: Store in GCS or S3 (remote backend)                         │
│  • Version controlled, encrypted                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 **Terraform Resource Mapping**

### **GCP Resources**

| Terraform Resource | Resource Name | Purpose |
|-------------------|---------------|---------|
| `google_logging_project_sink.reasoning_engine_to_pubsub` | `reasoning-engine-to-pubsub` | Filters and forwards logs |
| `google_pubsub_topic.reasoning_engine_logs` | `reasoning-engine-logs-topic` | Message queue |
| `google_pubsub_subscription.reasoning_engine_to_oidc` | `reasoning-engine-to-oidc` | Push subscription |
| `google_service_account.pubsub_oidc_invoker` | `pubsub-oidc-invoker@...` | Service account for auth |
| `google_secret_manager_secret.aws_shared_secret` | `aws-lambda-shared-secret` | Stores shared secret |
| `google_project_iam_member.pubsub_token_creator` | N/A | IAM binding |
| `google_pubsub_topic_iam_member.log_sink_publisher` | N/A | IAM binding |

### **AWS Resources**

| Terraform Resource | Resource Name | Purpose |
|-------------------|---------------|---------|
| `aws_lambda_function.multi_customer_processor` | `gcp-pubsub-multi-customer-processor` | Processes logs |
| `aws_lambda_function_url.multi_customer_url` | N/A | Public endpoint |
| `aws_iam_role.lambda_execution_role` | `gcp-pubsub-multi-customer-processor-role` | Lambda IAM role |
| `aws_s3_bucket.customer_traces[*]` | `portal26-{customer}-traces` | Trace storage |
| `aws_kinesis_stream.customer_streams[*]` | `portal26-{customer}-stream` | Real-time streaming |
| `aws_secretsmanager_secret.gcp_shared_secret` | `gcp-pubsub-shared-secret` | Stores shared secret |
| `aws_cloudwatch_log_group.lambda_logs` | `/aws/lambda/...` | Lambda execution logs |
| `random_password.shared_secret` | N/A | Generates secret |

---

## 🔄 **Data Flow Through Infrastructure**

```
1. Agent Logs
   └─ Vertex AI → Cloud Logging (automatic)

2. Log Filtering
   └─ Log Sink filters by engine_id → forwards to Pub/Sub

3. Message Queueing
   └─ Pub/Sub Topic → stores messages (7 days retention)

4. Authentication Preparation
   └─ Pub/Sub Subscription reads shared_secret from Secret Manager
   └─ Adds secret to message attributes

5. Cross-Cloud Delivery
   └─ Pub/Sub HTTPS POST → AWS Lambda Function URL
   └─ Headers: Content-Type, Authorization metadata
   └─ Body: Base64-encoded log data
   └─ Attributes: shared_secret, customer_id

6. Lambda Processing
   └─ Receives POST request
   └─ Reads shared_secret from AWS Secrets Manager
   └─ Verifies secret matches (constant-time comparison)
   └─ Identifies customer (project_id → customer mapping)
   └─ Consolidates: logs → traces → metrics

7. Routing Decision
   └─ Check data size:
      • < 100 KB → OTEL endpoint (Portal26)
      • ≥ 100 KB → S3 bucket (customer-specific)
      • All sizes → Kinesis stream (customer-specific)

8. Destination Delivery
   └─ OTEL: HTTPS POST to Portal26 endpoint
   └─ S3: Put object to customer bucket
   └─ Kinesis: Put record to customer stream

9. Monitoring
   └─ CloudWatch Logs: Lambda execution logs
   └─ CloudWatch Metrics: Invocations, errors, duration
```

---

## 🎯 **What Terraform Manages vs. What It Doesn't**

### ✅ **Terraform MANAGES**

```
GCP:
├── Log Sink (creation, filter, destination)
├── Pub/Sub Topic (creation, retention)
├── Pub/Sub Subscription (creation, push config)
├── Service Account (creation, roles)
├── Secret Manager (creation, value)
└── IAM Bindings (permissions)

AWS:
├── Lambda Function (creation, code, config)
├── Lambda Function URL (creation)
├── IAM Role (creation, policies)
├── S3 Buckets (creation, lifecycle, versioning)
├── Kinesis Streams (creation, shards)
├── Secrets Manager (creation, value)
└── CloudWatch Log Group (creation, retention)

Security:
└── Shared Secret (generation, storage in both clouds)
```

### ❌ **Terraform DOES NOT Manage**

```
GCP:
├── Vertex AI Reasoning Engines (pre-existing)
├── Cloud Logging service (GCP managed service)
├── Actual log data (runtime data)
└── Pub/Sub messages (runtime data)

AWS:
├── Portal26 service (external)
├── Lambda invocations (runtime)
├── Actual trace data in S3 (runtime data)
├── Actual stream data in Kinesis (runtime data)
└── CloudWatch log streams (created at runtime)

Runtime:
├── Log content (generated by agents)
├── Trace data (extracted by Lambda)
├── Metrics (calculated by Lambda)
└── Authentication tokens (generated at runtime)
```

---

## 🔄 **Terraform Lifecycle**

```
terraform init
      ↓
  Download providers (Google, AWS, Random)
  Initialize backend (local or remote)
      ↓
terraform plan
      ↓
  Read current state
  Compare with desired state
  Calculate diff (resources to create/update/delete)
  Show execution plan
      ↓
terraform apply
      ↓
  ┌─ GCP Resources (parallel where possible)
  │  ├─ Create Service Account
  │  ├─ Create Secret Manager secret
  │  ├─ Create Pub/Sub Topic
  │  ├─ Grant IAM permissions
  │  ├─ Create Pub/Sub Subscription (needs topic)
  │  └─ Create Log Sink (needs topic)
  │
  ├─ AWS Resources (parallel where possible)
  │  ├─ Create Secrets Manager secret
  │  ├─ Create IAM Role
  │  ├─ Create Lambda Function (needs role)
  │  ├─ Create Lambda Function URL (needs function)
  │  ├─ Create S3 Buckets (parallel)
  │  ├─ Create Kinesis Streams (parallel)
  │  └─ Create CloudWatch Log Group
  │
  └─ Update State File
      ↓
  Infrastructure Ready!
      ↓
terraform output
      ↓
  Display Lambda URL, bucket names, etc.
```

---

## 💾 **Terraform State File**

### **What's Stored**

```json
{
  "version": 4,
  "terraform_version": "1.5.0",
  "resources": [
    {
      "type": "google_pubsub_topic",
      "name": "reasoning_engine_logs",
      "provider": "google",
      "instances": [{
        "attributes": {
          "id": "projects/PROJECT_ID/topics/reasoning-engine-logs-topic",
          "name": "reasoning-engine-logs-topic",
          ...
        }
      }]
    },
    {
      "type": "aws_lambda_function",
      "name": "multi_customer_processor",
      "provider": "aws",
      "instances": [{
        "attributes": {
          "arn": "arn:aws:lambda:us-east-1:...",
          "function_name": "gcp-pubsub-multi-customer-processor",
          ...
        }
      }]
    }
  ]
}
```

### **Why It Matters**

- Tracks resource IDs, ARNs, attributes
- Enables updates without recreating everything
- Detects drift (manual changes)
- Enables collaboration (shared state)

### **Best Practice: Remote Backend**

```hcl
terraform {
  backend "gcs" {
    bucket = "terraform-state-bucket"
    prefix = "observability/state"
  }
}
```

---

This diagram shows the **complete infrastructure** that Terraform creates and manages across GCP and AWS!
