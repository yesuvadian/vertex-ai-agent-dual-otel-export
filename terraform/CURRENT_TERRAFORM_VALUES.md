# Current Terraform Configuration Values

## 📋 terraform.tfvars (Current Settings)

```hcl
# Project and Region
project_id = "agentic-ai-integration-490716"
region     = "us-central1"

# Agent IDs
portal26_ngrok_agent_id = "2658127084508938240"
portal26_otel_agent_id  = "7483734085236424704"

# Environment variables for portal26_ngrok_agent
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://tabetha-unelemental-bibulously.ngrok-free.dev"
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local"
}

# Environment variables for portal26_otel_agent
portal26_otel_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://otel-tenant1.portal26.in:4318"
  service_name        = "portal26_otel_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=otel-direct"
}

# Deployment trigger
trigger_redeploy = false
```

---

## 🔧 How Each Value Maps to Agent Configuration

### portal26_ngrok_agent_env_vars

| Terraform Variable | Maps to Environment Variable | Current Value |
|-------------------|------------------------------|---------------|
| `telemetry_enabled` | `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` | `true` |
| `otel_endpoint` | `OTEL_EXPORTER_OTLP_ENDPOINT` | `https://tabetha-unelemental-bibulously.ngrok-free.dev` |
| `service_name` | `OTEL_SERVICE_NAME` | `portal26_ngrok_agent` |
| `resource_attributes` | `OTEL_RESOURCE_ATTRIBUTES` | `portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local` |

**Generated .env file**: `portal26_ngrok_agent/.env`

### portal26_otel_agent_env_vars

| Terraform Variable | Maps to Environment Variable | Current Value |
|-------------------|------------------------------|---------------|
| `telemetry_enabled` | `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` | `true` |
| `otel_endpoint` | `OTEL_EXPORTER_OTLP_ENDPOINT` | `https://otel-tenant1.portal26.in:4318` |
| `service_name` | `OTEL_SERVICE_NAME` | `portal26_otel_agent` |
| `resource_attributes` | `OTEL_RESOURCE_ATTRIBUTES` | `portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=otel-direct` |

**Generated .env file**: `portal26_otel_agent/.env`

---

## ✏️ How to Change Values Through Terraform

### Example 1: Change ngrok Endpoint

**Edit** `terraform/terraform.tfvars`:

```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://new-tunnel-url.ngrok-free.dev"  # ← CHANGED
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local"
}

trigger_redeploy = true  # ← ENABLE REDEPLOYMENT
```

**Apply:**
```bash
cd terraform
terraform plan    # Preview changes
terraform apply   # Apply changes
```

**After deployment completes** (2-3 minutes):
```hcl
trigger_redeploy = false  # ← DISABLE TRIGGER
```
```bash
terraform apply
```

---

### Example 2: Change Tenant ID (Multi-tenant)

**Edit** `terraform/terraform.tfvars`:

```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://tabetha-unelemental-bibulously.ngrok-free.dev"
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant2,portal26.user.id=relusys,agent.type=ngrok-local"  # ← tenant2
}

portal26_otel_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://otel-tenant1.portal26.in:4318"
  service_name        = "portal26_otel_agent"
  resource_attributes = "portal26.tenant_id=tenant2,portal26.user.id=relusys,agent.type=otel-direct"  # ← tenant2
}

trigger_redeploy = true
```

**Apply:**
```bash
terraform apply
```

---

### Example 3: Add Environment Tag

**Edit** `terraform/terraform.tfvars`:

```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://tabetha-unelemental-bibulously.ngrok-free.dev"
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local,environment=production"  # ← Added environment
}

trigger_redeploy = true
```

**Apply:**
```bash
terraform apply
```

---

### Example 4: Disable Telemetry

**Edit** `terraform/terraform.tfvars`:

```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "false"  # ← DISABLED
  otel_endpoint       = "https://tabetha-unelemental-bibulously.ngrok-free.dev"
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local"
}

trigger_redeploy = true
```

**Apply:**
```bash
terraform apply
```

---

### Example 5: Change Portal26 Endpoint

**Edit** `terraform/terraform.tfvars`:

```hcl
portal26_otel_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://otel-tenant2.portal26.in:4318"  # ← CHANGED to tenant2
  service_name        = "portal26_otel_agent"
  resource_attributes = "portal26.tenant_id=tenant2,portal26.user.id=relusys,agent.type=otel-direct"
}

trigger_redeploy = true
```

**Apply:**
```bash
terraform apply
```

---

## 🔄 Terraform Workflow

### Standard Update Workflow

```bash
# 1. Edit configuration
cd terraform
notepad terraform.tfvars

# 2. Preview changes
terraform plan

# 3. Apply if looks good
terraform apply

# 4. Wait for deployment (2-3 minutes if trigger_redeploy=true)

# 5. Test
cd ..
python test_tracer_provider.py

# 6. Disable trigger (back in terraform/)
cd terraform
# Edit terraform.tfvars: trigger_redeploy = false
terraform apply
```

### Testing Workflow (No Redeployment)

```bash
# 1. Edit configuration
cd terraform
notepad terraform.tfvars
# Keep trigger_redeploy = false

# 2. Apply (only updates .env files)
terraform apply

# 3. Review .env files
type ..\portal26_ngrok_agent\.env

# 4. When ready to deploy:
# Edit terraform.tfvars: trigger_redeploy = true
terraform apply
```

---

## 📊 Terraform State

### View Current State

```bash
cd terraform

# List all managed resources
terraform state list

# Show current state
terraform show

# View specific resource
terraform state show local_file.portal26_ngrok_agent_env

# View outputs
terraform output
```

### Example Output

