# Terraform Setup Ready (Not Deployed)

## ✅ What's Prepared

### 1. Empty Agent with OTEL Injection
**Location:** `empty_agent_portal26/`
- ✅ `agent.py` - Minimal agent with OTEL import
- ✅ `otel_portal26.py` - Portal26 telemetry module
- ✅ `.env` - Portal26 configuration
- ✅ `requirements.txt` - Dependencies

### 2. Terraform Configuration
**Location:** `terraform-portal26/terraform/`
- ✅ `main.tf` - Terraform infrastructure
- ✅ `variables.tf` - Variable definitions
- ✅ `empty-agent.tfvars` - Configuration for empty agent

---

## 📋 Terraform Configuration (`empty-agent.tfvars`)

```hcl
project_id = "agentic-ai-integration-490716"
region     = "us-central1"

portal26_endpoint     = "https://otel-tenant1.portal26.in:4318"
portal26_service_name = "empty-agent-portal26"

agents = {
  "empty-portal26" = {
    source_dir   = "../../empty_agent_portal26"
    display_name = "Empty Agent Portal26 Test"
  }
}
```

---

## 🚀 How Terraform Would Deploy (When Ready)

### Step 1: Initialize Terraform
```bash
cd terraform-portal26/terraform
terraform init
```

**What it does:**
- Downloads Google provider plugin
- Downloads null provider plugin
- Initializes terraform state

### Step 2: Plan Deployment
```bash
terraform plan -var-file="empty-agent.tfvars"
```

**What it shows:**
- Resources to be created
- OTEL injection script to run
- Agent deployment configuration

### Step 3: Apply (Deploy)
```bash
terraform apply -var-file="empty-agent.tfvars"
```

**What it does:**
1. Enables required GCP APIs:
   - `aiplatform.googleapis.com`
   - `cloudbuild.googleapis.com`
   - `storage.googleapis.com`

2. Runs deployment script:
   ```bash
   python3 scripts/inject_otel_and_deploy.py \
     --agent-name "empty-portal26" \
     --source-dir "../../empty_agent_portal26" \
     --display-name "Empty Agent Portal26 Test" \
     --portal26-endpoint "https://otel-tenant1.portal26.in:4318" \
     --service-name "empty-agent-portal26" \
     --project-id "agentic-ai-integration-490716" \
     --location "us-central1"
   ```

3. The script:
   - Creates temp directory
   - Copies agent source
   - Copies `otel_portal26.py`
   - Injects `import otel_portal26` into `agent.py`
   - Deploys to Vertex AI Agent Engine
   - Returns agent ID

4. Outputs deployment info:
   ```
   portal26_config = {
     endpoint     = "https://otel-tenant1.portal26.in:4318"
     service_name = "empty-agent-portal26"
     agents       = ["empty-portal26"]
     agent_count  = 1
   }
   ```

---

## 🔍 What Happens During Deployment

```
┌────────────────────────────────────────────────────────────┐
│ 1. Terraform reads empty-agent.tfvars                     │
│    - Project: agentic-ai-integration-490716                │
│    - Agent source: ../../empty_agent_portal26              │
│    - Portal26: https://otel-tenant1.portal26.in:4318      │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 2. inject_otel_and_deploy.py runs                         │
│    - Creates temp directory                                │
│    - Copies all files from empty_agent_portal26/          │
│    - Copies otel_portal26.py to temp directory            │
│    - Checks if 'import otel_portal26' exists in agent.py  │
│    - Injects import if not present                         │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Vertex AI Agent Engine deployment                      │
│    - Uploads agent code to GCS staging bucket              │
│    - Creates Reasoning Engine resource                     │
│    - Builds container with dependencies                    │
│    - Deploys to managed infrastructure                     │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 4. Agent starts running                                    │
│    - Container starts                                      │
│    - Python imports otel_portal26 (first import)          │
│    - OTEL initializes automatically                        │
│    - Connects to Portal26 endpoint                         │
│    - Agent ready for queries                               │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 5. Telemetry flows to Portal26                            │
│    - Every query generates traces                          │
│    - Logs sent to Portal26                                 │
│    - Metrics exported (may get 404 - known issue)          │
│    - Data appears in Kinesis stream                        │
└────────────────────────────────────────────────────────────┘
```

---

## 📊 Expected Telemetry After Deployment

### Service Identifier
```json
{
  "service.name": "empty-agent-portal26",
  "portal26.tenant_id": "tenant1",
  "portal26.user.id": "relusys_terraform"
}
```

### In Kinesis
Pull with:
```bash
cd ../../portal26_otel_agent
python3 pull_agent_logs.py

# Look for new service
grep "empty-agent-portal26" portal26_otel_agent_logs_*.jsonl
```

