# How to Upload to GitHub (titaniam/lambda-gcp-otel-preprocessor)

## Files to Upload

Upload the entire `terraformGCP/` folder structure to the repository:

```
lambda-gcp-otel-preprocessor/   (GitHub repo root)
├── README.md                    (from terraformGCP/README.md)
├── terraform/
│   ├── .gitignore
│   ├── DISTRIBUTE.md
│   ├── GCP_PERMISSIONS.md
│   └── client_package/
│       ├── .gitignore
│       ├── README.md
│       ├── CLIENT_GUIDE.md
│       ├── CLIENT_GUIDE_USER_AUTH.md
│       ├── main.tf
│       ├── gcp_log_sink_pubsub.tf
│       ├── terraform.tfvars.example
│       ├── appengine-sa-key.json (EXAMPLE ONLY)
│       ├── deploy.sh
│       ├── deploy.ps1
│       ├── deploy.bat
│       ├── deploy-with-user-account.sh
│       ├── deploy-with-user-account.ps1
│       ├── deploy-with-user-account.bat
│       ├── cleanup.ps1
│       ├── cleanup-with-user-account.sh
│       ├── cleanup-with-user-account.ps1
│       └── cleanup-with-user-account.bat
```

## CRITICAL: Files to EXCLUDE

**DO NOT upload:**
- ❌ `terraform.tfvars` (contains your actual project ID and config)
- ❌ `terraform.tfstate*` (contains infrastructure state)
- ❌ `.terraform/` folder (Terraform cache)
- ❌ Real service account keys
- ❌ `client_package.zip`

**Only upload `terraform.tfvars.example`** - clients will copy and configure it.

## Upload Steps

### Option 1: Via GitHub Web UI (Easiest)

1. **Go to:** https://github.com/titaniam/lambda-gcp-otel-preprocessor
2. **Click:** "Add file" → "Upload files"
3. **Drag the entire `terraformGCP` folder** (excluding sensitive files)
4. **Commit message:** "Add GCP to AWS Lambda log sink infrastructure"
5. **Click:** "Commit changes"

### Option 2: Via Git Command Line

```bash
# 1. Clone the empty repo
cd /c/Users/yesuv
gh repo clone titaniam/lambda-gcp-otel-preprocessor

# 2. Copy files
cd lambda-gcp-otel-preprocessor
cp -r /c/Yesu/ai_agent_projectgcp/monitoring_setup/terraformGCP/* .

# 3. Remove sensitive files
rm -f terraform/client_package/terraform.tfvars
rm -f terraform/client_package/terraform.tfstate*
rm -rf terraform/client_package/.terraform/
rm -f terraform/client_package.zip

# 4. Commit and push
git add .
git commit -m "Add GCP to AWS Lambda log sink infrastructure"
git push origin main
```

## Verify Before Pushing

Run this checklist:

```bash
# Check what will be committed
git status

# Make sure these DON'T appear:
# - terraform.tfvars (only .example should be there)
# - *.tfstate files
# - .terraform/ folder
# - Real service account keys

# If you see them, add to .gitignore:
echo "terraform.tfvars" >> terraform/client_package/.gitignore
git add .gitignore
```

## After Upload

Create a good README.md in the repo root explaining:
- What this repo contains
- How clients use it
- Quick start guide
- Link to CLIENT_GUIDE.md

## Security Checklist

✅ Uploaded terraform.tfvars.example (template)  
✅ Did NOT upload terraform.tfvars (actual config)  
✅ Did NOT upload real service account keys  
✅ Did NOT upload .terraform/ folder  
✅ Did NOT upload terraform.tfstate files  
✅ Added proper .gitignore files  

---

**Ready to upload?** Follow Option 1 (web UI) or Option 2 (command line) above.
