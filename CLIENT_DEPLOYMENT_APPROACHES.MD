# Client Deployment Approaches for Portal26 Telemetry

This document outlines different approaches for deploying telemetry integration in client projects to send data to Portal26.

---

## 📊 Overview of Approaches

| Approach | Complexity | Setup Time | Production Ready | Best For |
|----------|-----------|------------|------------------|----------|
| **1. Direct OTEL Export** | Low | 5 mins | ⚠️ Limited | Quick testing |
| **2. Local Worker + Ngrok** | Medium | 15 mins | ❌ No | Development/debugging |
| **3. Cloud Run Worker** | High | 30 mins | ✅ Yes | Production deployments |
| **4. Terraform IaC** | High | 45 mins | ✅ Yes | Multi-tenant production |

---

## 🔐 Required Permissions (All Approaches)

### GCP Permissions

#### Developer/Admin User
```bash
# Required for all approaches
roles/aiplatform.user           # Deploy and manage agents
roles/logging.admin             # Create log sinks
roles/iam.serviceAccountAdmin   # Create service accounts
roles/storage.admin             # Manage GCS buckets for agent packages
```

#### Service Accounts (Created During Setup)

**Telemetry Worker Service Account**
```bash
# Automatically gets these roles:
roles/cloudtrace.user          # Read traces from client project
roles/logging.logWriter        # Write logs (optional)
roles/pubsub.subscriber        # Pull messages from Pub/Sub
```

**Log Sink Service Account (Auto-created)**
```bash
# Automatically created by Cloud Logging when you create a sink
# Format: service-<PROJECT_NUMBER>@gcp-sa-logging.iam.gserviceaccount.com

# Needs this role:
roles/pubsub.publisher         # Publish logs to Pub/Sub topic
```

### AWS Permissions (For Data Verification)

If pulling telemetry data from Portal26's Kinesis stream:

**IAM Policy Required:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "KinesisReadAccess",
      "Effect": "Allow",
      "Action": [
        "kinesis:GetRecords",
        "kinesis:GetShardIterator",
        "kinesis:DescribeStream",
        "kinesis:ListShards",
        "kinesis:DescribeStreamSummary"
      ],
      "Resource": "arn:aws:kinesis:us-east-2:473550159910:stream/stg_otel_source_data_stream"
    }
  ]
}
```

**Setup:**
```bash
# Option 1: AWS CLI (Recommended)
aws configure
# Enter: Access Key, Secret Key, Region (us-east-2)

# Option 2: Environment Variables (Development only)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-2
```

### Portal26 Endpoint Access

**No additional permissions needed** - Portal26 endpoint uses Basic Auth:
```bash
# Included in all .env configurations
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
```

---

## Approach 1: Direct OTEL Export from Agent

### Description
Agent directly exports OTEL telemetry to Portal26 endpoint using OpenTelemetry SDK.

### Architecture
```
Vertex AI Agent → OTEL SDK → Portal26 OTLP Endpoint
```

### Pros
- ✅ Simplest setup (5 minutes)
- ✅ No additional infrastructure
- ✅ Direct export, low latency
- ✅ Works for basic use cases

### Cons
- ⚠️ Limited trace correlation (no Cloud Trace integration)
- ⚠️ No centralized log aggregation
- ⚠️ Hard to debug (no local logs)
- ❌ Not suitable for production multi-tenant

### Setup Steps

#### 1. Configure Agent Environment
```python
# portal26_otel_agent/agent.py
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

endpoint = "https://otel-tenant1.portal26.in:4318/v1/traces"
exporter = OTLPSpanExporter(endpoint=endpoint)
```

#### 2. Set Environment Variables
```bash
# .env file
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_SERVICE_NAME=portal26_otel_agent
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
```

#### 3. Deploy Agent
```bash
cd portal26_otel_agent
python deploy.py
```

### When to Use
- Quick proof-of-concept
- Single-tenant testing
- Development environments
- When Cloud Trace integration is not needed

---

## Approach 2: Local Worker + Ngrok Tunnel

### Description
Run telemetry worker locally and expose via ngrok tunnel. Agent sends to ngrok URL which forwards to local worker.

### Architecture
```
Vertex AI Agent → Ngrok Tunnel → Local Worker → Cloud Trace API
                                            ↓
                                    Portal26 OTLP Endpoint
