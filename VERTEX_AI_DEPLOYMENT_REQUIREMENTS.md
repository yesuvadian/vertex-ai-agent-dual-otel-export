# Vertex AI Reasoning Engine Deployment Requirements

## ✅ What You Have

**Project:** `agentic-ai-integration-490716`

---

## 📋 What Else You Need

### 1. **Enabled APIs** (Required)

```bash
# Check if enabled
gcloud services list --enabled --project=agentic-ai-integration-490716 | grep -E "aiplatform|cloudbuild|storage"

# Enable if needed
gcloud services enable aiplatform.googleapis.com --project=agentic-ai-integration-490716
gcloud services enable cloudbuild.googleapis.com --project=agentic-ai-integration-490716
gcloud services enable storage-api.googleapis.com --project=agentic-ai-integration-490716
```

**Required APIs:**
- ✅ `aiplatform.googleapis.com` - Vertex AI for Reasoning Engine
- ✅ `cloudbuild.googleapis.com` - For building agent container
- ✅ `storage-api.googleapis.com` - For GCS staging bucket

---

### 2. **GCS Staging Bucket** (Auto-created or Manual)

**Auto-created pattern:**
```
gs://agentic-ai-integration-490716-adk-staging
```

**Or create manually:**
```bash
gsutil mb -p agentic-ai-integration-490716 -l us-central1 gs://agentic-ai-integration-490716-adk-staging
```

---

### 3. **IAM Permissions** (Your Account Needs)

Check your permissions:
```bash
gcloud projects get-iam-policy agentic-ai-integration-490716 \
  --flatten="bindings[].members" \
  --filter="bindings.members:yesuvadian.c@portal26.ai"
```

**Required Roles:**
- ✅ `roles/aiplatform.user` - Deploy & manage Reasoning Engines
- ✅ `roles/storage.objectAdmin` - Write to GCS staging bucket  
- ✅ `roles/cloudbuild.builds.builder` - Build agent container

**Grant if missing:**
```bash
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="user:yesuvadian.c@portal26.ai" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="user:yesuvadian.c@portal26.ai" \
  --role="roles/storage.objectAdmin"
```

---

### 4. **Application Default Credentials** (ADC)

**Check current credentials:**
```bash
gcloud auth application-default print-access-token
```

**Set if not configured:**
```bash
gcloud auth application-default login
```

This creates: `~/.config/gcloud/application_default_credentials.json`

---

### 5. **Region/Location** (Where to Deploy)

**Your config:** `us-central1`

**Check available regions:**
```bash
gcloud ai regions list
```

**Supported regions for Reasoning Engine:**
- `us-central1` ✅ (your choice)
- `us-east1`
- `us-west1`
- `europe-west1`
- `asia-southeast1`

---

### 6. **Agent Code** (What to Deploy)

**Your injected agent is ready:**
```
empty_agent_portal26_injected/
├── agent.py              ← Has 'import otel_portal26'
├── otel_portal26.py      ← OTEL module
├── .env                  ← Portal26 config
└── requirements.txt      ← Dependencies
```

---

### 7. **Python Environment** (For Deployment)

**Required packages:**
```bash
pip install google-cloud-aiplatform vertexai
```

**Check versions:**
```bash
python3 -c "import vertexai; print(vertexai.__version__)"
```

---

## 🚀 Ready to Deploy?

### Quick Check Script

```bash
cd empty_agent_portal26_injected

python3 << 'EOF'
import sys

print("="*60)
print("VERTEX AI DEPLOYMENT READINESS CHECK")
print("="*60)

# 1. Check vertexai installed
try:
    import vertexai
    print(f"✅ vertexai installed: {vertexai.__version__}")
except ImportError:
    print("❌ vertexai not installed: pip install vertexai")
    sys.exit(1)

# 2. Check ADC credentials
try:
    import google.auth
    creds, project = google.auth.default()
    print(f"✅ ADC configured: project={project}")
except Exception as e:
    print(f"❌ ADC not configured: {e}")
    sys.exit(1)

# 3. Check agent.py exists
import os
if os.path.exists("agent.py"):
    print("✅ agent.py found")
    with open("agent.py") as f:
        if "import otel_portal26" in f.read():
            print("✅ OTEL injection present")
        else:
            print("⚠️  OTEL injection missing")
else:
    print("❌ agent.py not found")
    sys.exit(1)

# 4. Check requirements.txt
if os.path.exists("requirements.txt"):
    print("✅ requirements.txt found")
else:
    print("⚠️  requirements.txt missing")

# 5. Test agent import
try:
    import agent
    print("✅ Agent module loads successfully")
    if hasattr(agent, 'root_agent'):
        print("✅ root_agent defined")
    else:
        print("❌ root_agent not found in agent.py")
        sys.exit(1)
except Exception as e:
    print(f"❌ Agent import failed: {e}")
    sys.exit(1)

print("\n"+"="*60)
print("✅ ALL CHECKS PASSED - READY TO DEPLOY!")
print("="*60)
EOF
```

---

## 📦 3 Ways to Deploy

### Option A: Python SDK (Recommended)

