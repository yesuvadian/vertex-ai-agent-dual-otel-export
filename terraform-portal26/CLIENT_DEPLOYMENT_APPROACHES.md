# Client Deployment Approaches

There are TWO ways clients can use this Portal 26 integration:

## Approach 1: One-Time Injection (Recommended for Most Clients)

**Best for**: Clients who want to commit the modified code and manage it themselves.

### Workflow

#### Step 1: Initial Setup (One Time Only)

```bash
# Client runs injection test to get modified code
python scripts/test_injection_with_output.py \
  --source-dir "./my_agent" \
  --output-dir "./my_agent_with_portal26" \
  --portal26-endpoint "https://portal26.example.com/client-x" \
  --service-name "my-service"
```

#### Step 2: Review and Commit

```bash
cd my_agent_with_portal26

# Review changes
diff agent_original.py agent.py

# If satisfied, commit to version control
git add agent.py otel_portal26.py
git commit -m "Add Portal 26 telemetry integration"
git push
```

#### Step 3: Deploy Normally (No Terraform Injection Needed)

```bash
# Use standard Vertex AI deployment
python deploy_agent.py  # Or whatever their normal process is
```

### Files in Repository After Commit

```
my_agent/
├── agent.py              ← Modified (has "import otel_portal26")
├── otel_portal26.py      ← Added (Portal 26 module)
├── requirements.txt      ← Updated with OTEL dependencies
└── .env                  ← Environment variables for Portal 26
```

### Benefits

✅ **No Terraform needed** - Deploy with any method  
✅ **Version controlled** - Changes tracked in git  
✅ **Transparent** - Team sees exactly what's deployed  
✅ **Simpler CI/CD** - Standard deployment pipeline works  
✅ **One-time setup** - Never run injection again  

### Trade-offs

❌ **Manual updates** - If `otel_portal26.py` updates, must manually copy new version  
❌ **Code modified** - `agent.py` permanently changed (minimal impact)  

---

## Approach 2: Automatic Injection (Advanced)

**Best for**: Clients managing many agents, want centralized OTEL management.

### Workflow

#### Step 1: Keep Original Code

```
my_agent/
├── agent.py              ← Original (NO otel import)
├── requirements.txt      ← Original dependencies only
└── [other files]
```

**Important**: `agent.py` does NOT have `import otel_portal26` line.

#### Step 2: Configure Terraform

```hcl
# terraform.tfvars
agents = {
  "my-agent" = {
    source_dir   = "./my_agent"      # Points to ORIGINAL code
    display_name = "My Agent"
  }
}
```

#### Step 3: Terraform Injects Every Time

```bash
terraform apply
```

**What happens**:
1. Terraform copies original agent
2. Terraform injects `otel_portal26.py`
3. Terraform adds import line to `agent.py`
4. Terraform deploys modified version
5. Original files remain unchanged

### Benefits

✅ **Original code clean** - No OTEL in source  
✅ **Centralized management** - Update `otel_portal26.py` once, all agents get it  
✅ **Easy OTEL updates** - Just update module, redeploy  
✅ **Separation of concerns** - Agent logic separate from observability  

### Trade-offs

❌ **Terraform required** - Must use Terraform for all deployments  
❌ **Less transparent** - Deployed code differs from repository  
❌ **CI/CD complexity** - Must integrate Terraform  

---

## Comparison Table

| Feature | Approach 1: One-Time | Approach 2: Automatic |
|---------|---------------------|----------------------|
| **Complexity** | Low | Medium |
| **Setup time** | 5 minutes | 15 minutes |
| **Deployment** | Any method | Terraform only |
| **OTEL updates** | Manual copy | Automatic |
| **Code in repo** | Modified | Original |
| **CI/CD** | Standard | Terraform-based |
| **Best for** | Simple setups | Many agents |

---

## Recommendation by Use Case

### Use Approach 1 (One-Time) If:

- ✅ Client has 1-5 agents
- ✅ Client prefers simple deployments
- ✅ Client wants code transparency
- ✅ Client doesn't use Terraform
- ✅ OTEL updates are infrequent

### Use Approach 2 (Automatic) If:

- ✅ Client has 10+ agents
- ✅ Client already uses Terraform
- ✅ Client wants centralized OTEL management
- ✅ Client separates infra from code
- ✅ OTEL updates are frequent

---

## Detailed Guide: Approach 1 (One-Time Injection)

### Step-by-Step for Clients

#### 1. Run Injection Locally

```bash
cd terraform-portal26

python scripts/test_injection_with_output.py \
  --source-dir "/path/to/my_agent" \
  --output-dir "/path/to/my_agent_modified" \
  --portal26-endpoint "https://portal26.yourcompany.com/client-name" \
  --service-name "my-agents"
```

#### 2. Review Output

```bash
cd /path/to/my_agent_modified

# See what changed
cat README.txt

# Compare original vs modified
diff agent_original.py agent.py

# Should see ONE line added:
# +import otel_portal26  # Portal 26 telemetry
```

#### 3. Copy Files Back to Original Location

```bash
# Copy modified agent back
cp agent.py /path/to/my_agent/agent.py

# Copy OTEL module
cp otel_portal26.py /path/to/my_agent/otel_portal26.py

# Update requirements (add OTEL dependencies)
cat >> /path/to/my_agent/requirements.txt <<EOF
opentelemetry-instrumentation-google-genai>=0.4b0
opentelemetry-exporter-otlp-proto-http
opentelemetry-instrumentation-vertexai>=2.0b0
EOF
```

