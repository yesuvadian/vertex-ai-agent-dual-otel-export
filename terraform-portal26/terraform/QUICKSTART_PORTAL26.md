# Quick Start: Portal 26 Integration for Vertex AI Agent Engine

Complete guide to enable Portal 26 telemetry for existing Vertex AI agents using Terraform.

## What This Does

- ✅ Injects OTEL module into your agents (no manual code changes)
- ✅ Deploys to Vertex AI Agent Engine with Portal 26 configuration
- ✅ Manages multi-client deployments via Terraform
- ✅ All telemetry (traces/logs/metrics) → Portal 26
- ❌ **No Cloud Run** - Pure Vertex AI Agent Engine solution

## Prerequisites

1. Python 3.10+
2. Terraform >= 1.5
3. GCP credentials configured (`gcloud auth application-default login`)
4. Portal 26 endpoint URL
5. Agent source code accessible locally

## Quick Start (5 Minutes)

### 1. Configure Portal 26

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
project_id = "your-project-id"

# Portal 26 endpoint
portal26_endpoint     = "https://portal26.example.com"
portal26_service_name = "my-agents"

# Your agents
agents = {
  "my-agent" = {
    source_dir   = "../my_agent"  # Path to agent source
    display_name = "My Agent"
  }
}
```

### 2. Deploy with Terraform

```bash
terraform init
terraform apply
```

### 3. Verify in Portal 26

Query your agent:

```bash
cd ..
python3 query_agent.py AGENT_ID "test query"
```

Check Portal 26 dashboard for traces, logs, and metrics!

## What Happens Behind the Scenes

```
1. Terraform triggers deployment
   ↓
2. Python script copies agent source
   ↓
3. Injects otel_portal26.py module
   ↓
4. Adds "import otel_portal26" to agent.py
   ↓
5. Deploys to Vertex AI Agent Engine
   ↓
6. Agent starts, OTEL auto-initializes
   ↓
7. Telemetry flows to Portal 26
```

## Multi-Client Setup

### Client A

```bash
# Create client config
cat > terraform/clients/client-a.tfvars <<EOF
project_id            = "client-a-project"
portal26_endpoint     = "https://portal26.example.com/client-a"
portal26_service_name = "client-a-agents"

agents = {
  "support" = {
    source_dir   = "/path/to/client-a/support_agent"
    display_name = "Support Agent"
  }
}
EOF

# Deploy
terraform apply -var-file="clients/client-a.tfvars"
```

### Client B

```bash
# Create client config
cat > terraform/clients/client-b.tfvars <<EOF
project_id            = "client-b-project"
portal26_endpoint     = "https://portal26.example.com/client-b"
portal26_service_name = "client-b-agents"

agents = {
  "helpdesk" = {
    source_dir   = "/path/to/client-b/helpdesk_agent"
    display_name = "Helpdesk"
  }
}
EOF

# Deploy
terraform apply -var-file="clients/client-b.tfvars"
```

## Update Portal 26 Endpoint

```hcl
# terraform.tfvars
portal26_endpoint = "https://new-portal26.example.com"
```

```bash
terraform apply  # Redeploys all agents with new endpoint
```

## Add New Agent

```hcl
# terraform.tfvars
agents = {
  # Existing agents...
  
  "new-agent" = {  # Add this
    source_dir   = "./new_agent"
    display_name = "New Agent"
  }
}
```

```bash
terraform apply  # Deploys new agent with Portal 26
```

## Agent Code Changes (Automatic)

**Before (original agent.py):**
```python
from google.adk.agents import Agent

def get_weather(city: str):
    # ... existing code

root_agent = Agent(...)
```

**After (automatically modified):**
```python
import otel_portal26  # ← Added automatically by script
from google.adk.agents import Agent

def get_weather(city: str):
    # ... unchanged

root_agent = Agent(...)  # Unchanged
```

That's the ONLY change! Everything else is handled by the OTEL module.

## Verification

### Check Deployment

```bash
# View Terraform outputs
terraform output

# List deployed agents
python3 ../list_agents.py
```

### Test Telemetry

```bash
# Query agent
python3 ../query_agent.py AGENT_ID "What is the weather in Tokyo?"

# Check Portal 26 for:
# - Traces: agent invocations, LLM calls
# - Logs: Application logs, errors
# - Metrics: Request counts, latencies
```

## Troubleshooting

### "No module named 'agent'"

Ensure `source_dir` points to a directory containing `agent.py`:

```bash
ls /path/to/source_dir/agent.py  # Should exist
```

### "Deployment failed"

Check logs:

```bash
terraform apply -var-file="..." 2>&1 | tee deploy.log
```

### No telemetry in Portal 26

Verify Portal 26 endpoint is correct:

```bash
terraform output portal26_config
```

Test endpoint:

```bash
curl https://portal26.example.com/health
```

## File Structure

```
.
├── otel_portal26.py                    # Shared OTEL module
├── scripts/
│   └── inject_otel_and_deploy.py      # Deployment script
├── terraform/
│   ├── main.tf                         # Terraform config
│   ├── variables.tf                    # Variables
│   ├── terraform.tfvars                # Your config
│   └── clients/
│       ├── client-a.tfvars            # Client A config
│       └── client-b.tfvars            # Client B config
└── my_agent/
    ├── agent.py                        # Your agent (will be modified)
    └── requirements.txt
```

## Cost

- **Terraform state:** Free (local by default)
- **Agent deployment:** Pay-per-invocation
- **No additional infra:** No Cloud Run, no wrapper costs

## Next Steps

1. ✅ Copy `terraform.tfvars.example` to `terraform.tfvars`
2. ✅ Set `portal26_endpoint` and agent paths
3. ✅ Run `terraform apply`
4. 📊 View telemetry in Portal 26 dashboard
5. 🚀 Scale to multiple clients using `clients/*.tfvars` files

## Support

- **Documentation:** See `/VERTEX_ENGINE_PORTAL26_SOLUTION.md` for detailed explanation
- **Issues:** Check `terraform apply` output for errors
- **Portal 26:** Verify endpoint connectivity before deployment
