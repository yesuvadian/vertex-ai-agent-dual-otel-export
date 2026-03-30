# Guide: Switching Between Values (Testing Workflow)

## 📋 What We Have

```
terraform/
├── terraform.tfvars            # Current active configuration
├── terraform.tfvars.backup     # Backup of old/working values
└── terraform.tfvars.dummy      # Dummy/test values
```

---

## 🔄 Complete Workflow: Test Dummy Values & Switch Back

### Step 1: View Current (Old/Working) Values

```cmd
cd terraform
type terraform.tfvars
```

**Current values:**
- ngrok endpoint: `https://tabetha-unelemental-bibulously.ngrok-free.dev`
- otel endpoint: `https://otel-tenant1.portal26.in:4318`
- tenant_id: `tenant1`
- user.id: `relusys`

✅ **Backup created**: `terraform.tfvars.backup`

---

### Step 2: Switch to Dummy Values

```cmd
cd terraform

# Copy dummy values to active config
copy terraform.tfvars.dummy terraform.tfvars
```

**Dummy values:**
- ngrok endpoint: `https://dummy-ngrok-endpoint.ngrok-free.dev`
- otel endpoint: `https://otel-test.portal26.in:4318`
- tenant_id: `tenant_test`
- user.id: `testuser`
- service names: Added `_TEST` suffix

---

### Step 3: Preview Changes (Without Applying)

```cmd
terraform plan
```

This shows what will change:
```
~ local_file.portal26_ngrok_agent_env will be updated
  OTEL_EXPORTER_OTLP_ENDPOINT:
    "https://tabetha-unelemental-bibulously.ngrok-free.dev"
    → "https://dummy-ngrok-endpoint.ngrok-free.dev"

  OTEL_SERVICE_NAME:
    "portal26_ngrok_agent"
    → "portal26_ngrok_agent_TEST"
```

---

### Step 4: Apply Dummy Values (Update .env Files Only)

```cmd
terraform apply
```

Type `yes` when prompted.

This will:
- ✅ Update `.env` files with dummy values
- ❌ NOT redeploy agents (trigger_redeploy = false)

---

### Step 5: Verify Dummy Values Were Applied

```cmd
# Check .env files
type ..\portal26_ngrok_agent\.env
type ..\portal26_otel_agent\.env
```

You should see:
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://dummy-ngrok-endpoint.ngrok-free.dev
OTEL_SERVICE_NAME=portal26_ngrok_agent_TEST
OTEL_RESOURCE_ATTRIBUTES=portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=ngrok-test
```

**Note**: Agents are still running with OLD values (not redeployed yet).

---

### Step 6 (Optional): Deploy with Dummy Values

If you want to actually deploy with dummy values:

```cmd
# Edit terraform.tfvars
notepad terraform.tfvars
```

Change:
```hcl
trigger_redeploy = true  # Change to true
```

```cmd
terraform apply
```

⏰ **Wait 2-3 minutes for deployment**

Test:
```cmd
cd ..
python test_tracer_provider.py
```

---

### Step 7: Switch Back to Old/Working Values

```cmd
cd terraform

# Restore from backup
copy terraform.tfvars.backup terraform.tfvars
```

Verify:
```cmd
type terraform.tfvars
```

You should see old values:
- ngrok: `https://tabetha-unelemental-bibulously.ngrok-free.dev`
- tenant_id: `tenant1`

---

### Step 8: Apply Old Values

```cmd
terraform plan  # Preview the switch back
```

```cmd
terraform apply  # Apply old values
```

This will:
- ✅ Update `.env` files back to old values
- ❌ NOT redeploy (if trigger_redeploy = false)

---

### Step 9: Redeploy with Old Values (If Needed)

If you deployed with dummy values earlier, redeploy with old values:

```cmd
# Edit terraform.tfvars
notepad terraform.tfvars
```

Change:
```hcl
trigger_redeploy = true
```

```cmd
terraform apply
```

⏰ **Wait 2-3 minutes**

---

### Step 10: Verify Back to Working State

```cmd
# Check .env files
type ..\portal26_ngrok_agent\.env

# Test agents
cd ..
python test_tracer_provider.py

# Check telemetry
dir otel-data
```

✅ **Back to working configuration!**

---

## 🎯 Quick Commands Summary

### Switch TO Dummy Values

```cmd
cd terraform
copy terraform.tfvars.dummy terraform.tfvars
terraform plan
terraform apply
type ..\portal26_ngrok_agent\.env  # Verify
```

### Switch BACK to Old Values

```cmd
cd terraform
copy terraform.tfvars.backup terraform.tfvars
terraform plan
terraform apply
type ..\portal26_ngrok_agent\.env  # Verify
```

---

## 📊 Configuration Files Comparison

### Old/Working Values (terraform.tfvars.backup)

```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://tabetha-unelemental-bibulously.ngrok-free.dev"
  service_name        = "portal26_ngrok_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local"
}

portal26_otel_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://otel-tenant1.portal26.in:4318"
  service_name        = "portal26_otel_agent"
  resource_attributes = "portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=otel-direct"
}

trigger_redeploy = false
```

