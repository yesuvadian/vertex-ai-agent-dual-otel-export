# Quick Start: One-Time Injection (Commit and Deploy)

**For clients who want to commit the modified code and never run injection again.**

## 5-Minute Setup

### Step 1: Run Injection (One Time Only)

```bash
cd terraform-portal26

python scripts/test_injection_with_output.py \
  --source-dir "../your_agent" \
  --output-dir "../your_agent_with_portal26" \
  --portal26-endpoint "https://portal26.example.com/your-company" \
  --service-name "your-service-name"
```

**Output**:
```
[SUCCESS] INJECTION TEST COMPLETE
Output saved to: ../your_agent_with_portal26

Files created:
  - agent.py (modified)
  - agent_original.py (backup)
  - otel_portal26.py (Portal 26 module)
  - env_variables.txt (config)
  - requirements.txt
  - README.txt
```

### Step 2: Review Changes

```bash
cd ../your_agent_with_portal26

# Read the summary
cat README.txt

# See what changed (should be ONE line added)
diff agent_original.py agent.py
```

**Expected diff**:
```diff
"""
Your agent docstring
"""
+import otel_portal26  # Portal 26 telemetry
from google.adk.agents import Agent
```

### Step 3: Copy Files to Original Location

```bash
# Replace original agent with modified version
cp agent.py ../your_agent/agent.py

# Add OTEL module
cp otel_portal26.py ../your_agent/otel_portal26.py

# Create environment config
cp env_variables.txt ../your_agent/.env.portal26
```

### Step 4: Commit to Git

```bash
cd ../your_agent

git add agent.py otel_portal26.py .env.portal26
git commit -m "Add Portal 26 telemetry integration"
git push
```

### Step 5: Deploy (Your Normal Way)

**No Terraform needed!** Deploy however you normally deploy:

```bash
# Example: Direct Python deployment
python deploy_to_vertex.py

# Or: gcloud CLI
gcloud ai agents deploy --source=.

# Or: Your CI/CD pipeline
git push  # Triggers deployment
```

**Important**: Make sure your deployment sets the environment variables from `.env.portal26`

### Step 6: Verify Telemetry

```bash
# Test your agent
python query_agent.py AGENT_ID "test query"

# Check Portal 26 dashboard
# You should see traces, logs, and metrics!
```

---

## What Just Happened?

### Before (Original Code)
```python
# your_agent/agent.py
from google.adk.agents import Agent

def my_tool():
    return "result"

root_agent = Agent(...)
```

### After (Modified Code)
```python
# your_agent/agent.py
import otel_portal26  # Portal 26 telemetry  ← ADDED
from google.adk.agents import Agent

def my_tool():  # ← UNCHANGED
    return "result"

root_agent = Agent(...)  # ← UNCHANGED
```

### Files Added
```
your_agent/
├── agent.py              ← Modified (1 line added)
├── otel_portal26.py      ← New file
└── .env.portal26         ← New file
```

---

## Deploy With Environment Variables

Your deployment must include the Portal 26 configuration from `.env.portal26`:

### Method 1: Python Deployment

```python
# deploy.py
import os
from dotenv import load_dotenv
import vertexai
from vertexai import agent_engines

# Load Portal 26 config
load_dotenv('.env.portal26')

# Import your agent
from agent import root_agent

# Deploy with env vars
vertexai.init(project="your-project", location="us-central1")

deployed = agent_engines.create(
    agent_engine=root_agent,
    extra_packages=["."],  # Includes otel_portal26.py
    display_name="Your Agent",
    env_vars=dict(os.environ)  # ← Portal 26 config included
)

print(f"Deployed: {deployed.resource_name}")
```

### Method 2: Terraform (Simple Version)

```hcl
# main.tf
resource "google_vertex_ai_agent" "agent" {
  display_name = "Your Agent"
  source_dir   = "./your_agent"
  
  env_vars = {
    OTEL_EXPORTER_OTLP_ENDPOINT = "https://portal26.example.com/your-company"
    OTEL_SERVICE_NAME           = "your-service-name"
    OTEL_TRACES_EXPORTER        = "otlp"
    OTEL_METRICS_EXPORTER       = "otlp"
    OTEL_LOGS_EXPORTER          = "otlp"
    OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
    GOOGLE_GENAI_USE_VERTEXAI   = "true"
  }
}
```

