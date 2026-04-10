# Portal 26 Integration for Vertex AI Agent Engine

Complete solution for adding Portal 26 telemetry to Vertex AI Agent Engine agents without OTEL initialization code.

## Problem

Clients have existing Vertex AI Agent Engine agents that:
- ❌ Don't have hardcoded OTEL initialization
- ❌ Can't use env_vars alone (arrive too late for deployed agents)
- ✅ Need to send telemetry to Portal 26
- ✅ Want Terraform configuration management

## Solution

**Shared OTEL Module + Terraform Managed Deployment**

### How It Works

1. **Terraform Configuration** - Define Portal 26 endpoint and agents
2. **Python Script** (automatic) - Injects OTEL module into agent source
3. **Vertex AI Deploy** - Deploys agent with Portal 26 configuration
4. **Runtime** - OTEL auto-initializes, telemetry flows to Portal 26

### Architecture

```
Terraform (terraform.tfvars)
    ↓
    Portal 26 endpoint
    Agent source paths
    ↓
Python Script (automatic)
    ↓
    1. Copy agent source
    2. Inject otel_portal26.py
    3. Add "import otel_portal26" to agent.py
    ↓
Vertex AI Agent Engine
    ↓
    Agent starts
    → OTEL initializes
    → Telemetry → Portal 26
```

## Implementation

### Files

- `otel_portal26.py` - Shared OTEL initialization module
- `scripts/inject_otel_and_deploy.py` - Deployment script
- `terraform/main.tf` - Terraform configuration
- `terraform/variables.tf` - Portal 26 variables

### Agent Code Changes

**Original agent.py:**
```python
from google.adk.agents import Agent

def get_weather(city: str):
    return {"weather": "sunny"}

root_agent = Agent(...)
```

**After deployment (automatic):**
```python
import otel_portal26  # ← Added by script
from google.adk.agents import Agent

def get_weather(city: str):  # ← Unchanged
    return {"weather": "sunny"}

root_agent = Agent(...)  # ← Unchanged
```

## Usage

### 1. Configure

```hcl
# terraform/terraform.tfvars
project_id = "your-project-id"

portal26_endpoint     = "https://portal26.example.com"
portal26_service_name = "my-agents"

agents = {
  "support-agent" = {
    source_dir   = "../../my_agent"
    display_name = "Support Agent"
  }
}
```

### 2. Deploy

```bash
cd terraform
terraform init
terraform apply
```

### 3. Verify

```bash
python3 ../../query_agent.py AGENT_ID "test"
# Check Portal 26 for telemetry
```

## Multi-Client Example

### Client A

```hcl
# terraform/clients/client-a.tfvars
portal26_endpoint = "https://portal26.example.com/client-a"

agents = {
  "support" = {
    source_dir = "/path/to/client-a/support"
    display_name = "Support"
  }
}
```

```bash
terraform apply -var-file="clients/client-a.tfvars"
```

### Client B

```hcl
# terraform/clients/client-b.tfvars
portal26_endpoint = "https://portal26.example.com/client-b"

agents = {
  "sales" = {
    source_dir = "/path/to/client-b/sales"
    display_name = "Sales"
  }
}
```

```bash
terraform apply -var-file="clients/client-b.tfvars"
```

## Benefits

- ✅ **Minimal code changes** - One import line (automatic)
- ✅ **Terraform managed** - Update endpoint → redeploy all agents
- ✅ **Multi-client support** - Separate Portal 26 namespaces
- ✅ **Reusable** - Same OTEL module for all agents
- ✅ **Pure Vertex AI** - No Cloud Run or wrapper needed

## What Gets Sent to Portal 26

**Traces:**
- Agent invocations
- LLM calls (Gemini)
- Tool executions
- Timing/latency

**Logs:**
- Application logs
- Errors
- Debug info

**Metrics:**
- Request counts
- Token usage
- Performance metrics

## Limitations

### Requires
- Agent source code access
- Python 3.10+
- Agent redeployment (managed by Terraform)

### Not Supported
- Agents without source access
- Binary/compiled agents
- Third-party agents you don't control

## Troubleshooting

### Deployment Fails

```bash
# Check logs
terraform apply 2>&1 | tee deploy.log
```

### No Telemetry in Portal 26

```bash
# Verify config
terraform output portal26_config

# Test endpoint
curl https://portal26.example.com/health
```

### Import Error

```bash
# Verify OTEL module exists
ls otel_portal26.py

# Verify injection worked
grep "import otel_portal26" /path/to/agent/agent.py
```

## Summary

This solution provides:
- ✅ Portal 26 integration for existing agents
- ✅ Terraform configuration management
- ✅ Minimal code changes (automatic)
- ✅ Multi-client support
- ✅ Pure Vertex AI Agent Engine solution

Perfect for managing Portal 26 telemetry across many agents!
