# Terraform Configuration for Vertex AI Agent Engine

This Terraform configuration manages environment variables for Vertex AI Agent Engine (Reasoning Engines) agents.

## Prerequisites

- Terraform >= 1.0
- Google Cloud SDK (gcloud)
- Python with google-adk installed
- Authenticated GCP account: `gcloud auth application-default login`

## Files

- `main.tf` - Main Terraform configuration
- `variables.tf` - Variable definitions
- `terraform.tfvars.example` - Example variables file
- `.gitignore` - Git ignore rules

## How It Works

Since Terraform doesn't have native support for Vertex AI Reasoning Engine yet, this configuration:

1. **Manages .env files** - Creates/updates `.env` files for each agent with your environment variables
2. **Optional Redeployment** - Optionally triggers agent redeployment when variables change
3. **Tracks Changes** - Uses Terraform state to track environment variable changes

## Setup

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Create terraform.tfvars

Copy the example file and customize:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_id = "your-project-id"
region     = "us-central1"

portal26_ngrok_agent_id = "your-ngrok-agent-id"
portal26_otel_agent_id  = "your-otel-agent-id"

portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://your-ngrok-endpoint.ngrok-free.dev"
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=youruser,agent.type=ngrok-local"
}

# Set to true when you want to redeploy
trigger_redeploy = false
```

### 3. Preview Changes

```bash
terraform plan
```

### 4. Apply Configuration

```bash
terraform apply
```

This will:
- Create/update `.env` files in agent directories
- Show what would be deployed (if `trigger_redeploy = true`)

## Updating Environment Variables

### Option 1: Update .env Files Only (Recommended for Testing)

1. Edit `terraform.tfvars` with new environment variable values
2. Set `trigger_redeploy = false`
3. Run `terraform apply`
4. .env files will be updated but agents won't be redeployed
5. Manually deploy when ready:
   ```bash
   cd ..
   python -m google.adk.cli deploy agent_engine portal26_ngrok_agent \
     --project agentic-ai-integration-490716 \
     --region us-central1 \
     --agent_engine_id 2658127084508938240
   ```

### Option 2: Update and Redeploy (Production)

1. Edit `terraform.tfvars` with new environment variable values
2. Set `trigger_redeploy = true`
3. Run `terraform apply`
4. Agents will be redeployed with new environment variables (takes 2-3 minutes per agent)
5. After deployment, set `trigger_redeploy = false` and run `terraform apply` again

## Example: Change OTEL Endpoint

1. Edit `terraform.tfvars`:
```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://NEW-ngrok-endpoint.ngrok-free.dev"  # Changed
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local"
}

trigger_redeploy = true  # Enable redeployment
```

2. Apply changes:
```bash
terraform apply
```

3. Verify deployment:
```bash
# Check logs
gcloud logging read "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" \
  AND resource.labels.reasoning_engine_id=\"2658127084508938240\" \
  AND textPayload=~\"OTEL_INIT\"" \
  --limit 5 --project agentic-ai-integration-490716
```

4. Disable redeployment trigger:
```hcl
trigger_redeploy = false
```

```bash
terraform apply
```

## Example: Add New Resource Attribute

```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://tabetha-unelemental-bibulously.ngrok-free.dev"
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local,environment=production"  # Added environment
}

trigger_redeploy = true
```

## Viewing Current Configuration

```bash
# View Terraform outputs
terraform output

# View current agent configuration in GCP
gcloud ai reasoning-engines describe 2658127084508938240 \
  --location=us-central1 \
  --project=agentic-ai-integration-490716
```

## Troubleshooting

### Deployment Fails

If redeployment fails:

1. Check the error in Terraform output
2. Manually verify agent configuration:
   ```bash
   gcloud ai reasoning-engines describe YOUR_AGENT_ID \
     --location=us-central1 \
     --project=agentic-ai-integration-490716
   ```
3. Try manual deployment:
   ```bash
   cd ..
   python -m google.adk.cli deploy agent_engine portal26_ngrok_agent \
     --project agentic-ai-integration-490716 \
     --region us-central1 \
     --agent_engine_id 2658127084508938240
   ```

### Environment Variables Not Applied

Environment variables are set at deployment time. To apply changes:

1. Verify .env files are updated: `cat ../portal26_ngrok_agent/.env`
2. Redeploy the agent (set `trigger_redeploy = true`)
3. Verify in GCP Console or with gcloud

### Terraform State Issues

If Terraform state gets out of sync:

```bash
# View state
terraform state list

# Refresh state
terraform refresh

# If needed, remove and reimport resources
terraform state rm null_resource.update_portal26_ngrok_agent_env
```

## Limitations

- **No Native Resource**: Terraform doesn't have native support for Vertex AI Reasoning Engine yet
- **Redeployment Required**: Environment variable changes require full agent redeployment
- **Deployment Time**: Each deployment takes 2-3 minutes
- **Manual Verification**: Must verify changes in GCP Console or via gcloud

## Alternative: REST API Approach

For more direct control, you can use the REST API with `terraform-provider-restapi`:

```bash
# Install provider
terraform init -upgrade

# See rest_api.tf.example for REST API approach
```

## Security Best Practices

1. **Never commit terraform.tfvars** - Contains sensitive configuration
2. **Use Secret Manager** - Store sensitive values in GCP Secret Manager
3. **Restrict Access** - Use IAM to control who can update agents
4. **Review Changes** - Always run `terraform plan` before `apply`
5. **Backup State** - Use remote state storage (GCS) for production

## Production Setup

For production, use remote state:

```hcl
# backend.tf
terraform {
  backend "gcs" {
    bucket = "your-terraform-state-bucket"
    prefix = "vertex-ai-agents"
  }
}
```

Initialize with backend:

```bash
terraform init -backend-config="bucket=your-terraform-state-bucket"
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Update Agent Environment Variables

on:
  push:
    paths:
      - 'terraform/terraform.tfvars'
      - 'terraform/*.tf'

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2

      - name: Terraform Init
        run: terraform init
        working-directory: terraform

      - name: Terraform Plan
        run: terraform plan
        working-directory: terraform

      - name: Terraform Apply
        run: terraform apply -auto-approve
        working-directory: terraform
```

## Support

For issues or questions:
- Check DEPLOYMENT_SUCCESS.md in project root
- Review agent logs in GCP Console
- See Vertex AI Agent Engine documentation: https://cloud.google.com/vertex-ai/docs/agent-engine
