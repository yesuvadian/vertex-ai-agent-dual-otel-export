# Portal 26 Integration for Vertex AI Agent Engine

Complete Terraform solution for adding Portal 26 telemetry to existing Vertex AI agents.

## Overview

This standalone solution enables Portal 26 telemetry for Vertex AI Agent Engine agents that **don't have OTEL initialization code**, using Terraform for configuration management.

## What This Does

- ✅ Adds Portal 26 telemetry to existing agents
- ✅ Minimal code changes (one import line, auto-injected)
- ✅ Terraform manages all configuration
- ✅ Multi-client support with isolated namespaces
- ✅ Pure Vertex AI Agent Engine (no Cloud Run)

## Quick Start

### 0. Setup Permissions (Required First)

**Important:** Before deploying, you need proper GCP permissions.

```bash
# Create service account with required permissions
./scripts/setup_terraform_sa.sh your-project-id

# Verify permissions
./scripts/verify_permissions.sh portal26-terraform@your-project-id.iam.gserviceaccount.com your-project-id

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"
```

**See [PERMISSIONS.md](PERMISSIONS.md) for detailed permission requirements.**

### 1. Configure

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
    source_dir   = "../../my_agent"  # Path to agent source
    display_name = "My Agent"
  }
}
```

### 2. Deploy

```bash
terraform init
terraform apply
```

### 3. Verify

```bash
cd ../..
python3 query_agent.py AGENT_ID "test query"
```

Check Portal 26 dashboard for traces, logs, and metrics!

## How It Works

```
Terraform Configuration
    ↓
Python Script (automatic)
    ├─ Copy agent source
    ├─ Inject otel_portal26.py
    └─ Add "import otel_portal26"
    ↓
Deploy to Vertex AI Agent Engine
    ↓
Agent starts → OTEL initializes → Portal 26
```

## Multi-Client Example

### Client A
```bash
terraform apply -var-file="terraform/clients/client-a.tfvars"
```

### Client B
```bash
terraform apply -var-file="terraform/clients/client-b.tfvars"
```

Each client gets isolated Portal 26 namespace!

## Structure

```
terraform-portal26/
├── README.md                        # This file
├── otel_portal26.py                # Shared OTEL module
├── scripts/
│   └── inject_otel_and_deploy.py  # Deployment script
├── terraform/
│   ├── main.tf                     # Terraform config
│   ├── variables.tf                # Variables
│   ├── terraform.tfvars.example   # Template
│   ├── clients/
│   │   ├── client-a.tfvars        # Client A example
│   │   └── client-b.tfvars        # Client B example
│   ├── QUICKSTART_PORTAL26.md     # 5-minute guide
│   └── README.md                   # Terraform docs
└── docs/
    ├── VERTEX_ENGINE_PORTAL26_SOLUTION.md  # Detailed guide
    └── PORTAL26_INTEGRATION_GUIDE.md       # All approaches
```

## Code Changes (Automatic)

Your agent gets ONE line added:

```python
import otel_portal26  # ← Added automatically
from google.adk.agents import Agent

# ... rest unchanged
```

## Common Operations

### Update Portal 26 Endpoint

```hcl
# terraform/terraform.tfvars
portal26_endpoint = "https://new-endpoint.com"
```

```bash
cd terraform && terraform apply
```

### Add New Agent

```hcl
agents = {
  # Existing...
  
  "new-agent" = {
    source_dir   = "../../new_agent"
    display_name = "New Agent"
  }
}
```

```bash
cd terraform && terraform apply
```

## Documentation

- **Permissions Setup:** `PERMISSIONS.md` (⚠️ **Read this first!**)
- **Quick Start:** `terraform/QUICKSTART_PORTAL26.md` (5 minutes)
- **One-Time Setup:** `QUICKSTART_ONE_TIME_INJECTION.md` (Commit and deploy)
- **Deployment Approaches:** `CLIENT_DEPLOYMENT_APPROACHES.md` (Choose your strategy)
- **Detailed Guide:** `docs/VERTEX_ENGINE_PORTAL26_SOLUTION.md`
- **All Approaches:** `docs/PORTAL26_INTEGRATION_GUIDE.md`
- **Terraform Docs:** `terraform/README.md`

## Requirements

### Software
- Python 3.10+
- Terraform >= 1.5
- gcloud CLI (authenticated)

### GCP Permissions
- **Approach 1 (One-Time):** `aiplatform.user` + `storage.objectAdmin`
- **Approach 2 (Terraform):** Service account with `aiplatform.admin` + `storage.admin` + `iam.serviceAccountUser` + `serviceusage.serviceUsageAdmin`

**Run setup script:** `./scripts/setup_terraform_sa.sh PROJECT_ID`

**Full details:** [PERMISSIONS.md](PERMISSIONS.md)

### Other
- Portal 26 endpoint URL
- Agent source code accessible

## Support

1. Read `terraform/QUICKSTART_PORTAL26.md` for step-by-step setup
2. Check `docs/` for detailed guides
3. Verify Portal 26 endpoint connectivity
4. Review Terraform output for errors

## Summary

**For clients with many existing Vertex AI agents:**
- ✅ Terraform manages Portal 26 configuration
- ✅ Minimal code changes (automatic)
- ✅ Multi-client support
- ✅ No Cloud Run needed
- ✅ All telemetry → Portal 26

Perfect for managing Portal 26 integration at scale!
