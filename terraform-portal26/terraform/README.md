# Terraform Configuration Management for Vertex AI Agents

**Purpose:** Update OTEL configuration for existing Vertex AI agents across multiple clients.

## Use Case

Your clients already have many agents deployed. This Terraform setup:
- ✅ Updates existing agent configurations (no redeployment)
- ✅ Manages OTEL endpoints and environment variables
- ✅ Supports multiple clients with separate configs
- ✅ Provides environment profiles (dev/staging/prod)
- ❌ Does NOT deploy new agents
- ❌ Does NOT manage infrastructure

## Architecture

```
terraform.tfvars OR clients/client-a.tfvars
    ↓
Terraform reads existing agents
    ↓
Updates only env_vars with OTEL config
    ↓
No agent redeployment - just config update
```

## Quick Start

### 1. List Existing Agents

First, find your agent IDs:

```bash
cd ..
python3 list_agents.py
```

Output example:
```
agent-123456789  → Customer Support Agent
agent-987654321  → Sales Agent
```

### 2. Create Configuration

Edit `terraform.tfvars`:

```hcl
project_id = "your-project-id"

agents = {
  "123456789" = {
    display_name = "Customer Support Agent"
    otel_profile = "production"  # or development, staging, disabled
  }
  
  "987654321" = {
    display_name = "Sales Agent"
    otel_profile = "production"
  }
}

otel_endpoint_prod = "https://your-collector.run.app"
otel_service_name_prod = "your-agents"
```

### 3. Apply Configuration

```bash
terraform init
terraform plan   # Review changes
terraform apply  # Update agents
```

## Multi-Client Management

### Structure

```
terraform/
├── main.tf
├── variables.tf
└── clients/
    ├── client-a.tfvars  # Client A's agents
    ├── client-b.tfvars  # Client B's agents
    └── client-c.tfvars  # Client C's agents
```

### Deploy for Specific Client

```bash
# Update Client A's agents
terraform apply -var-file="clients/client-a.tfvars"

# Update Client B's agents
terraform apply -var-file="clients/client-b.tfvars"
```

### Workspace Approach (Alternative)

```bash
# Create workspace per client
terraform workspace new client-a
terraform workspace new client-b

# Switch and apply
terraform workspace select client-a
terraform apply -var-file="clients/client-a.tfvars"

terraform workspace select client-b
terraform apply -var-file="clients/client-b.tfvars"
```

## OTEL Profiles

### Available Profiles

| Profile | Use Case | OTEL Config |
|---------|----------|-------------|
| `production` | Live agents | Production collector endpoint |
| `development` | Testing agents | Dev/ngrok endpoint |
| `staging` | Pre-production | Staging collector |
| `disabled` | Remove OTEL | Clears all OTEL env vars |

### Example: Mixed Profiles

```hcl
agents = {
  "agent-001" = {
    display_name = "Production Support"
    otel_profile = "production"
  }
  
  "agent-dev" = {
    display_name = "Test Agent"
    otel_profile = "development"
  }
  
  "agent-legacy" = {
    display_name = "Legacy Agent (no OTEL)"
    otel_profile = "disabled"
  }
}
```

## Configuration Updates

### Update OTEL Endpoint

Change endpoint in `terraform.tfvars`:

```hcl
otel_endpoint_prod = "https://new-collector.run.app"
```

Apply:
```bash
terraform apply
```

### Migrate Agent to Different Profile

```hcl
agents = {
  "agent-123" = {
    display_name = "Support Agent"
    otel_profile = "development"  # Changed from production
  }
}
```

### Add New Agent to OTEL

```hcl
agents = {
  # Existing agents...
  
  "agent-new-456" = {  # Add this
    display_name = "New Agent"
    otel_profile = "production"
  }
}
```

### Remove OTEL from Agent

```hcl
agents = {
  "agent-123" = {
    display_name = "Support Agent"
    otel_profile = "disabled"  # Removes OTEL config
  }
}
```

## Bulk Operations

### Enable OTEL on All Client Agents