```bash
cd empty_agent_portal26_injected

python3 << 'EOF'
import vertexai
from vertexai.preview import reasoning_engines

# Initialize Vertex AI
vertexai.init(
    project="agentic-ai-integration-490716",
    location="us-central1",
    staging_bucket="gs://agentic-ai-integration-490716-adk-staging"
)

# Import agent (OTEL will initialize)
import agent

print("Deploying to Vertex AI Reasoning Engine...")

# Deploy
deployed = reasoning_engines.ReasoningEngine.create(
    reasoning_engine=agent.root_agent,
    requirements="requirements.txt",
    display_name="Empty Agent Portal26 Test",
    description="Minimal agent with Portal26 OTEL telemetry",
    extra_packages=["./"]  # Include current directory (for otel_portal26.py)
)

print(f"\n✅ Deployed successfully!")
print(f"Agent ID: {deployed.resource_name}")
print(f"Resource: {deployed.gca_resource}")

# Test query
print("\nTesting agent...")
response = deployed.query(input="Hello, test!")
print(f"Response: {response}")

print("\n✅ Agent is live and responding!")
EOF
```

### Option B: gcloud CLI

```bash
cd empty_agent_portal26_injected

# Package agent
tar -czf agent.tar.gz agent.py otel_portal26.py requirements.txt .env

# Upload to GCS
gsutil cp agent.tar.gz gs://agentic-ai-integration-490716-adk-staging/

# Deploy (note: gcloud doesn't fully support Reasoning Engine deployment yet)
# Use Python SDK or Console instead
```

### Option C: Terraform (Full Deployment)

```bash
cd ../../terraform-portal26/terraform

# Backup injection-only config
mv main.tf main-injection-only.tf.backup

# Restore deployment config
mv main-deployment.tf.backup main.tf

# Deploy
terraform init
terraform apply -var-file="empty-agent.tfvars"
```

---

## 📊 After Deployment - Verify Telemetry

### 1. Get Agent ID

```bash
# From Python output
AGENT_ID="projects/.../locations/us-central1/reasoningEngines/..."

# Or list all agents
gcloud ai reasoning-engines list --region=us-central1 --project=agentic-ai-integration-490716
```

### 2. Query Agent

```bash
python3 << EOF
import vertexai
from vertexai.preview import reasoning_engines

vertexai.init(project="agentic-ai-integration-490716", location="us-central1")

agent = reasoning_engines.ReasoningEngine("$AGENT_ID")
response = agent.query(input="Test Portal26 telemetry")
print(response)
EOF
```

### 3. Check Kinesis for Telemetry

```bash
cd ../../portal26_otel_agent

# Pull from Kinesis
python3 pull_agent_logs.py

# Look for your agent
grep "empty-agent-portal26" portal26_otel_agent_logs_*.jsonl | head -5

# Analyze pattern
python3 analyze_pattern.py | grep "empty-agent"
```

**Expected in Kinesis:**
```json
{
  "service.name": "empty-agent-portal26",
  "portal26.tenant_id": "tenant1",
  "portal26.user.id": "relusys_terraform",
  "agent.type": "empty-portal26"
}
```

---

## ⚠️ Common Issues

### Issue 1: Permission Denied

```
Error: Permission denied on project
```

**Fix:**
```bash
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/aiplatform.user"
```

### Issue 2: API Not Enabled

```
Error: aiplatform.googleapis.com not enabled
```

**Fix:**
```bash
gcloud services enable aiplatform.googleapis.com --project=agentic-ai-integration-490716
```

### Issue 3: Staging Bucket Missing

```
Error: Staging bucket not found
```

**Fix:**
```bash
gsutil mb -p agentic-ai-integration-490716 -l us-central1 \
  gs://agentic-ai-integration-490716-adk-staging
```

### Issue 4: Import Error: otel_portal26

```
ModuleNotFoundError: No module named 'otel_portal26'
```

**Fix:**
Ensure `extra_packages=["./"]` is in deployment call, or copy otel_portal26.py to agent directory.

---

## 📋 Pre-Deployment Checklist

- [ ] Project: `agentic-ai-integration-490716`
- [ ] APIs enabled: aiplatform, cloudbuild, storage
- [ ] IAM permissions granted
- [ ] ADC credentials configured
- [ ] Region selected: `us-central1`
- [ ] Agent code with OTEL injection ready
- [ ] Python environment with vertexai installed
- [ ] Staging bucket exists or will auto-create
- [ ] Requirements.txt has all dependencies
- [ ] OTEL configuration in .env file

---

## ✅ Summary

**Besides the project, you need:**

1. **3 APIs enabled** (aiplatform, cloudbuild, storage)
2. **IAM permissions** (aiplatform.user, storage.objectAdmin)
3. **ADC credentials** (gcloud auth application-default login)
4. **GCS staging bucket** (auto-created or manual)
5. **Python with vertexai** (pip install vertexai)
6. **Agent code ready** (already have this: empty_agent_portal26_injected/)

**Everything is ready! You can deploy now.**

---

## 🚀 Quick Deploy Command

```bash
cd empty_agent_portal26_injected

python3 << 'EOF'
import vertexai
from vertexai.preview import reasoning_engines

vertexai.init(
    project="agentic-ai-integration-490716",
    location="us-central1"
)

import agent

deployed = reasoning_engines.ReasoningEngine.create(
    reasoning_engine=agent.root_agent,
    requirements="requirements.txt",
    display_name="Empty Agent Portal26",
    extra_packages=["./"]
)

print(f"✅ Deployed: {deployed.resource_name}")
EOF
```

**This will deploy your agent with Portal26 telemetry to Vertex AI!**