```

### Pros
- ✅ Easy debugging (local logs)
- ✅ Cloud Trace correlation
- ✅ Can test/modify worker code instantly
- ✅ Full telemetry pipeline testing

### Cons
- ❌ Requires ngrok running 24/7
- ❌ Not production-ready
- ⚠️ Ngrok tunnel can disconnect
- ⚠️ Single point of failure

### Setup Steps

#### 1. Start Ngrok Tunnel
```bash
ngrok http 8082
# Note the URL: https://xxx-yyy-zzz.ngrok-free.dev
```

#### 2. Configure Agent
```bash
# portal26_ngrok_agent/.env
OTEL_EXPORTER_OTLP_ENDPOINT=https://xxx-yyy-zzz.ngrok-free.dev
OTEL_SERVICE_NAME=portal26_ngrok_agent
```

#### 3. Run Local Worker
```bash
cd telemetry_worker_ngrok
python flask_fixed_8082.py
```

#### 4. Deploy Agent
```bash
cd portal26_ngrok_agent
python deploy.py
```

### When to Use
- Development and debugging
- Testing new telemetry features
- When you need to inspect live traffic
- Temporary deployments

---

## Approach 3: Cloud Run Production Worker

### Description
Deploy telemetry worker as Cloud Run service. Pub/Sub pushes logs to Cloud Run, worker processes and sends to Portal26.

### Architecture
```
Vertex AI Agent → Cloud Logging → Log Sink → Pub/Sub Topic
                                                    ↓
                                            Pub/Sub Subscription
                                                    ↓
                                            Cloud Run Worker
                                                    ↓
                                            Cloud Trace API → Portal26
```

### Pros
- ✅ Production-ready
- ✅ Auto-scaling
- ✅ No maintenance (serverless)
- ✅ Built-in monitoring
- ✅ Multi-tenant support

### Cons
- ⚠️ More complex setup (30 minutes)
- ⚠️ Requires CI/CD for updates
- ⚠️ Cold start latency
- 💰 Costs scale with usage

### Setup Steps

#### 1. Enable Required APIs
```bash
PROJECT_ID="your-project-id"

gcloud services enable \
  cloudtrace.googleapis.com \
  logging.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  --project=$PROJECT_ID
```

#### 2. Create Service Account
```bash
gcloud iam service-accounts create telemetry-worker \
  --display-name="Telemetry Worker" \
  --project=$PROJECT_ID

# Grant Cloud Trace User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:telemetry-worker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.user"
```

#### 3. Create Pub/Sub Topic & Subscription
```bash
# Create topic
gcloud pubsub topics create telemetry-logs \
  --project=$PROJECT_ID

# Create subscription
gcloud pubsub subscriptions create telemetry-processor \
  --topic=telemetry-logs \
  --ack-deadline=600 \
  --project=$PROJECT_ID

# Grant subscriber role to worker SA
gcloud pubsub subscriptions add-iam-policy-binding telemetry-processor \
  --member="serviceAccount:telemetry-worker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber" \
  --project=$PROJECT_ID
```

#### 4. Create Log Sink
```bash
# Get your Reasoning Engine ID
AGENT_ID="your-reasoning-engine-id"

# Create log sink
gcloud logging sinks create telemetry-sink \
  pubsub.googleapis.com/projects/${PROJECT_ID}/topics/telemetry-logs \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="'${AGENT_ID}'"' \
  --project=$PROJECT_ID

# Grant publisher permission to log sink SA
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud pubsub topics add-iam-policy-binding telemetry-logs \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-logging.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher" \
  --project=$PROJECT_ID
```

#### 5. Deploy to Cloud Run
```bash
cd telemetry_worker_ngrok

# Build and deploy
gcloud run deploy telemetry-worker \
  --source=. \
  --region=us-central1 \
  --service-account=telemetry-worker@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},PUBSUB_SUBSCRIPTION=telemetry-processor" \
  --allow-unauthenticated \
  --project=$PROJECT_ID