```bash
# Create agent list script
python3 << 'EOF'
import vertexai
from vertexai import agent_engines

vertexai.init(project="client-project-id", location="us-central1")
agents = agent_engines.list()

print('agents = {')
for agent in agents:
    agent_id = agent.resource_name.split('/')[-1]
    print(f'  "{agent_id}" = {{')
    print(f'    display_name = "{agent.display_name}"')
    print(f'    otel_profile = "production"')
    print(f'  }}')
print('}')
EOF
```

Copy output to `terraform.tfvars` and apply.

### Update Endpoint for All Agents

Just change the endpoint variable - all agents using that profile update automatically:

```hcl
otel_endpoint_prod = "https://new-endpoint.com"
```

```bash
terraform apply  # Updates all production agents
```

## Verification

### Check Updated Configuration

```bash
# After terraform apply
python3 << 'EOF'
import vertexai
from vertexai import agent_engines

vertexai.init(project="your-project", location="us-central1")
agent = agent_engines.get("agent-123")

# Check env vars
for key, value in agent.env_vars.items():
    if key.startswith('OTEL'):
        print(f"{key} = {value}")
EOF
```

### Test Telemetry

```bash
# Query agent
python3 query_agent.py agent-123 "test query"

# Check your OTEL collector for traces/logs/metrics
```

## Best Practices

### 1. Use Client-Specific Files

```bash
terraform/clients/
├── acme-corp.tfvars
├── globex-inc.tfvars
└── initech.tfvars
```

### 2. Version Control

```bash
git add terraform/clients/client-a.tfvars
git commit -m "Update Client A OTEL config"
git tag client-a-v1.0
```

### 3. Staged Rollout

```hcl
# Week 1: Test on development agents
agents = {
  "agent-dev-001" = { otel_profile = "development" }
}

# Week 2: Promote to staging
agents = {
  "agent-dev-001" = { otel_profile = "staging" }
}

# Week 3: Production rollout
agents = {
  "agent-dev-001" = { otel_profile = "production" }
  "agent-prod-001" = { otel_profile = "production" }
  # ... more agents
}
```

### 4. Emergency Disable

```bash
# Quick disable all OTEL if collector fails
sed -i 's/otel_profile = "production"/otel_profile = "disabled"/g' terraform.tfvars
terraform apply
```

## Limitations

### What Terraform CANNOT Update

- Agent code (requires redeployment via Python SDK)
- Model changes (use Python SDK)
- Tool definitions (use Python SDK)
- Requirements/packages (use Python SDK)

### What Terraform CAN Update

- ✅ Environment variables (OTEL config)
- ✅ Display names
- ✅ Descriptions
- ✅ Resource labels/annotations

## Troubleshooting

### "Agent not found"

```bash
# Verify agent exists
python3 list_agents.py

# Check agent ID matches (no "projects/.../agents/" prefix)
agents = {
  "1234567890"  # ✅ Correct
  # NOT "projects/123/locations/us/agents/456"  # ❌ Wrong
}
```

### "Permission denied"

Ensure you have `aiplatform.agents.update` permission:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:you@example.com" \
  --role="roles/aiplatform.admin"
```

### "Prevent destroy"

Terraform won't delete agents (lifecycle policy). To remove from management:

```bash
# Remove from state (agent keeps running)
terraform state rm 'google_vertex_ai_agent_engine.agents["agent-123"]'
```

## Cost

**$0** - Updating configuration doesn't incur costs. Only agent usage costs apply.

## Migration Path

### Phase 1: Single Client (Manual)

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit manually
terraform apply
```

### Phase 2: Multiple Clients (Per-File)

```bash
terraform apply -var-file="clients/client-a.tfvars"
terraform apply -var-file="clients/client-b.tfvars"
```

### Phase 3: Automated (CI/CD)

```yaml
# .github/workflows/update-agents.yml
- name: Update Client A
  run: terraform apply -var-file="clients/client-a.tfvars" -auto-approve
```

## Examples

See `clients/` directory for real-world examples:
- `client-a.tfvars` - Multi-environment setup
- `client-b.tfvars` - Production-only setup