```bash
$ terraform state list
local_file.portal26_ngrok_agent_env
local_file.portal26_otel_agent_env
null_resource.redeploy_portal26_ngrok_agent[0]
null_resource.redeploy_portal26_otel_agent[0]

$ terraform output
portal26_ngrok_agent_env_file = "../portal26_ngrok_agent/.env"
portal26_ngrok_agent_id = "2658127084508938240"
portal26_otel_agent_env_file = "../portal26_otel_agent/.env"
portal26_otel_agent_id = "7483734085236424704"
```

---

## 🎯 Quick Reference: All Configurable Values

### Global Settings

| Variable | Current Value | Purpose |
|----------|---------------|---------|
| `project_id` | `agentic-ai-integration-490716` | GCP project |
| `region` | `us-central1` | GCP region |
| `trigger_redeploy` | `false` | Enable/disable redeployment |

### Agent IDs

| Variable | Current Value | Purpose |
|----------|---------------|---------|
| `portal26_ngrok_agent_id` | `2658127084508938240` | Identify ngrok agent |
| `portal26_otel_agent_id` | `7483734085236424704` | Identify otel agent |

### Portal26 Ngrok Agent Variables

| Variable | Current Value | When to Change |
|----------|---------------|----------------|
| `telemetry_enabled` | `"true"` | To enable/disable telemetry |
| `otel_endpoint` | `"https://tabetha-unelemental-bibulously.ngrok-free.dev"` | When ngrok tunnel changes |
| `service_name` | `"portal26_ngrok_agent"` | To distinguish environments |
| `resource_attributes` | `"portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local"` | For multi-tenant, custom tracking |

### Portal26 OTEL Agent Variables

| Variable | Current Value | When to Change |
|----------|---------------|----------------|
| `telemetry_enabled` | `"true"` | To enable/disable telemetry |
| `otel_endpoint` | `"https://otel-tenant1.portal26.in:4318"` | When changing Portal26 instance |
| `service_name` | `"portal26_otel_agent"` | To distinguish environments |
| `resource_attributes` | `"portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=otel-direct"` | For multi-tenant, custom tracking |

---

## 💡 Common Scenarios with Terraform

### Scenario 1: ngrok Tunnel Expired

**Problem**: Your ngrok tunnel URL changed because you restarted ngrok.

**Solution**:
1. Get new ngrok URL: `https://new-url.ngrok-free.dev`
2. Edit `terraform/terraform.tfvars`:
   ```hcl
   portal26_ngrok_agent_env_vars = {
     otel_endpoint = "https://new-url.ngrok-free.dev"  # Changed
     # ... rest unchanged
   }
   trigger_redeploy = true
   ```
3. Run: `terraform apply`
4. Wait 2-3 minutes
5. Test: `python test_tracer_provider.py`

### Scenario 2: Switch to Different Tenant

**Problem**: You need to track a different tenant (tenant2).

**Solution**:
1. Edit `terraform/terraform.tfvars`:
   ```hcl
   portal26_ngrok_agent_env_vars = {
     resource_attributes = "portal26.tenant_id=tenant2,portal26.user.id=relusys,agent.type=ngrok-local"
     # ... rest unchanged
   }
   portal26_otel_agent_env_vars = {
     resource_attributes = "portal26.tenant_id=tenant2,portal26.user.id=relusys,agent.type=otel-direct"
     # ... rest unchanged
   }
   trigger_redeploy = true
   ```
2. Run: `terraform apply`

### Scenario 3: Add Custom Attributes

**Problem**: You want to add environment and version tags.

**Solution**:
1. Edit `terraform/terraform.tfvars`:
   ```hcl
   portal26_ngrok_agent_env_vars = {
     resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local,environment=production,version=2.0.0"
     # ... rest unchanged
   }
   trigger_redeploy = true
   ```
2. Run: `terraform apply`

### Scenario 4: Testing Without Deployment

**Problem**: You want to test configuration changes without redeploying.

**Solution**:
1. Edit `terraform/terraform.tfvars` with new values
2. Keep `trigger_redeploy = false`
3. Run: `terraform apply`
4. Check: `type ..\portal26_ngrok_agent\.env`
5. When satisfied, set `trigger_redeploy = true` and apply again

---

## 🔍 Verify Changes Through Terraform

### Check What Will Change

```bash
terraform plan
```

**Example output:**
```
Terraform will perform the following actions:

  # local_file.portal26_ngrok_agent_env will be updated in-place
  ~ resource "local_file" "portal26_ngrok_agent_env" {
      ~ content = <<-EOT
            OTEL_EXPORTER_OTLP_ENDPOINT=https://NEW-URL.ngrok-free.dev
        EOT
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

### Verify After Apply

```bash
# View outputs
terraform output

# Check .env file
type ..\portal26_ngrok_agent\.env

# Test agents
cd ..
python test_tracer_provider.py

# Check logs
gcloud logging read "..." --limit 5
```

---

## 🚨 Important Notes

1. **Always run `terraform plan` first** - Review changes before applying
2. **`trigger_redeploy = true` takes 2-3 minutes** - Agent redeployment is slow
3. **Reset trigger after deployment** - Set back to `false` to avoid accidental redeployment
4. **Terraform doesn't track actual agent status** - Only tracks configuration files
5. **Changes require redeployment** - Environment variables only take effect after redeployment

---

## 📖 See Also

- **Full Terraform Guide**: `terraform/README.md`
- **Quick Reference**: `terraform/TERRAFORM_GUIDE.md`
- **Architecture**: `terraform/ARCHITECTURE.md`
- **Deployment Success**: `../DEPLOYMENT_SUCCESS.md`