```

#### 6. Configure Pub/Sub to Push to Cloud Run
```bash
CLOUD_RUN_URL=$(gcloud run services describe telemetry-worker --region=us-central1 --format="value(status.url)" --project=$PROJECT_ID)

gcloud pubsub subscriptions modify telemetry-processor \
  --push-endpoint="${CLOUD_RUN_URL}/process" \
  --project=$PROJECT_ID
```

### When to Use
- Production deployments
- Multi-tenant environments
- When you need auto-scaling
- Serverless architecture preference

---

## Approach 4: Terraform Infrastructure as Code

### Description
Use Terraform to provision all infrastructure (Pub/Sub, Cloud Run, IAM, Log Sinks) and manage agent environment variables.

### Architecture
```
Terraform State
    ↓
Manages: Service Accounts, Pub/Sub, Cloud Run, Log Sinks, IAM Bindings
    ↓
Same flow as Approach 3 (Cloud Run Production)
```

### Pros
- ✅ Version-controlled infrastructure
- ✅ Repeatable deployments
- ✅ Multi-environment support (dev/staging/prod)
- ✅ Easy to add new clients/tenants
- ✅ Audit trail of changes

### Cons
- ⚠️ Requires Terraform knowledge
- ⚠️ Initial setup time (45 minutes)
- ⚠️ State management complexity
- ⚠️ Need CI/CD for automation

### Setup Steps

#### 1. Initialize Terraform
```bash
cd terraform
terraform init
```

#### 2. Configure Variables
```bash
# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id = "your-project-id"
region     = "us-central1"
environment = "production"

# Portal26 configuration
portal26_otel_endpoint = "https://otel-tenant1.portal26.in:4318"
portal26_otel_headers  = "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="

# Agent IDs (if already deployed)
portal26_ngrok_agent_id = "your-ngrok-agent-id"
portal26_otel_agent_id  = "your-otel-agent-id"

# Log sink filter
log_sink_filter = "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\""

# Cloud Run deployment
deploy_cloud_run = true
telemetry_worker_image = "gcr.io/your-project/telemetry-worker:latest"
EOF
```

#### 3. Review Plan
```bash
terraform plan
```

#### 4. Apply Infrastructure
```bash
terraform apply
```

This creates:
- Service accounts with correct IAM roles
- Pub/Sub topic and subscription
- Log sink with proper filters
- Cloud Run service (if enabled)
- Storage bucket for agent packages

#### 5. Deploy Agents
```bash
# Terraform creates .env files automatically
cd ../portal26_otel_agent
python deploy.py
```

### When to Use
- Production multi-tenant deployments
- When you need infrastructure versioning
- Multiple environments (dev/staging/prod)
- Team collaboration on infrastructure
- Compliance/audit requirements

---

## Comparison Matrix

### By Use Case

| Use Case | Recommended Approach | Alternative |
|----------|---------------------|-------------|
| Quick POC (< 1 hour) | Approach 1: Direct OTEL | Approach 2: Ngrok |
| Development/Debugging | Approach 2: Ngrok | Approach 1: Direct OTEL |
| Single Production Client | Approach 3: Cloud Run | Approach 4: Terraform |
| Multi-Tenant Production | Approach 4: Terraform | Approach 3: Cloud Run |
| Enterprise (>10 clients) | Approach 4: Terraform | - |

### By Feature

| Feature | Approach 1 | Approach 2 | Approach 3 | Approach 4 |
|---------|-----------|-----------|-----------|-----------|
| Cloud Trace Integration | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| Local Debugging | ❌ No | ✅ Yes | ⚠️ Logs only | ⚠️ Logs only |
| Auto-Scaling | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| Multi-Tenant | ⚠️ Manual | ⚠️ Manual | ✅ Yes | ✅ Yes |
| Infrastructure as Code | ❌ No | ❌ No | ⚠️ Partial | ✅ Yes |
| Cost (monthly) | $0 | $5 | $10-50 | $10-50 |
| Setup Time | 5 min | 15 min | 30 min | 45 min |

---

## Migration Path

### From Approach 1 → 3 (Direct OTEL to Cloud Run)
```bash
# 1. Set up Pub/Sub and Cloud Run (Approach 3 steps 1-6)
# 2. No agent code changes needed
# 3. Update .env to keep direct export OR switch to log sink
```

### From Approach 2 → 3 (Ngrok to Cloud Run)
```bash
# 1. Deploy Cloud Run worker
# 2. Update agent env var:
#    OLD: OTEL_EXPORTER_OTLP_ENDPOINT=https://xxx.ngrok-free.dev
#    NEW: Use log sink (no OTEL endpoint needed)
# 3. Redeploy agent
# 4. Stop ngrok tunnel
```

### From Approach 3 → 4 (Manual to Terraform)
```bash
# 1. Import existing resources:
terraform import google_pubsub_topic.telemetry_logs projects/PROJECT_ID/topics/telemetry-logs
terraform import google_pubsub_subscription.telemetry_processor projects/PROJECT_ID/subscriptions/telemetry-processor

