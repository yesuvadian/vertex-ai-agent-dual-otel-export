# Standalone Setup Guide

Use this if you want `terraform-portal26` as a completely separate project.

## Setup

### 1. Create Project Directory

```bash
mkdir -p ~/vertex-portal26-manager
cd ~/vertex-portal26-manager
```

### 2. Copy terraform-portal26

```bash
# Copy this entire folder
cp -r /path/to/terraform-portal26 .

cd terraform-portal26
```

### 3. Configure

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
project_id = "your-gcp-project"

portal26_endpoint     = "https://portal26.example.com"
portal26_service_name = "client-agents"

# Point to agent source directories (can be anywhere)
agents = {
  "agent-1" = {
    source_dir   = "/absolute/path/to/agent1"
    display_name = "Agent 1"
  }
  
  "agent-2" = {
    source_dir   = "/absolute/path/to/agent2"
    display_name = "Agent 2"
  }
}
```

**Note:** Use **absolute paths** for standalone setup.

### 4. Deploy

```bash
terraform init
terraform apply
```

## Managing Multiple Clients

### Structure

```
~/vertex-portal26-manager/
└── terraform-portal26/
    └── terraform/
        └── clients/
            ├── acme-corp.tfvars     # Client 1
            ├── globex-inc.tfvars    # Client 2
            └── initech.tfvars       # Client 3
```

### Create Client Configs

```bash
cd terraform-portal26/terraform/clients

# Client 1
cat > acme-corp.tfvars <<EOF
project_id = "acme-project-123"
portal26_endpoint = "https://portal26.example.com/acme"
portal26_service_name = "acme-agents"

agents = {
  "support" = {
    source_dir   = "/clients/acme/support_agent"
    display_name = "Acme Support"
  }
}
EOF

# Client 2
cat > globex-inc.tfvars <<EOF
project_id = "globex-project-456"
portal26_endpoint = "https://portal26.example.com/globex"
portal26_service_name = "globex-agents"

agents = {
  "sales" = {
    source_dir   = "/clients/globex/sales_agent"
    display_name = "Globex Sales"
  }
}
EOF
```

### Deploy Per Client

```bash
cd ..  # Back to terraform directory

# Deploy Client 1
terraform apply -var-file="clients/acme-corp.tfvars"

# Deploy Client 2
terraform apply -var-file="clients/globex-inc.tfvars"
```

## Organizing Agent Source Code

### Option A: All Clients in One Directory

```
/clients/
├── acme/
│   ├── support_agent/
│   │   ├── agent.py
│   │   └── requirements.txt
│   └── sales_agent/
├── globex/
│   └── sales_agent/
└── initech/
    └── helpdesk_agent/
```

### Option B: Clients in Git Repos

```bash
# Clone client repositories
cd /clients
git clone git@github.com:acme/agents.git acme
git clone git@github.com:globex/agents.git globex

# Reference in terraform.tfvars
agents = {
  "support" = {
    source_dir = "/clients/acme/support_agent"
    display_name = "Support"
  }
}
```

### Option C: Remote Agents

```bash
# Sync from remote before deploy
rsync -av user@client-server:/agents/support_agent /tmp/client-agents/support

# Use temporary path in terraform
agents = {
  "support" = {
    source_dir = "/tmp/client-agents/support"
    display_name = "Support"
  }
}
```

## Automation with Scripts

### deploy-all-clients.sh

```bash
#!/bin/bash
# Save as: terraform-portal26/scripts/deploy-all-clients.sh

cd "$(dirname "$0")/../terraform"

for client_file in clients/*.tfvars; do
    client_name=$(basename "$client_file" .tfvars)
    echo "========================================="
    echo "Deploying $client_name..."
    echo "========================================="
    
    terraform apply -var-file="$client_file" -auto-approve
    
    if [ $? -eq 0 ]; then
        echo "✅ $client_name deployed successfully"
    else
        echo "❌ $client_name deployment failed"
    fi
    echo ""
done
```

Usage:
```bash
chmod +x terraform-portal26/scripts/deploy-all-clients.sh
./terraform-portal26/scripts/deploy-all-clients.sh
```

### update-portal26-endpoint.sh

```bash
#!/bin/bash
# Update Portal 26 endpoint for a client

CLIENT=$1
NEW_ENDPOINT=$2

if [ -z "$CLIENT" ] || [ -z "$NEW_ENDPOINT" ]; then
    echo "Usage: $0 <client-name> <new-endpoint>"
    exit 1
fi

cd "$(dirname "$0")/../terraform"

# Update endpoint in client config
sed -i "s|portal26_endpoint = .*|portal26_endpoint = \"$NEW_ENDPOINT\"|" \
    clients/${CLIENT}.tfvars

# Redeploy
terraform apply -var-file="clients/${CLIENT}.tfvars"
```

Usage:
```bash
./scripts/update-portal26-endpoint.sh acme-corp https://new-portal26.com
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/deploy-agents.yml
name: Deploy Agents to Vertex AI

on:
  push:
    paths:
      - 'terraform-portal26/terraform/clients/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.6.0
      
      - name: Setup GCP credentials
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_CREDENTIALS }}
      
      - name: Deploy changed clients
        run: |
          cd terraform-portal26/terraform
          
          for client_file in clients/*.tfvars; do
            terraform apply -var-file="$client_file" -auto-approve
          done
```

## Monitoring

### Check Deployment Status

```bash
cd terraform-portal26/terraform

# View all outputs
terraform output

# Check specific client
terraform output -var-file="clients/acme-corp.tfvars"
```

### Query Deployed Agents

```python
# check-agents.py
import vertexai
from vertexai import agent_engines

projects = {
    "acme": "acme-project-123",
    "globex": "globex-project-456",
}

for client, project_id in projects.items():
    print(f"\n{client.upper()} Agents:")
    vertexai.init(project=project_id, location="us-central1")
    
    agents = agent_engines.list()
    for agent in agents:
        print(f"  - {agent.display_name}: {agent.resource_name}")
```

## Backup & Version Control

```bash
# Initialize git in terraform-portal26
cd terraform-portal26
git init

# Add files (terraform.tfvars excluded by .gitignore)
git add .
git commit -m "Initial Portal 26 setup"

# Push to remote
git remote add origin git@github.com:yourorg/portal26-terraform.git
git push -u origin main
```

## Cleanup

### Remove Specific Client

```bash
cd terraform-portal26/terraform

# Remove from Terraform (keeps agents running)
terraform state rm -var-file="clients/acme-corp.tfvars" 'null_resource.deploy_agents_portal26["support"]'

# Or destroy agents
terraform destroy -var-file="clients/acme-corp.tfvars"
```

### Remove All

```bash
cd terraform-portal26/terraform

# Destroy all managed resources
for client_file in clients/*.tfvars; do
    terraform destroy -var-file="$client_file" -auto-approve
done
```

## Benefits of Standalone Setup

- ✅ Centralized management for all clients
- ✅ Easy to backup and version control
- ✅ Consistent deployment process
- ✅ CI/CD integration ready
- ✅ Automation scripts in one place

## Next Steps

1. Set up client configs in `terraform/clients/`
2. Run `deploy-all-clients.sh` or deploy individually
3. Monitor via Portal 26 dashboard
4. Automate with CI/CD if needed
