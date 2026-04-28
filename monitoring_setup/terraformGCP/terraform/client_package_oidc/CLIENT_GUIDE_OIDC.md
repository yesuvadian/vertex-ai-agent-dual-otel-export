# Setup Instructions (WITH OIDC Authentication)

## ⚠️ IMPORTANT: Lambda Must Support OIDC

This configuration requires your AWS Lambda to **validate OIDC JWT tokens**. 

**Before deploying**, ensure your Lambda:
- Validates the `Authorization: Bearer <JWT>` header
- Verifies token issuer: `https://accounts.google.com`
- Verifies token audience matches your Lambda URL

See `LAMBDA_OIDC_GUIDE.md` for Lambda implementation details.

---

## Prerequisites
- Terraform installed
- GCP Project with Reasoning Engines
- Service Account with Editor role in your GCP project
- **AWS Lambda with OIDC validation enabled**

## Steps

### 1. Replace Service Account Key

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

**Optional Filters:**
- `log_severity_filter` - Filter by severity (e.g., `["ERROR", "CRITICAL"]`) for cost savings
- `agent_ids` - Filter by specific agent IDs
- `log_resource_types` - Filter by resource types
- `custom_log_filter` - Advanced custom filter expression

**Example:**
```hcl
gcp_project_id = "my-gcp-project-123"
reasoning_engine_ids = ["9162160575269044224", "8213677864684355584"]
aws_lambda_url = "https://your-lambda-url.lambda-url.us-east-1.on.aws"
log_severity_filter = ["ERROR", "CRITICAL"]  # Optional: for cost savings
```

### 3. Deploy (One Command!)

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

**Manual Deployment (if scripts don't work):**

Set credentials first:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"  # Linux/Mac
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\appengine-sa-key.json"     # PowerShell
```

Then deploy:
```bash
terraform init
terraform apply
```

## What Gets Created

In YOUR GCP project:
- **Service Account**: `pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com`
- **Pub/Sub Topic**: `reasoning-engine-logs-topic`
- **Pub/Sub Subscription**: Pushes to YOUR Lambda with OIDC token
- **Log Sink**: Routes YOUR Reasoning Engine logs
- **IAM Permissions**: Token Creator role for service account

## Security Features

✅ **OIDC Authentication**: Every request includes a JWT token  
✅ **Token Validation**: Lambda must verify token signature and claims  
✅ **Audience Verification**: Token audience matches Lambda URL  
✅ **Issuer Verification**: Token issued by Google (accounts.google.com)  

## Testing

After deployment:

1. **Generate a test log** in your Reasoning Engine
2. **Check Lambda logs** - you should see OIDC token in headers
3. **Verify authentication** - Lambda should validate and accept the token

## Troubleshooting

### Lambda returns 401/403
- ✅ Check Lambda has OIDC validation enabled
- ✅ Verify token audience matches Lambda URL
- ✅ Check Lambda logs for JWT validation errors

### No logs arriving
- ✅ Verify Reasoning Engine ID is correct
- ✅ Check GCP Log Sink filter in Cloud Console
- ✅ Test Pub/Sub subscription manually

### OIDC token invalid
- ✅ Verify service account has Token Creator role
- ✅ Check service account email matches subscription config
- ✅ Ensure audience matches Lambda URL exactly

## Cleanup

**Option 1: Terraform destroy**
```bash
terraform destroy
```

**Option 2: PowerShell cleanup script**
```powershell
.\cleanup-with-user-account.ps1
```

This removes:
- Service account
- Pub/Sub subscription and topic
- Log sink
- All IAM bindings

---

## Next Steps

1. ✅ Deploy this infrastructure
2. ✅ Verify Lambda validates OIDC tokens (see `LAMBDA_OIDC_GUIDE.md`)
3. ✅ Test with sample logs
4. ✅ Monitor for authentication errors
5. ✅ Set up alerting on Lambda failures