# 2. Review terraform plan to ensure no deletions
terraform plan

# 3. Apply to bring under Terraform management
terraform apply
```

---

## Troubleshooting by Approach

### Approach 1 Issues

**Problem:** No telemetry appearing in Portal26

**Check:**
```bash
# 1. Verify endpoint is reachable
curl -I https://otel-tenant1.portal26.in:4318

# 2. Check agent logs
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND textPayload=~"OTEL"' \
  --limit=10 --project=PROJECT_ID

# 3. Test OTEL export locally
cd portal26_otel_agent
python agent.py
```

### Approach 2 Issues

**Problem:** Ngrok tunnel not working

**Check:**
```bash
# 1. Is ngrok running?
ps aux | grep ngrok

# 2. Test ngrok URL
curl https://your-ngrok-url.ngrok-free.dev/health

# 3. Check local worker logs
tail -f flask_fixed_8082.log
```

### Approach 3 Issues

**Problem:** Cloud Run not receiving messages

**Check:**
```bash
# 1. Check Pub/Sub has messages
gcloud pubsub subscriptions describe telemetry-processor --project=PROJECT_ID

# 2. Check Cloud Run logs
gcloud run logs read telemetry-worker --region=us-central1 --project=PROJECT_ID

# 3. Verify IAM permissions
gcloud pubsub subscriptions get-iam-policy telemetry-processor --project=PROJECT_ID
```

### Approach 4 Issues

**Problem:** Terraform apply fails

**Check:**
```bash
# 1. Check Terraform state
terraform state list

# 2. Validate configuration
terraform validate

# 3. Check for existing resources
gcloud pubsub topics list --project=PROJECT_ID
```

---

## Cost Estimates (Monthly)

| Approach | Compute | Storage | Network | Total |
|----------|---------|---------|---------|-------|
| Approach 1 | $0 | $0 | $0 | **$0** |
| Approach 2 | $5 (ngrok) | $0 | $0 | **$5** |
| Approach 3 | $10-30 (Cloud Run) | $1 (Pub/Sub) | $5 | **$16-36** |
| Approach 4 | $10-30 (Cloud Run) | $1 (Pub/Sub + State) | $5 | **$16-36** |

*Based on ~1M traces/month*

---

## Next Steps

1. **Choose your approach** based on the comparison matrix
2. **Review permission requirements** - ensure you have necessary roles
3. **Follow the setup steps** in the chosen approach section
4. **Test end-to-end** - verify telemetry in Portal26
5. **Monitor and optimize** - check logs and adjust as needed

For detailed setup instructions, see:
- `CLIENT_SETUP_GUIDE.md` - Detailed GCP setup
- `terraform/README.md` - Terraform specifics
- `ARCHITECTURE.md` - System architecture

---

## Support

**Issues?** Check:
1. This guide's troubleshooting section
2. `CLIENT_SETUP_GUIDE.md` for detailed GCP setup
3. Agent logs in GCP Console
4. Portal26 documentation

**Contact:**
- Portal26 Support: support@portal26.in
- Project Issues: Create issue in repository
