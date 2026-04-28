# Upload terraformGCP to GitHub Repository

## Quick Start

### Method 1: Web UI (Recommended - Easiest!)

1. **Prepare files:**
   ```powershell
   cd C:\Yesu\ai_agent_projectgcp\monitoring_setup\terraformGCP
   .\prepare-for-upload.ps1
   ```

2. **Go to GitHub:**
   - Visit: https://github.com/titaniam/lambda-gcp-otel-preprocessor
   - Click: "Add file" → "Upload files"

3. **Upload:**
   - Drag the entire `terraformGCP` folder contents
   - Commit message: "Add GCP to Lambda log sink Terraform infrastructure"
   - Click "Commit changes"

### Method 2: Git Command Line

```powershell
# 1. Clone the repository
cd C:\Users\yesuv
gh auth login  # If not already logged in
gh repo clone titaniam/lambda-gcp-otel-preprocessor

# 2. Copy your prepared files
cd lambda-gcp-otel-preprocessor
Copy-Item C:\Yesu\ai_agent_projectgcp\monitoring_setup\terraformGCP\* -Recurse -Force

# 3. Stage and commit
git add .
git status  # Verify no sensitive files are staged
git commit -m "Add GCP to Lambda log sink Terraform infrastructure"
git push origin main
```

## What Will Be Uploaded

```
lambda-gcp-otel-preprocessor/  (GitHub repo)
│
├── README.md                   (Main overview)
├── UPLOAD_INSTRUCTIONS.md      (This guide)
│
└── terraform/
    ├── .gitignore
    ├── DISTRIBUTE.md           (For admins)
    ├── GCP_PERMISSIONS.md      (Permission requirements)
    │
    └── client_package/         (Ready to distribute)
        ├── README.md
        ├── CLIENT_GUIDE.md
        ├── CLIENT_GUIDE_USER_AUTH.md
        │
        ├── main.tf
        ├── gcp_log_sink_pubsub.tf
        ├── terraform.tfvars.example
        ├── appengine-sa-key.json (EXAMPLE)
        │
        ├── deploy.sh
        ├── deploy.ps1
        ├── deploy.bat
        ├── deploy-with-user-account.sh
        ├── deploy-with-user-account.ps1
        ├── deploy-with-user-account.bat
        │
        ├── cleanup.ps1
        ├── cleanup-with-user-account.sh
        ├── cleanup-with-user-account.ps1
        └── cleanup-with-user-account.bat
```

## Security Check ✓

**Files that WILL be uploaded:**
- ✅ terraform.tfvars.example (template only)
- ✅ appengine-sa-key.json (example only)
- ✅ All .tf files
- ✅ All deployment scripts
- ✅ All documentation

**Files that will NOT be uploaded:**
- ❌ terraform.tfvars (your actual config)
- ❌ terraform.tfstate* (infrastructure state)
- ❌ .terraform/ (Terraform cache)
- ❌ Real service account keys
- ❌ client_package.zip

## After Upload - Create a Good README

Once uploaded, edit the main README.md to include:

```markdown
# GCP to AWS Lambda Log Forwarder

Terraform infrastructure to forward GCP Vertex AI Reasoning Engine logs to AWS Lambda.

## Quick Start

1. Download or clone this repository
2. Navigate to `terraform/client_package/`
3. Follow the [CLIENT_GUIDE.md](terraform/client_package/CLIENT_GUIDE.md)

## What This Does

- Creates a GCP Log Sink to capture Reasoning Engine logs
- Sets up Pub/Sub Topic and Subscription
- Pushes logs to your AWS Lambda endpoint

## Two Deployment Methods

1. **Service Account Key** (Default) - See [CLIENT_GUIDE.md](terraform/client_package/CLIENT_GUIDE.md)
2. **User Account** (No key needed) - See [CLIENT_GUIDE_USER_AUTH.md](terraform/client_package/CLIENT_GUIDE_USER_AUTH.md)

## For Admins

See [DISTRIBUTE.md](terraform/DISTRIBUTE.md) for how to distribute this to clients.
```

## Verification Steps

After upload, verify:

1. **Check the repository:** https://github.com/titaniam/lambda-gcp-otel-preprocessor
2. **Verify files exist:**
   - terraform/client_package/CLIENT_GUIDE.md
   - terraform/client_package/terraform.tfvars.example
   - All deployment scripts (.sh, .ps1, .bat)
3. **Verify sensitive files are NOT there:**
   - terraform.tfvars should NOT exist
   - .terraform/ should NOT exist
   - terraform.tfstate should NOT exist

## Ready?

Run the prepare script first:
```powershell
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup\terraformGCP
.\prepare-for-upload.ps1
```

Then upload via GitHub web UI or git command line!