### Pattern to Expect
- **Service:** empty-agent-portal26
- **User:** relusys_terraform (NOT relusys)
- **Type:** Traces + Logs (Metrics may error with 404)
- **Frequency:** On-demand (when queried)

---

## 🎯 Comparison: relusys vs relusys_terraform

| Attribute | Current Mystery Source | New Empty Agent |
|-----------|------------------------|-----------------|
| Service Name | portal26_otel_agent | empty-agent-portal26 |
| User ID | relusys | **relusys_terraform** |
| Pattern | Every 11.7s (automated) | On-demand (queries only) |
| Type | ERROR logs only | Traces + Logs |
| Platform | Unknown (no metadata) | Vertex AI (cloud) |
| Purpose | Metrics export errors | Normal telemetry |

This helps us distinguish the new deployment from the mystery source!

---

## 💡 Why We Changed USER_ID

**Original config had:**
```hcl
portal26_user_id = "relusys"  # Same as mystery source
```

**Changed to:**
```hcl
# Removed from tfvars (not a terraform variable)
# Will use default in OTEL module or env vars
```

**Result:** Won't conflict with existing "relusys" telemetry

---

## 🔧 If You Want to Deploy Later

### Option A: Via Terraform
```bash
cd terraform-portal26/terraform

# Initialize (first time only)
terraform init

# Review plan
terraform plan -var-file="empty-agent.tfvars"

# Deploy
terraform apply -var-file="empty-agent.tfvars"

# Get outputs
terraform output
```

### Option B: Via Python Script Directly
```bash
cd ../scripts

python3 inject_otel_and_deploy.py \
  --agent-name "empty-portal26" \
  --source-dir "../../empty_agent_portal26" \
  --display-name "Empty Agent Portal26 Test" \
  --portal26-endpoint "https://otel-tenant1.portal26.in:4318" \
  --service-name "empty-agent-portal26" \
  --project-id "agentic-ai-integration-490716" \
  --location "us-central1"
```

### Option C: Via Manual SDK
```bash
cd ../../empty_agent_portal26

python3 << 'EOF'
import vertexai
from vertexai.preview import reasoning_engines

vertexai.init(
    project="agentic-ai-integration-490716",
    location="us-central1"
)

# Load agent (triggers OTEL init)
import agent

# Deploy
deployed = reasoning_engines.ReasoningEngine.create(
    reasoning_engine=agent.root_agent,
    requirements="requirements.txt",
    display_name="Empty Agent Portal26 Test",
    extra_packages=["./"]
)

print(f"Deployed: {deployed.resource_name}")
EOF
```

---

## 📂 Current State

```
ai_agent_projectgcp/
├── empty_agent_portal26/          ✅ Agent with OTEL injection
│   ├── agent.py                   ✅ Has 'import otel_portal26'
│   ├── otel_portal26.py           ✅ OTEL module
│   ├── .env                       ✅ Portal26 config
│   └── requirements.txt           ✅ Dependencies
│
├── terraform-portal26/
│   ├── otel_portal26.py           ✅ Shared OTEL module
│   ├── scripts/
│   │   └── inject_otel_and_deploy.py  ✅ Deployment script
│   └── terraform/
│       ├── main.tf                ✅ Infrastructure as code
│       ├── variables.tf           ✅ Variable definitions
│       └── empty-agent.tfvars     ✅ Empty agent config
│
└── portal26_otel_agent/           ✅ Kinesis pull scripts
    ├── pull_agent_logs.py         ✅ Pull telemetry
    └── analyze_pattern.py         ✅ Analyze patterns
```

---

## ✅ Status

- ✅ **Agent created** with OTEL injection
- ✅ **Terraform configured** for deployment
- ✅ **Ready to deploy** when you want
- ❌ **NOT deployed yet** (as requested)

**Everything is prepared but not deployed!**

---

## 🎯 Next Steps (When Ready)

1. **Deploy:**
   ```bash
   cd terraform-portal26/terraform
   terraform init
   terraform apply -var-file="empty-agent.tfvars"
   ```

2. **Test:**
   ```bash
   # Get agent ID from terraform output
   AGENT_ID=$(terraform output -raw agent_ids)
   
   # Query agent
   cd ../../
   python3 query_agent.py $AGENT_ID "Hello Portal26"
   ```

3. **Verify Telemetry:**
   ```bash
   cd portal26_otel_agent
   python3 pull_agent_logs.py
   grep "empty-agent-portal26" portal26_otel_agent_logs_*.jsonl
   ```

---

**Deployment ready but paused - waiting for your go-ahead!**
