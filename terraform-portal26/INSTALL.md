# Installation Guide

## Quick Install (Copy-Paste)

### Option 1: In Your Project Root

```bash
# From your project root directory
cd /path/to/your/project

# Copy terraform-portal26 folder here
cp -r /path/to/terraform-portal26 .

# Your structure should be:
# your-project/
# ├── terraform-portal26/    ← Portal 26 Terraform solution
# ├── my_agent/               ← Your existing agents
# ├── query_agent.py
# └── list_agents.py
```

### Option 2: Standalone Installation

```bash
# Create dedicated directory
mkdir -p ~/vertex-ai-portal26
cd ~/vertex-ai-portal26

# Copy terraform-portal26 folder
cp -r /path/to/terraform-portal26 .

cd terraform-portal26
```

## Setup

### 1. Configure

```bash
cd terraform-portal26/terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

Set:
- `project_id` - Your GCP project
- `portal26_endpoint` - Your Portal 26 URL
- `agents` - Paths to your agent source directories

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Deploy

```bash
terraform plan   # Review changes
terraform apply  # Deploy agents
```

## Directory Structure After Install

### Option 1 (In Project Root)
```
your-project/
├── terraform-portal26/          # Portal 26 solution
│   ├── README.md
│   ├── otel_portal26.py
│   ├── scripts/
│   ├── terraform/
│   └── docs/
├── my_agent/                     # Your existing agents
│   ├── agent.py
│   └── requirements.txt
├── query_agent.py
└── list_agents.py
```

### Option 2 (Standalone)
```
~/vertex-ai-portal26/
└── terraform-portal26/
    ├── README.md
    ├── otel_portal26.py
    ├── scripts/
    ├── terraform/
    └── docs/
```

## Verify Installation

```bash
# Check structure
ls -la terraform-portal26/

# Should see:
# - README.md
# - otel_portal26.py
# - scripts/
# - terraform/
# - docs/

# Check Terraform
cd terraform-portal26/terraform
terraform version  # Should show >= 1.5

# Check Python
python3 --version  # Should show >= 3.10
```

## Configure for Your Agents

Edit `terraform-portal26/terraform/terraform.tfvars`:

```hcl
project_id = "your-gcp-project-id"

portal26_endpoint     = "https://portal26.example.com"
portal26_service_name = "your-agents"

agents = {
  "agent-1" = {
    # Relative path from terraform directory to agent source
    source_dir   = "../../my_agent"
    display_name = "My Agent"
  }
}
```

**Path Rules:**
- Paths are relative to `terraform-portal26/terraform/` directory
- Use `../../` to go up to project root
- Example: `../../my_agent` points to `your-project/my_agent/`

## Deploy Your First Agent

```bash
cd terraform-portal26/terraform
terraform apply
```

Follow prompts, type `yes` to confirm.

## Verify Deployment

```bash
# Go back to project root
cd ../..

# List deployed agents
python3 list_agents.py

# Query an agent
python3 query_agent.py AGENT_ID "test query"

# Check Portal 26 for telemetry!
```

## Multi-Client Setup

```bash
cd terraform-portal26/terraform

# Create client configurations
cp clients/client-a.tfvars clients/my-client.tfvars
nano clients/my-client.tfvars

# Deploy for specific client
terraform apply -var-file="clients/my-client.tfvars"
```

## Uninstall

```bash
# Destroy agents (optional - keeps agents but removes from Terraform state)
cd terraform-portal26/terraform
terraform destroy

# Remove folder
cd ../..
rm -rf terraform-portal26
```

## Troubleshooting

### "terraform: command not found"

Install Terraform:
```bash
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### "Python version too old"

Install Python 3.10+:
```bash
# macOS
brew install python@3.11

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11
```

### "No such file or directory: agent source"

Check path in `terraform.tfvars`:
```bash
# From terraform directory, verify path exists
ls -la ../../my_agent/agent.py

# Should exist. If not, update source_dir in terraform.tfvars
```

## Next Steps

1. ✅ Read `terraform-portal26/README.md` for overview
2. ✅ Read `terraform-portal26/terraform/QUICKSTART_PORTAL26.md` for detailed walkthrough
3. ✅ Configure your agents in `terraform.tfvars`
4. ✅ Run `terraform apply`
5. 📊 Check Portal 26 for telemetry

## Support

- **Quick Start:** `terraform/QUICKSTART_PORTAL26.md`
- **Detailed Guide:** `docs/VERTEX_ENGINE_PORTAL26_SOLUTION.md`
- **All Options:** `docs/PORTAL26_INTEGRATION_GUIDE.md`