### Dummy/Test Values (terraform.tfvars.dummy)

```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://dummy-ngrok-endpoint.ngrok-free.dev"  # CHANGED
  service_name        = "portal26_ngrok_agent_TEST"  # CHANGED
  resource_attributes = "portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=ngrok-test"  # CHANGED
}

portal26_otel_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://otel-test.portal26.in:4318"  # CHANGED
  service_name        = "portal26_otel_agent_TEST"  # CHANGED
  resource_attributes = "portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=otel-test"  # CHANGED
}

trigger_redeploy = false
```

---

## 🔍 Difference Summary

| Value | Old/Working | Dummy/Test |
|-------|-------------|------------|
| **ngrok endpoint** | `tabetha-unelemental-bibulously.ngrok-free.dev` | `dummy-ngrok-endpoint.ngrok-free.dev` |
| **otel endpoint** | `otel-tenant1.portal26.in:4318` | `otel-test.portal26.in:4318` |
| **ngrok service** | `portal26_ngrok_agent` | `portal26_ngrok_agent_TEST` |
| **otel service** | `portal26_otel_agent` | `portal26_otel_agent_TEST` |
| **tenant_id** | `tenant1` | `tenant_test` |
| **user.id** | `relusys` | `testuser` |
| **ngrok agent.type** | `ngrok-local` | `ngrok-test` |
| **otel agent.type** | `otel-direct` | `otel-test` |

---

## 💡 Use Cases

### Use Case 1: Test Configuration Without Redeployment

```cmd
# Switch to dummy
copy terraform.tfvars.dummy terraform.tfvars
terraform apply

# Check .env files (no deployment)
type ..\portal26_ngrok_agent\.env

# Switch back
copy terraform.tfvars.backup terraform.tfvars
terraform apply
```

**Result**: Only .env files changed, agents still running with old config

---

### Use Case 2: Full Test with Dummy Values

```cmd
# Switch to dummy
copy terraform.tfvars.dummy terraform.tfvars

# Enable deployment
notepad terraform.tfvars  # Set trigger_redeploy = true

# Deploy
terraform apply

# Wait 2-3 minutes, then test
python ..\test_tracer_provider.py

# Switch back
copy terraform.tfvars.backup terraform.tfvars
notepad terraform.tfvars  # Set trigger_redeploy = true
terraform apply
```

**Result**: Agents deployed with dummy values, then back to old values

---

### Use Case 3: Create Your Own Test Values

```cmd
# Edit dummy file
notepad terraform.tfvars.dummy

# Change values:
otel_endpoint = "https://my-test-endpoint.com"
resource_attributes = "portal26.tenant_id=my_test,portal26.user.id=me,agent.type=custom-test"

# Use it
copy terraform.tfvars.dummy terraform.tfvars
terraform apply
```

---

## ⚠️ Important Notes

1. **`.env` files vs Deployed agents**:
   - `terraform apply` updates `.env` files immediately
   - Agents only get new values after redeployment (trigger_redeploy = true)

2. **Always backup before testing**:
   ```cmd
   copy terraform.tfvars terraform.tfvars.backup
   ```

3. **Check what will change first**:
   ```cmd
   terraform plan
   ```

4. **Redeployment takes time**:
   - 2-3 minutes per agent
   - Set trigger_redeploy = true only when ready

5. **Verify after switching**:
   ```cmd
   type ..\portal26_ngrok_agent\.env
   python ..\test_tracer_provider.py
   ```

---

## 🛠️ Troubleshooting

### Problem: Changes not taking effect

**Cause**: Agents not redeployed

**Solution**:
```cmd
# Edit terraform.tfvars
trigger_redeploy = true

# Apply
terraform apply
```

### Problem: Can't find backup file

**Recreate backup from current values**:
```cmd
copy terraform.tfvars terraform.tfvars.backup
```

### Problem: Accidentally deployed with dummy values

**Fix**:
```cmd
# Switch back immediately
copy terraform.tfvars.backup terraform.tfvars
notepad terraform.tfvars  # Set trigger_redeploy = true
terraform apply
```

### Problem: Want to compare configurations

```cmd
# Show differences
fc terraform.tfvars.backup terraform.tfvars.dummy
```

---

## 📖 Quick Reference

| File | Purpose |
|------|---------|
| `terraform.tfvars` | Active configuration (what Terraform uses) |
| `terraform.tfvars.backup` | Backup of old/working values |
| `terraform.tfvars.dummy` | Test/dummy values |

| Command | What it does |
|---------|--------------|
| `copy terraform.tfvars.dummy terraform.tfvars` | Switch TO dummy |
| `copy terraform.tfvars.backup terraform.tfvars` | Switch BACK to old |
| `terraform plan` | Preview changes |
| `terraform apply` | Apply changes |
| `type ..\portal26_ngrok_agent\.env` | Check .env file |

---

**Ready to test?** Just run:
```cmd
cd terraform
copy terraform.tfvars.dummy terraform.tfvars
terraform plan
```
