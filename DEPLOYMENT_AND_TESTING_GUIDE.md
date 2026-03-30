# Agent Deployment and Testing Guide

Complete guide for deploying, testing, and managing Vertex AI agents with Terraform-managed environment variables.

---

## Table of Contents

1. [Agent Deployment](#agent-deployment)
2. [Testing Deployed Agents](#testing-deployed-agents)
3. [Terraform Configuration Management](#terraform-configuration-management)
4. [Switching to Dummy Values](#switching-to-dummy-values)
5. [Validating in Google Console](#validating-in-google-console)
6. [Switching Back to Original Values](#switching-back-to-original-values)
7. [Complete Testing Workflow](#complete-testing-workflow)
8. [Troubleshooting](#troubleshooting)

---

## Agent Deployment

### Prerequisites

- Google Cloud SDK installed and authenticated
- Python 3.10+ with `google-adk` package installed
- Agent folders: `portal26_ngrok_agent/` and `portal26_otel_agent/`
- `.env` files configured in each agent folder

### Deploy New Agents

**Deploy portal26_ngrok_agent:**

```bash
cd portal26_ngrok_agent

python -m google.adk.cli deploy agent_engine portal26_ngrok_agent \
  --project agentic-ai-integration-490716 \
  --region us-central1
```

**Deploy portal26_otel_agent:**

```bash
cd portal26_otel_agent

python -m google.adk.cli deploy agent_engine portal26_otel_agent \
  --project agentic-ai-integration-490716 \
  --region us-central1
```

**Expected Output:**
```
Staging all files...
Copying agent source code...
Reading environment variables from .env
Initializing Vertex AI...
Deploying to agent engine...
✓ Successfully deployed agent: portal26_ngrok_agent
Agent ID: 2658127084508938240
Query URL: https://us-central1-aiplatform.googleapis.com/v1beta1/projects/...
```

**Save the Agent IDs** - you'll need them for updates and Terraform configuration.

---

### Redeploy Existing Agents

To update an existing agent (e.g., after code changes):

```bash
python -m google.adk.cli deploy agent_engine portal26_ngrok_agent \
  --project agentic-ai-integration-490716 \
  --region us-central1 \
  --agent_engine_id 2658127084508938240
```

⏰ **Deployment time:** 2-3 minutes per agent

---

## Testing Deployed Agents

### Test Script

Use the provided test script to verify agents are working:

```bash
python test_tracer_provider.py
```

### What the Test Does

1. Queries both agents with a sample prompt
2. Verifies OTEL telemetry is being exported
3. Checks that traces include custom resource attributes
4. Validates dual export (ngrok + direct Portal26)

### Expected Output

```
========================================
Testing Dual OTEL Export Agents
========================================

Testing portal26_ngrok_agent...
Query: What is 2+2?
Response: 2 + 2 equals 4.
✓ Agent responded successfully

Testing portal26_otel_agent...
Query: What is the capital of France?
Response: The capital of France is Paris.
✓ Agent responded successfully

========================================
OTEL Export Verification
========================================

Checking telemetry data...
✓ Found telemetry data in otel-data/
✓ Traces contain portal26 resource attributes
  - portal26.tenant_id: tenant1
  - portal26.user.id: relusys
  - agent.type: ngrok-local / otel-direct

✓ Dual export successful!
```

### Manual Testing

You can also test agents manually using the GCP Console or REST API.

**Console Testing:**
1. Go to: https://console.cloud.google.com/vertex-ai/agents/agent-engines
2. Click on agent name
3. Go to "Query" tab
4. Enter a test prompt
5. Check response and telemetry

**REST API Testing:**

```bash
curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/2658127084508938240:query" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"input": {"query": "What is 2+2?"}}'
```

---

## Terraform Configuration Management

### Overview

Environment variables are managed through Terraform, allowing version-controlled, reproducible configuration changes.

**Key Files:**
- `terraform/terraform.tfvars` - Active configuration
- `terraform/terraform.tfvars.backup` - Production/original values backup
- `terraform/terraform.tfvars.dummy` - Test/dummy values
- `terraform/terraform.tfvars.example` - Template for new setups

### Current Configuration

**Production Values (terraform.tfvars.backup):**

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

**Dummy/Test Values (terraform.tfvars.dummy):**

```hcl
portal26_ngrok_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://dummy-ngrok-endpoint.ngrok-free.dev"
  service_name        = "portal26_ngrok_agent_TEST"
  resource_attributes = "portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=ngrok-test"
}

portal26_otel_agent_env_vars = {
  telemetry_enabled   = "true"
  otel_endpoint       = "https://otel-test.portal26.in:4318"
  service_name        = "portal26_otel_agent_TEST"
  resource_attributes = "portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=otel-test"
}

trigger_redeploy = false
```

---

## Switching to Dummy Values

### Quick Method (Recommended)

**Windows:**

```cmd
cd terraform
switch_to_dummy.bat
```

The script will:
1. Copy dummy configuration to `terraform.tfvars`
2. Show preview of changes (`terraform plan`)
3. Prompt for confirmation
4. Apply changes (`terraform apply`)

**Manual Method:**

```cmd
cd terraform

# 1. Copy dummy values to active config
copy terraform.tfvars.dummy terraform.tfvars

# 2. Preview changes
terraform plan

# 3. Apply changes (updates .env files only)
terraform apply
```

### Deploy with Dummy Values

After switching, if you want to actually deploy agents with dummy values:

**Step 1: Enable redeployment**

```cmd
notepad terraform.tfvars
```

Change line:
```hcl
trigger_redeploy = true  # Change from false to true
```

**Step 2: Apply and deploy**

```cmd
terraform apply
```

Type `yes` when prompted.

**Step 3: Wait for deployment**

⏰ **Wait 5-7 minutes** for both agents to redeploy.

You'll see output like:
```
null_resource.redeploy_portal26_ngrok_agent[0]: Creating...
null_resource.redeploy_portal26_otel_agent[0]: Creating...
...
Staging all files...
Copying agent source code...
Reading environment variables from .env
Deploying to agent engine...
```

**Step 4: Verify .env files**

```cmd
type ..\portal26_ngrok_agent\.env
```

Expected output:
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://dummy-ngrok-endpoint.ngrok-free.dev
OTEL_SERVICE_NAME=portal26_ngrok_agent_TEST
OTEL_RESOURCE_ATTRIBUTES=portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=ngrok-test
```

---

## Validating in Google Console

### Access the Console

1. Open: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716

2. You should see your two agents:
   - `portal26_ngrok_agent` (ID: 2658127084508938240)
   - `portal26_otel_agent` (ID: 7483734085236424704)

### Check portal26_ngrok_agent

**Step 1:** Click on **portal26_ngrok_agent**

**Step 2:** Go to **Deployment details** tab

**Step 3:** Scroll down to **Environment** section

**Step 4:** Verify dummy values:

```
GOOGLE_CLOUD_LOCATION: us-central1
GOOGLE_CLOUD_PROJECT: agentic-ai-integration-490716
OTEL_EXPORTER_OTLP_ENDPOINT: https://dummy-ngrok-endpoint.ngrok-free.dev  ✓ CHANGED
OTEL_SERVICE_NAME: portal26_ngrok_agent_TEST  ✓ CHANGED
OTEL_RESOURCE_ATTRIBUTES: portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=ngrok-test  ✓ CHANGED
```

📸 **Screenshot this for your records**

### Check portal26_otel_agent

Repeat the same steps for `portal26_otel_agent`:

```
OTEL_EXPORTER_OTLP_ENDPOINT: https://otel-test.portal26.in:4318  ✓ CHANGED
OTEL_SERVICE_NAME: portal26_otel_agent_TEST  ✓ CHANGED
OTEL_RESOURCE_ATTRIBUTES: portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=otel-test  ✓ CHANGED
```

### Important Notes

**Timing:**
- Changes appear in Console **only after** redeployment completes
- If `trigger_redeploy = false`, Console still shows old values
- Must set `trigger_redeploy = true` and wait 5-7 minutes

**Console Navigation:**
```
Google Cloud Console
  ↓
Vertex AI
  ↓
Agent Engine
  ↓
Select Agent
  ↓
Deployment details tab
  ↓
Scroll to "Environment" section
```

---

## Switching Back to Original Values

### Quick Method (Recommended)

**Windows:**

```cmd
cd terraform
switch_to_old.bat
```

The script will:
1. Restore original configuration from backup
2. Show preview of changes
3. Prompt for confirmation
4. Apply changes

**Manual Method:**

```cmd
cd terraform

# 1. Restore from backup
copy terraform.tfvars.backup terraform.tfvars

# 2. Verify
type terraform.tfvars

# 3. Preview changes
terraform plan

# 4. Apply changes
terraform apply
```

### Deploy with Original Values

**Step 1: Enable redeployment**

```cmd
notepad terraform.tfvars
```

Change:
```hcl
trigger_redeploy = true
```

**Step 2: Apply and deploy**

```cmd
terraform apply
```

**Step 3: Wait for deployment**

⏰ **Wait 5-7 minutes**

**Step 4: Verify in Console**

1. Refresh the Google Console page
2. Check **Deployment details** → **Environment**
3. Verify original values are restored:

```
OTEL_EXPORTER_OTLP_ENDPOINT: https://tabetha-unelemental-bibulously.ngrok-free.dev  ✓ RESTORED
OTEL_SERVICE_NAME: portal26_ngrok_agent  ✓ RESTORED (no _TEST)
OTEL_RESOURCE_ATTRIBUTES: portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local  ✓ RESTORED
```

**Step 5: Disable redeployment (for safety)**

```cmd
notepad terraform.tfvars
```

Change back:
```hcl
trigger_redeploy = false
```

Save the file.

---

## Complete Testing Workflow

### Full End-to-End Test

This workflow validates the entire Terraform configuration management system:

```cmd
# ========================================
# PHASE 1: Initial State
# ========================================

cd terraform

# Verify current configuration
type terraform.tfvars

# Check current values in Console
# Open: https://console.cloud.google.com/vertex-ai/agents/agent-engines

# ========================================
# PHASE 2: Switch to Dummy Values
# ========================================

# Switch configuration
switch_to_dummy.bat

# Enable redeployment
notepad terraform.tfvars
# Set: trigger_redeploy = true

# Deploy
terraform apply

# Wait 5-7 minutes

# Verify dummy values in Console
# Expected: _TEST suffix, tenant_test, testuser

# ========================================
# PHASE 3: Test with Dummy Configuration
# ========================================

# Test agents
cd ..
python test_tracer_provider.py

# Check telemetry
dir otel-data

# ========================================
# PHASE 4: Switch Back to Original
# ========================================

cd terraform

# Restore original configuration
switch_to_old.bat

# Enable redeployment
notepad terraform.tfvars
# Set: trigger_redeploy = true

# Deploy
terraform apply

# Wait 5-7 minutes

# Verify original values in Console
# Expected: No _TEST, tenant1, relusys

# ========================================
# PHASE 5: Final Verification
# ========================================

# Test agents with original config
cd ..
python test_tracer_provider.py

# Disable redeployment for safety
cd terraform
notepad terraform.tfvars
# Set: trigger_redeploy = false

# Save state
terraform apply
```

### Test Checklist

**Before Switching to Dummy:**
- [ ] Backup exists: `terraform.tfvars.backup`
- [ ] Current config noted
- [ ] Console shows original values

**After Switching to Dummy:**
- [ ] `terraform.tfvars` contains dummy values
- [ ] `.env` files updated with dummy values
- [ ] Console shows dummy values (after redeployment)
- [ ] Service names have `_TEST` suffix
- [ ] Resource attributes show `tenant_test`, `testuser`
- [ ] Agents respond to test queries

**After Switching Back:**
- [ ] `terraform.tfvars` contains original values
- [ ] `.env` files restored to original values
- [ ] Console shows original values (after redeployment)
- [ ] Service names without `_TEST` suffix
- [ ] Resource attributes show `tenant1`, `relusys`
- [ ] Agents respond to test queries

---

## Troubleshooting

### Console Shows Old Values After Switching

**Cause:** Agents not redeployed yet

**Solution:**
```cmd
cd terraform
notepad terraform.tfvars
# Set: trigger_redeploy = true

terraform apply
# Wait 5-7 minutes
# Refresh Console page
```

### Terraform Apply Fails with "charmap codec" Error

**Cause:** Windows terminal encoding issue (emoji in output)

**Status:** Not a real error - deployment likely succeeded

**Solution:**
```cmd
# Check if .env files were updated
type ..\portal26_ngrok_agent\.env

# Check Console to see if deployment actually succeeded
# If yes, ignore the error message
```

### Deployment Takes Longer Than Expected

**Cause:** Network latency or GCP processing delays

**Normal:** 5-7 minutes
**Acceptable:** up to 10 minutes
**Too long:** over 15 minutes

**Solution:**
```cmd
# Check deployment status in Console
# Go to: Vertex AI → Agent Engine → Select agent
# Check "Deployment details" tab for status

# If stuck, cancel and retry:
# Ctrl+C to cancel
terraform apply -auto-approve
```

### Can't Find Environment Section in Console

**Solution:**
1. Make sure you're on **Deployment details** tab (not "Observability")
2. Scroll down past URLs and IDs
3. Look for section titled **"Environment"**
4. Click on truncated values to see full text

### Values Look Truncated in Console

**Solution:**
- Click on the truncated value
- A popup or expanded view shows full text

### Terraform State Issues

**Problem:** State file corruption or conflicts

**Solution:**
```cmd
cd terraform

# Backup state
copy terraform.tfstate terraform.tfstate.backup

# Refresh state
terraform refresh

# If still issues, reinitialize
terraform init -reconfigure
```

### Agent Deployment Fails

**Check these:**

1. **Authentication:**
   ```bash
   gcloud auth list
   gcloud config get-value project
   ```

2. **Permissions:**
   - Vertex AI Agent Builder Admin role
   - Service Account Token Creator role

3. **Agent folder structure:**
   ```
   portal26_ngrok_agent/
   ├── agent.py
   ├── requirements.txt
   └── .env
   ```

4. **Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Network Connectivity Issues

**Symptoms:**
- `getaddrinfo failed`
- Connection timeout during deployment

**Solution:**
```bash
# Test connectivity
gcloud auth application-default print-access-token

# Check firewall/proxy settings
# Retry deployment after network stabilizes
```

---

## Quick Reference

### Key Commands

| Task | Command |
|------|---------|
| Switch to dummy | `cd terraform && switch_to_dummy.bat` |
| Switch to original | `cd terraform && switch_to_old.bat` |
| Enable deployment | Edit `terraform.tfvars`, set `trigger_redeploy = true` |
| Apply changes | `terraform apply` |
| Preview changes | `terraform plan` |
| Check .env file | `type ..\portal26_ngrok_agent\.env` |
| Test agents | `python test_tracer_provider.py` |

### Important URLs

| Resource | URL |
|----------|-----|
| **Agent Engine Console** | https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716 |
| **portal26_ngrok_agent** | Agent ID: `2658127084508938240` |
| **portal26_otel_agent** | Agent ID: `7483734085236424704` |

### File Locations

| File | Purpose |
|------|---------|
| `terraform/terraform.tfvars` | Active configuration |
| `terraform/terraform.tfvars.backup` | Original/production values |
| `terraform/terraform.tfvars.dummy` | Test/dummy values |
| `portal26_ngrok_agent/.env` | Agent environment file |
| `portal26_otel_agent/.env` | Agent environment file |

### Timing Reference

| Operation | Duration |
|-----------|----------|
| `terraform apply` (no redeploy) | 5-10 seconds |
| `terraform apply` (with redeploy) | 5-7 minutes |
| Agent query response | 2-5 seconds |
| Console refresh | Immediate |

---

## Best Practices

### Before Making Changes

1. ✅ Always check current configuration
2. ✅ Verify backup exists (`terraform.tfvars.backup`)
3. ✅ Run `terraform plan` to preview changes
4. ✅ Note current Console values (screenshot)

### During Changes

1. ✅ Use provided scripts (`switch_to_dummy.bat`, `switch_to_old.bat`)
2. ✅ Only enable `trigger_redeploy = true` when ready
3. ✅ Wait full 5-7 minutes for deployment
4. ✅ Monitor deployment in Console

### After Changes

1. ✅ Verify in Console that changes applied
2. ✅ Test agents with `test_tracer_provider.py`
3. ✅ Check telemetry data in `otel-data/`
4. ✅ Set `trigger_redeploy = false` for safety

### Safety Guidelines

1. ⚠️ Never commit `terraform.tfvars` to git (contains real endpoints)
2. ⚠️ Never commit `terraform.tfstate` (contains state)
3. ⚠️ Always keep backup before major changes
4. ⚠️ Test with dummy values before changing production
5. ⚠️ Don't interrupt deployment (wait for completion)

---

## Additional Resources

- **Terraform Guide:** `terraform/TERRAFORM_GUIDE.md`
- **Architecture Details:** `terraform/ARCHITECTURE.md`
- **Switching Workflow:** `terraform/SWITCHING_VALUES_GUIDE.md`
- **Console Validation:** `terraform/VALIDATE_IN_CONSOLE.md`
- **Main README:** `README.md`

---

## Summary

This guide covers:

✅ **Agent Deployment:** Deploy new or update existing agents
✅ **Testing:** Verify agents work correctly with test script
✅ **Configuration Management:** Use Terraform to manage environment variables
✅ **Dummy Values:** Test configuration changes safely
✅ **Console Validation:** Verify changes in Google Cloud Console
✅ **Restoration:** Switch back to original configuration
✅ **Troubleshooting:** Solve common issues

**Next Steps:**
1. Deploy agents using ADK CLI
2. Test with `test_tracer_provider.py`
3. Practice switching configurations
4. Validate changes in Console

For detailed Terraform setup, see `terraform/TERRAFORM_GUIDE.md`.