### Method 3: GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy Agent

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vertex AI
        env:
          # Set these in GitHub Secrets
          OTEL_EXPORTER_OTLP_ENDPOINT: ${{ secrets.PORTAL26_ENDPOINT }}
          OTEL_SERVICE_NAME: ${{ secrets.PORTAL26_SERVICE }}
          OTEL_TRACES_EXPORTER: otlp
          OTEL_METRICS_EXPORTER: otlp
          OTEL_LOGS_EXPORTER: otlp
          OTEL_EXPORTER_OTLP_PROTOCOL: http/protobuf
          GOOGLE_GENAI_USE_VERTEXAI: true
        run: |
          python deploy.py
```

---

## Updating Your Agent Later

When you modify your agent code:

```bash
cd your_agent

# Edit your agent normally
vim agent.py

# Commit and deploy
git commit -am "Added new feature"
git push

# Deploy (Portal 26 still works!)
python deploy.py
```

**The `import otel_portal26` line stays in the code - don't remove it!**

---

## Updating OTEL Module (When We Release Updates)

If we release a new version of `otel_portal26.py`:

```bash
# We'll send you the new file
# Download: otel_portal26_v2.py

cd your_agent

# Backup old version
cp otel_portal26.py otel_portal26_v1_backup.py

# Copy new version
cp ~/Downloads/otel_portal26_v2.py otel_portal26.py

# Commit and redeploy
git commit -am "Update OTEL module to v2"
git push
python deploy.py
```

---

## Multiple Agents?

Repeat for each agent:

```bash
# Agent 1
python scripts/test_injection_with_output.py \
  --source-dir "../agent1" \
  --output-dir "../agent1_with_portal26" \
  --portal26-endpoint "https://portal26.example.com/your-company" \
  --service-name "your-service-name"

# Agent 2
python scripts/test_injection_with_output.py \
  --source-dir "../agent2" \
  --output-dir "../agent2_with_portal26" \
  --portal26-endpoint "https://portal26.example.com/your-company" \
  --service-name "your-service-name"

# Copy files and commit for each agent
```

**All agents share the same Portal 26 endpoint and service name.**

---

## Troubleshooting

### "Module otel_portal26 not found"

**Problem**: Deployment didn't include `otel_portal26.py`

**Solution**:
```python
# In deploy script, make sure to include current directory
agent_engines.create(
    agent_engine=root_agent,
    extra_packages=["."],  # ← Must include this
    ...
)
```

### "No telemetry appearing in Portal 26"

**Problem**: Environment variables not set

**Solution**: Check deployment logs for:
```
[OTEL] Initializing Portal 26 integration...
[OTEL] Endpoint: https://portal26.example.com/your-company
[OTEL] Service: your-service-name
```

If not present, environment variables weren't passed to deployment.

### "Portal 26 endpoint changed"

**Problem**: Need to update endpoint URL

**Solution**:
```bash
# Edit .env.portal26
vim .env.portal26
# Change OTEL_EXPORTER_OTLP_ENDPOINT

# Redeploy (no code changes needed)
python deploy.py
```

---

## Benefits of This Approach

✅ **Simple** - Run injection once, deploy normally forever  
✅ **Transparent** - Team sees exactly what's in production  
✅ **Standard tools** - Use your existing deployment process  
✅ **Version controlled** - Changes tracked in git  
✅ **No Terraform** - Not required for this approach  
✅ **CI/CD friendly** - Works with any pipeline  

---

## Summary

1. **Run injection once** → Get modified code
2. **Copy files back** → Update your repository
3. **Commit to git** → Track the changes
4. **Deploy normally** → Use your existing process
5. **Telemetry flows** → Appears in Portal 26 automatically

**You never need to run the injection script again!** ✅

The modified code is now your production code. Deploy it however you want - Terraform, Python, gcloud, CI/CD, anything works!

---

## Need Help?

- Review: `CLIENT_DEPLOYMENT_APPROACHES.md` for comparison with automatic approach
- Support: Contact Portal 26 support team
- Issues: Check that environment variables are set during deployment
