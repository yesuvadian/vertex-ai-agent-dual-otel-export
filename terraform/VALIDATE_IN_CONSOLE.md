# How to Validate in Google Console

## 🚀 Quick Start

### Step 1: Switch to Dummy Values

```cmd
cd terraform
switch_to_dummy.bat
```

This will:
1. Copy dummy configuration
2. Show preview of changes
3. Ask for confirmation
4. Update .env files

**Note**: This only updates .env files, agents are NOT redeployed yet.

---

### Step 2: Deploy with Dummy Values (Optional)

If you want to actually deploy agents with dummy values:

```cmd
notepad terraform.tfvars
```

Change line:
```hcl
trigger_redeploy = true  # Change from false to true
```

Save and apply:
```cmd
terraform apply
```

⏰ **Wait 2-3 minutes for deployment to complete**

---

### Step 3: Validate in Google Console

#### Navigate to Agent Engine

1. Open browser: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716

2. You should see two agents:
   - `portal26_ngrok_agent` (ID: 2658127084508938240)
   - `portal26_otel_agent` (ID: 7483734085236424704)

#### Check portal26_ngrok_agent

1. Click on **portal26_ngrok_agent**

2. Go to **Deployment details** tab

3. Scroll down to **Environment** section

4. Verify you see:

```
GOOGLE_CLOUD_LOCATION: us-central1
GOOGLE_CLOUD_PROJECT: agentic-ai-integration-490716
OTEL_EXPORTER_OTLP_ENDPOINT: https://dummy-ngrok-endpoint.ngrok-free.dev  ← CHANGED
OTEL_SERVICE_NAME: portal26_ngrok_agent_TEST  ← CHANGED
OTEL_RESOURCE_ATTRIBUTES: portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=ngrok-test  ← CHANGED
```

📸 **Screenshot this for reference**

#### Check portal26_otel_agent

1. Go back and click on **portal26_otel_agent**

2. Go to **Deployment details** tab

3. Scroll down to **Environment** section

4. Verify you see:

```
OTEL_EXPORTER_OTLP_ENDPOINT: https://otel-test.portal26.in:4318  ← CHANGED
OTEL_SERVICE_NAME: portal26_otel_agent_TEST  ← CHANGED
OTEL_RESOURCE_ATTRIBUTES: portal26.tenant_id=tenant_test,portal26.user.id=testuser,agent.type=otel-test  ← CHANGED
```

📸 **Screenshot this for reference**

---

### Step 4: Switch Back to Old Values

```cmd
cd terraform
switch_to_old.bat
```

This will:
1. Copy old configuration from backup
2. Show preview of changes
3. Ask for confirmation
4. Update .env files

To redeploy with old values:

```cmd
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

### Step 5: Validate Old Values in Console

1. Refresh the Google Console page

2. Check **portal26_ngrok_agent** → **Deployment details** → **Environment**

3. Verify you see OLD values:

```
OTEL_EXPORTER_OTLP_ENDPOINT: https://tabetha-unelemental-bibulously.ngrok-free.dev  ← BACK
OTEL_SERVICE_NAME: portal26_ngrok_agent  ← BACK (no _TEST)
OTEL_RESOURCE_ATTRIBUTES: portal26.tenant_id=tenant1,portal26.user.id=relusys,agent.type=ngrok-local  ← BACK
```

✅ **Verification complete!**

---

## 📊 What You'll See in Console

### Console Navigation Path

```
Google Cloud Console
  ↓
Vertex AI
  ↓
Agent Engine
  ↓
Select Agent (portal26_ngrok_agent or portal26_otel_agent)
  ↓
Deployment details tab
  ↓