#### 4. Create Environment Variables File

```bash
cd /path/to/my_agent

# Create .env file for Portal 26 config
cat > .env.portal26 <<EOF
OTEL_EXPORTER_OTLP_ENDPOINT=https://portal26.yourcompany.com/client-name
OTEL_SERVICE_NAME=my-agents
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
GOOGLE_GENAI_USE_VERTEXAI=true
EOF
```

#### 5. Commit to Version Control

```bash
cd /path/to/my_agent

git status
# Shows:
#   modified: agent.py
#   new file: otel_portal26.py
#   modified: requirements.txt
#   new file: .env.portal26

git add agent.py otel_portal26.py requirements.txt .env.portal26

git commit -m "Add Portal 26 telemetry integration

- Added import otel_portal26 to agent.py
- Added otel_portal26.py module
- Updated requirements.txt with OTEL dependencies
- Added .env.portal26 with Portal 26 configuration
"

git push origin main
```

#### 6. Deploy (Standard Method)

Client can now use their **normal deployment process**:

**Option A: Using Vertex AI SDK directly**
```python
# deploy.py
import vertexai
from vertexai import agent_engines
import os
from dotenv import load_dotenv

# Load Portal 26 config
load_dotenv('.env.portal26')

# Import agent
from agent import root_agent

# Deploy
vertexai.init(project="my-project", location="us-central1")

deployed = agent_engines.create(
    agent_engine=root_agent,
    extra_packages=["."],  # Includes otel_portal26.py
    requirements=[
        "google-adk>=1.17.0",
        # OTEL deps from requirements.txt
    ],
    display_name="My Agent",
    env_vars=dict(os.environ)  # Includes Portal 26 config
)

print(f"Deployed: {deployed.resource_name}")
```

**Option B: Using gcloud CLI**
```bash
# Load Portal 26 env vars
export $(cat .env.portal26 | xargs)

# Deploy
gcloud ai agent-engines deploy \
  --agent-file=agent.py \
  --extra-packages=. \
  --env-vars-file=.env.portal26
```

**Option C: CI/CD Pipeline (GitHub Actions)**
```yaml
name: Deploy Agent

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Deploy to Vertex AI
        env:
          # Portal 26 config from GitHub Secrets
          OTEL_EXPORTER_OTLP_ENDPOINT: ${{ secrets.PORTAL26_ENDPOINT }}
          OTEL_SERVICE_NAME: ${{ secrets.PORTAL26_SERVICE_NAME }}
        run: python deploy.py
```

#### 7. Verify Telemetry

```bash
# Query the deployed agent
python query_agent.py AGENT_ID "test query"

# Check Portal 26 dashboard
# https://portal26.yourcompany.com/client-name/dashboard
```

---

## Updating OTEL Module (Approach 1)

When you release a new version of `otel_portal26.py`:

### Option A: Provide Update Script

```bash
# update_otel.sh (you provide to clients)
#!/bin/bash

AGENT_DIR=$1
NEW_OTEL_MODULE=$2

if [ -z "$AGENT_DIR" ] || [ -z "$NEW_OTEL_MODULE" ]; then
    echo "Usage: $0 <agent_dir> <new_otel_portal26.py>"
    exit 1
fi

# Backup old version
cp "$AGENT_DIR/otel_portal26.py" "$AGENT_DIR/otel_portal26.py.bak"

# Copy new version
cp "$NEW_OTEL_MODULE" "$AGENT_DIR/otel_portal26.py"

echo "Updated otel_portal26.py in $AGENT_DIR"
echo "Backup saved as otel_portal26.py.bak"
echo "Please redeploy your agent for changes to take effect"
```

Client runs:
```bash
./update_otel.sh ./my_agent ./otel_portal26_v2.py
git commit -am "Update OTEL module to v2"
# Redeploy agent
```

### Option B: Clients Pull from Git

```bash
# You maintain otel_portal26.py in a Git repo
# Clients add as submodule or fetch directly

cd my_agent
curl -O https://portal26.yourcompany.com/downloads/otel_portal26.py
git commit -am "Update OTEL module"
# Redeploy
```

---

## Summary

### For Most Clients: Use Approach 1

**Workflow**:
1. Run injection script once (5 minutes)
2. Commit modified code to git
3. Deploy using existing tools
4. Portal 26 telemetry flows automatically

**After initial setup**: Client never needs Terraform or injection scripts again!

### For Advanced Clients: Use Approach 2

**Workflow**:
1. Keep original code clean
2. Use Terraform for all deployments
3. Terraform injects OTEL automatically
4. Easy to update OTEL module centrally

---

## Questions?

**Q: Can we switch from Approach 1 to Approach 2 later?**  
A: Yes! Remove OTEL code from repository, configure Terraform.

**Q: Can we switch from Approach 2 to Approach 1?**  
A: Yes! Run injection once, commit result, stop using Terraform.

**Q: What if we don't want version control changes?**  
A: Use Approach 2 (automatic injection via Terraform).

**Q: What if we don't want Terraform dependency?**  
A: Use Approach 1 (one-time injection, commit result).
