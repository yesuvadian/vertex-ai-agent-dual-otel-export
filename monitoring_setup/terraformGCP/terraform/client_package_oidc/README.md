# GCP Log Forwarding with OIDC Authentication - Complete Guide

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [What Gets Created](#what-gets-created)
- [Security Features](#security-features)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)

---

## Prerequisites

### Required:
- [ ] Terraform installed
- [ ] GCP Project with Reasoning Engines
- [ ] Service Account with **Editor**, **Logging Admin**, and **Cloud Trace User** roles ⚠️
- [ ] Destination endpoint URL (with OIDC validation enabled)
- [ ] **Reasoning Engine must log to Google Cloud Logging** ⚠️

### Files Needed:
- Service account key JSON file
- Destination endpoint URL
- Reasoning Engine IDs

### ⚠️ IMPORTANT: Reasoning Engine Requirements

**This setup ONLY works if your Reasoning Engine logs to Google Cloud Logging (default behavior).**

**Supported:**
- ✅ Reasoning Engines using Vertex AI Agent Builder SDK (default Cloud Logging)
- ✅ Reasoning Engines with standard Cloud Logging integration
- ✅ Default Vertex AI instrumentation

**NOT Supported:**
- ❌ Reasoning Engines with **custom OpenTelemetry (OTEL) exporters**
- ❌ Agents sending logs directly to external systems (bypassing Cloud Logging)
- ❌ Custom telemetry implementations that don't write to Cloud Logging

**How to verify:**
1. Go to: https://console.cloud.google.com/logs/query
2. Select your GCP project
3. Run query: `resource.labels.reasoning_engine_id="YOUR_ENGINE_ID"`
4. You should see logs appear when your Reasoning Engine runs
5. If no logs appear → Your setup uses custom OTEL and **this solution won't work**

### ⚠️ CRITICAL: Service Account Permissions

Your service account needs **THREE roles**:

1. **Editor** (`roles/editor`)
   - Create/modify Pub/Sub resources
   - Create service accounts

2. **Logging Admin** (`roles/logging.admin`) 
   - Create/modify log sinks
   - **Editor role does NOT include this!**

3. **Cloud Trace User** (`roles/cloudtrace.user`)
   - Collect trace/telemetry data from Reasoning Engine

**To add required roles:**

```bash
# Via gcloud CLI:
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:YOUR-SA@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:YOUR-SA@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/logging.admin"

gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:YOUR-SA@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.user"
```

Or via GCP Console:
1. Go to: IAM & Admin → IAM
2. Find your service account
3. Click **Edit** → **ADD ANOTHER ROLE**
4. Select: **Editor**
5. Click **ADD ANOTHER ROLE**
6. Select: **Logging Admin**
7. Click **ADD ANOTHER ROLE**
8. Select: **Cloud Trace User**
9. Click **SAVE**

---

## Quick Start

### Step 1: Get Service Account Key

**The included `appengine-sa-key.json` is an EXAMPLE only.**

Generate YOUR service account key:

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select YOUR GCP project
3. Click on your service account (with Editor + Logging Admin roles)
4. **KEYS** tab → **ADD KEY** → **Create new key** → **JSON**
5. **Replace** the example file with your downloaded key
6. Rename to: `appengine-sa-key.json`

### Step 2: Configure Terraform Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with YOUR values:

**Required:**
- `gcp_project_id` - YOUR GCP Project ID
- `customer_id` - YOUR Customer ID
- `reasoning_engine_ids` - YOUR Reasoning Engine IDs (list format)
- `aws_lambda_url` - YOUR destination endpoint URL

**How to get Reasoning Engine ID:**

1. Go to: https://console.cloud.google.com/vertex-ai/reasoning-engines
2. Select your project
3. Click on your Reasoning Engine
4. Copy the ID from the URL or details page
   - URL format: `.../reasoning-engines/REGION/REASONING_ENGINE_ID`
   - Example ID: `9162160575269044224`

**Example Configuration:**
```hcl
gcp_project_id = "my-gcp-project-123"
customer_id = "customer-001"
reasoning_engine_ids = ["9162160575269044224"]
aws_lambda_url = "https://your-endpoint-url.example.com"
```

### Step 3: Deploy Infrastructure

**Note:** Credentials are automatically loaded from `appengine-sa-key.json` (configured in `main.tf` provider block).

```bash
# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy
terraform apply
```

Type `yes` when Terraform asks to confirm.

---

## Deployment Complete

After deployment, Terraform will output:
- Service Account email (for OIDC)
- Pub/Sub Topic and Subscription names
- Log Sink name
- GCP Console links

---

## What Gets Created

In YOUR GCP project:

### 1. Service Account
- **Name**: `pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com`
- **Purpose**: Generates OIDC tokens for authentication
- **Permissions**: Token Creator role (automatically managed by GCP Pub/Sub)

### 2. Pub/Sub Topic
- **Name**: `portal26-telemetry-{customer-id}`
- **Purpose**: Receives logs from Log Sink
- **Retention**: 7-day message retention

### 3. Pub/Sub Subscription
- **Name**: `portal26-telemetry-sub-{customer-id}`
- **Purpose**: Pushes to destination endpoint with OIDC token
- **Features**: Automatic retry on failure

### 4. Log Sink
- **Name**: `portal26-sink-{customer-id}`
- **Purpose**: Routes Reasoning Engine logs
- **Default Filter**: Captures Reasoning Engine and Vertex AI agent logs
  - `resource.type="aiplatform.googleapis.com/ReasoningEngine"`
  - `logName=~"gen_ai\."`
  - `labels.agent_engine=true`
  - `jsonPayload.source="vertex-ai-agent"`

---

---

---

## Cleanup

To remove all created resources:

```bash
terraform destroy
```

Type `yes` when prompted to confirm.

This will remove:
- Service account (`pubsub-oidc-invoker`)
- Pub/Sub subscription and topic
- Log sink
- All IAM bindings

---

---

## 📚 Files in This Package

| File | Purpose |
|------|---------|
| `README.md` | This guide - complete setup instructions |
| `main.tf` | Terraform variables, provider, and outputs |
| `gcp_log_sink_pubsub_oidc.tf` | GCP infrastructure definitions |
| `terraform.tfvars.example` | Configuration template |
| `appengine-sa-key.json` | Service account key (EXAMPLE - replace with yours) |

---