Scroll to "Environment" section
```

### Environment Section Layout

The Environment section shows all environment variables as key-value pairs:

```
Environment
┌─────────────────────────────────────────────────────────┐
│ GOOGLE_CLOUD_LOCATION             us-central1          │
│ GOOGLE_CLOUD_PROJECT              agentic-ai-inte...   │
│ GOOGLE_CLOUD_AGENT_ENGINE_...     true                 │
│ OTEL_EXPORTER_OTLP_ENDPOINT       https://dummy-...    │
│ OTEL_SERVICE_NAME                 portal26_ngrok_...   │
│ OTEL_RESOURCE_ATTRIBUTES          portal26.tenant...   │
└─────────────────────────────────────────────────────────┘
```

Click on any value to see the full text (some are truncated).

---

## 🔍 Validation Checklist

### After Switching to Dummy

- [ ] Console shows `OTEL_EXPORTER_OTLP_ENDPOINT` = `https://dummy-ngrok-endpoint.ngrok-free.dev`
- [ ] Console shows `OTEL_SERVICE_NAME` ends with `_TEST`
- [ ] Console shows `OTEL_RESOURCE_ATTRIBUTES` contains `tenant_test`
- [ ] Console shows `OTEL_RESOURCE_ATTRIBUTES` contains `testuser`
- [ ] Console shows `agent.type` = `ngrok-test` or `otel-test`

### After Switching Back to Old

- [ ] Console shows `OTEL_EXPORTER_OTLP_ENDPOINT` = `https://tabetha-unelemental-bibulously.ngrok-free.dev`
- [ ] Console shows `OTEL_SERVICE_NAME` = `portal26_ngrok_agent` (no `_TEST`)
- [ ] Console shows `OTEL_RESOURCE_ATTRIBUTES` contains `tenant1`
- [ ] Console shows `OTEL_RESOURCE_ATTRIBUTES` contains `relusys`
- [ ] Console shows `agent.type` = `ngrok-local` or `otel-direct`

---

## 🚨 Important Notes

### Environment Variables Update Timing

**Without Redeployment** (`trigger_redeploy = false`):
- ✅ `.env` files updated immediately
- ❌ Agents still using old values
- ❌ Console shows old values

**With Redeployment** (`trigger_redeploy = true`):
- ✅ `.env` files updated
- ✅ Agents redeployed with new values (2-3 min)
- ✅ Console shows new values after deployment

**To see changes in Console**: You MUST redeploy with `trigger_redeploy = true`

---

## 🖼️ Console Screenshots Reference

### Where to Find Environment Variables

1. **Main View**:
   - https://console.cloud.google.com/vertex-ai/agents/agent-engines

2. **Agent Details**:
   - Click on agent name

3. **Deployment Tab**:
   - Click "Deployment details" tab (next to "Observability")

4. **Environment Section**:
   - Scroll down past "Resource name", "Display name", "Query URL"
   - Look for "Environment" section with key-value pairs

---

## 💡 Troubleshooting

### Console Shows Old Values After Switching

**Cause**: Agents not redeployed yet

**Solution**:
1. Edit `terraform.tfvars`
2. Set `trigger_redeploy = true`
3. Run `terraform apply`
4. Wait 2-3 minutes
5. Refresh console page

### Can't Find Environment Section

**Solution**:
1. Make sure you're on "Deployment details" tab (not "Observability")
2. Scroll down past the URLs and IDs
3. Look for section titled "Environment"

### Values Look Truncated in Console

**Solution**:
- Click on the truncated value
- A popup or expanded view will show the full text

---

## ✅ Complete Test Workflow

```cmd
# 1. Switch to dummy
cd terraform
switch_to_dummy.bat
notepad terraform.tfvars  # Set trigger_redeploy = true
terraform apply

# 2. Wait 2-3 minutes

# 3. Validate in Console
# Open: https://console.cloud.google.com/vertex-ai/agents/agent-engines
# Check Environment section for dummy values

# 4. Switch back
switch_to_old.bat
notepad terraform.tfvars  # Set trigger_redeploy = true
terraform apply

# 5. Wait 2-3 minutes

# 6. Validate in Console again
# Verify old values are back
```

---

## 📖 Quick Links

- **GCP Console - Agent Engine**: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716
- **portal26_ngrok_agent**: Agent ID `2658127084508938240`
- **portal26_otel_agent**: Agent ID `7483734085236424704`

---

**Ready to validate?** Run:
```cmd
cd terraform
switch_to_dummy.bat
```
