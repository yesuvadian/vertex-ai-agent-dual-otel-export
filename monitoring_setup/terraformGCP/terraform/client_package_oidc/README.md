# GCP to Lambda Log Forwarding with OIDC Authentication - Complete Guide

## 🔐 Secure Version - OIDC Authentication Required

This package deploys GCP infrastructure to forward Reasoning Engine logs to AWS Lambda **with OIDC authentication**. Your Lambda must validate JWT tokens.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup Instructions](#detailed-setup-instructions)
- [What Gets Created](#what-gets-created)
- [Security Features](#security-features)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)
- [Comparison with No-Auth](#comparison-oidc-vs-no-auth)

---

## Prerequisites

### Required:
- [ ] Terraform installed
- [ ] GCP Project with Reasoning Engines
- [ ] Service Account with **Editor** and **Logging Admin** roles ⚠️
- [ ] AWS Lambda URL
- [ ] **Lambda has OIDC validation enabled** ⚠️

### Files Needed:
- Service account key JSON file
- Lambda URL (must support OIDC)
- Reasoning Engine IDs

### ⚠️ CRITICAL: Service Account Permissions

Your service account needs **TWO roles**:

1. **Editor** (`roles/editor`)
   - Create/modify Pub/Sub resources
   - Create service accounts

2. **Logging Admin** (`roles/logging.admin`) 
   - Create/modify log sinks
   - **Editor role does NOT include this!**

**To add Logging Admin role:**

```bash
# Via gcloud CLI:
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:YOUR-SA@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/logging.admin"
```

Or via GCP Console:
1. Go to: IAM & Admin → IAM
2. Find your service account
3. Click **Edit** → **ADD ANOTHER ROLE**
4. Select: **Logging Admin**
5. Click **SAVE**

---

## Quick Start

### 1. Get Service Account Key

**The included `appengine-sa-key.json` is an EXAMPLE only.**

Generate YOUR service account key:

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select YOUR GCP project
3. Click on your service account (with Editor role)
4. **KEYS** tab → **ADD KEY** → **Create new key** → **JSON**
5. **Replace** the example file with your downloaded key
6. Rename to: `appengine-sa-key.json`

### 2. Configure

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with YOUR values
```

Edit `terraform.tfvars` - **Required:**
- `gcp_project_id` - YOUR GCP Project ID
- `reasoning_engine_ids` - YOUR Reasoning Engine IDs (list format)
- `aws_lambda_url` - YOUR Lambda URL (must support OIDC!)

**How to get Reasoning Engine ID:**

1. Go to: https://console.cloud.google.com/vertex-ai/reasoning-engines
2. Select your project
3. Click on your Reasoning Engine
4. Copy the ID from the URL or details page
   - URL format: `.../reasoning-engines/REGION/REASONING_ENGINE_ID`
   - Example ID: `9162160575269044224`

**Optional Filters (for cost savings):**
- `log_severity_filter` - Filter by severity (e.g., `["ERROR", "CRITICAL"]`)
- `agent_ids` - Filter by specific agent IDs

**Example Configuration:**
```hcl
gcp_project_id = "my-gcp-project-123"
reasoning_engine_ids = ["9162160575269044224", "8213677864684355584"]
aws_lambda_url = "https://your-lambda-url.lambda-url.us-east-1.on.aws"
log_severity_filter = ["ERROR", "CRITICAL"]  # Optional: 80-90% cost savings
```

### 3. Deploy (One Command!)

Choose your platform:

**Windows PowerShell:**
```powershell
.\deploy.ps1
```

**Windows CMD:**
```cmd
deploy.bat
```

**Git Bash / Linux / Mac:**
```bash
./deploy.sh
```

The script automatically:
- Sets credentials
- Initializes Terraform
- Deploys infrastructure (including OIDC service account)

Type `yes` when Terraform asks to confirm.

---

## Detailed Setup Instructions

### Manual Deployment (if scripts don't work)

**Step 1: Set credentials**

```bash
# Linux/Mac
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"

# PowerShell
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"
```

**Step 2: Deploy**

```bash
terraform init
terraform apply
```

---

## What Gets Created

In YOUR GCP project:

### 1. Service Account
- **Name**: `pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com`
- **Purpose**: Generates OIDC tokens for authentication
- **Permissions**: Token Creator role (automatically managed by GCP Pub/Sub)

### 2. Pub/Sub Topic
- **Name**: `reasoning-engine-logs-topic`
- **Purpose**: Receives logs from Log Sink
- **Retention**: 7-day message retention

### 3. Pub/Sub Subscription
- **Name**: `reasoning-engine-to-lambda-oidc`
- **Purpose**: Pushes to your Lambda with OIDC token
- **Features**: Automatic retry on failure

### 4. Log Sink
- **Name**: `reasoning-engine-to-pubsub-oidc`
- **Purpose**: Routes Reasoning Engine logs
- **Features**: Configurable filters

---

## Security Features

### ✅ OIDC Authentication
Every request includes a JWT token in the Authorization header.

### ✅ Token Validation
Lambda must verify:
- Token signature (signed by Google)
- Token issuer (`https://accounts.google.com`)
- Token audience (matches Lambda URL)
- Token expiration (1 hour validity)

### ✅ Service Account Isolation
Dedicated service account for token generation, separate from deployment account.

### ✅ Audience Binding
Token is bound to specific Lambda URL - cannot be reused elsewhere.

---

## Comparison: OIDC vs No-Auth

| Feature | OIDC (This Package) | No-Auth (client_package) |
|---------|-------------------|-------------------------|
| Security | ✅ JWT token validation | ❌ Public endpoint |
| Lambda Complexity | Medium (token validation) | Simple (no validation) |
| Setup Complexity | Medium (service account) | Simple |
| Production Ready | ✅ Yes | ⚠️ Testing only |
| Token in Header | ✅ Yes | ❌ No |
| Compliance Ready | ✅ Yes | ❌ No |

**Recommendation**: Use OIDC for production deployments.

---

## Testing

After deployment:

### 1. Generate Test Log
Trigger a log in your Reasoning Engine that matches your filter criteria.

### 2. Check Lambda CloudWatch Logs
Look for incoming requests with OIDC token in headers:
```json
{
  "headers": {
    "authorization": "Bearer eyJhbGc..."
  }
}
```

### 3. Verify Authentication
Lambda should successfully validate and process the request.

### Test Checklist:
- [ ] Log appears in GCP Log Sink
- [ ] Message arrives in Pub/Sub subscription
- [ ] Lambda receives request with Authorization header
- [ ] Lambda validates token successfully
- [ ] Lambda processes log data

---

## Troubleshooting

### Lambda returns 401/403

**Cause**: OIDC token validation failed

**Check:**
- ✅ Token audience matches Lambda URL **exactly** (no trailing slash!)
- ✅ Lambda has `google-auth` package installed
- ✅ Lambda has internet access to fetch Google public keys
- ✅ Check Lambda logs for JWT validation errors

**Solution:**
```python
# In Lambda, verify audience matches exactly:
EXPECTED_AUDIENCE = "https://your-lambda-url.lambda-url.us-east-1.on.aws"
id_info = id_token.verify_oauth2_token(token, requests.Request(), EXPECTED_AUDIENCE)
```

### No logs arriving

**Cause**: Pub/Sub can't reach Lambda or filter is wrong

**Check:**
- ✅ Verify Reasoning Engine ID is correct
- ✅ Check GCP Log Sink filter in Cloud Console
- ✅ Test Pub/Sub subscription manually
- ✅ Lambda URL is correct in `terraform.tfvars`
- ✅ Lambda returns 200 for valid tokens

**Debug:**
```bash
# Check Pub/Sub subscription errors
gcloud pubsub subscriptions pull reasoning-engine-to-lambda-oidc --limit=1
```

### OIDC token invalid

**Cause**: Token signature invalid or expired

**Check:**
- ✅ Service account has Token Creator role (automatically granted)
- ✅ Check service account email matches subscription config
- ✅ Ensure audience matches Lambda URL exactly
- ✅ Token hasn't expired (valid 1 hour)
- ✅ Verify issuer: `https://accounts.google.com`

**Debug:**
```bash
# Check service account IAM policy
gcloud iam service-accounts get-iam-policy pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com
```

### Terraform deployment fails

**Check:**
- ✅ Service account has Editor role
- ✅ `appengine-sa-key.json` is valid
- ✅ All required fields in `terraform.tfvars` are filled
- ✅ Project ID is correct

---

## Cleanup

### Option 1: Terraform Destroy (Recommended)

```bash
terraform destroy
```

This removes:
- Service account
- Pub/Sub subscription and topic
- Log sink
- All IAM bindings

### Option 2: Cleanup Scripts

**PowerShell:**
```powershell
.\cleanup-with-user-account.ps1
```

**Bash:**
```bash
./cleanup-with-user-account.sh
```

**CMD:**
```cmd
cleanup-with-user-account.bat
```

---

## Next Steps

1. ✅ **Implement Lambda OIDC validation** (see `LAMBDA_OIDC_GUIDE.md`)
2. ✅ **Deploy Lambda** with dependencies (`google-auth`, `cryptography`)
3. ✅ **Deploy this infrastructure** using steps above
4. ✅ **Test with sample logs**
5. ✅ **Monitor for authentication errors** in CloudWatch
6. ✅ **Set up alerting** on Lambda failures

---

## 💡 Tips

- **Audience must match exactly** - No trailing slashes!
- **Monitor auth failures** - Set up CloudWatch alarms
- **Rotate service account keys** - Every 90 days
- **Test OIDC first** - Validate locally before deploying
- **Keep Lambda dependencies updated** - `google-auth` package

---

## 🆚 Need No-Auth Version?

If you just want to test without OIDC (not recommended for production):

- Use `../client_package/` instead
- No Lambda changes required
- Less secure (public endpoint)

---

## 📞 Support

- **Setup Issues**: Review this guide
- **Lambda Issues**: Check `LAMBDA_OIDC_GUIDE.md`
- **Authentication Issues**: Review OIDC token validation section
- **Terraform Errors**: Check GCP permissions

---

## 📚 Additional Documentation

| File | Purpose |
|------|---------|
| `LAMBDA_OIDC_GUIDE.md` | Complete Lambda OIDC implementation with code examples |
| `terraform.tfvars.example` | Configuration template |
| `main.tf` | Terraform variables and outputs |
| `gcp_log_sink_pubsub_oidc.tf` | Infrastructure definitions |

---

## 📦 For Administrators: Distributing to Clients

If you're distributing this package to clients, they will deploy in **their own GCP project** using their own credentials.

### What to Send Clients:
1. This `client_package_oidc/` folder (all files)
2. AWS Lambda URL (shared Lambda for all clients)
3. Their specific Reasoning Engine IDs

### What Clients Will Do:
1. Generate their own service account key from their GCP Console
2. Replace the example `appengine-sa-key.json` with their real key
3. Configure `terraform.tfvars` with their project ID and Engine IDs
4. Run deployment script for their platform

### Security Model:
- ✅ Each client uses their own service account key
- ✅ Each client deploys to their own GCP project
- ✅ All clients send logs to the same Lambda URL (with OIDC)
- ✅ Lambda validates each client's OIDC token
- ✅ Recommend 90-day key rotation

### Distribution Methods:
```bash
# Create a ZIP file
zip -r client-setup-oidc.zip client_package_oidc/

# Or share via Git repository
# Clients can clone and use directly
```

---

**Ready to deploy?** Make sure your Lambda has OIDC validation, then follow the Quick Start section above!
