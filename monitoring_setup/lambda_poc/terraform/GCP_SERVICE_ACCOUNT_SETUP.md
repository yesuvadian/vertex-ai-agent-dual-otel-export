# GCP Service Account Setup (Without gcloud CLI)

## 📋 **Overview**

This guide shows how to authenticate Terraform with Google Cloud using a **service account key file** instead of gcloud CLI. This is useful when:
- Client machines don't have gcloud CLI installed
- Running in CI/CD pipelines
- Automating deployments

---

## 🔐 **Step 1: Create Service Account in GCP Console**

### **1.1 Navigate to Service Accounts**
Go to: https://console.cloud.google.com/iam-admin/serviceaccounts

OR

1. Open GCP Console: https://console.cloud.google.com
2. Select your project
3. Navigate to: **IAM & Admin** → **Service Accounts**

### **1.2 Create Service Account**
1. Click **"Create Service Account"** button
2. Fill in details:
   - **Service account name:** `terraform-deployer`
   - **Service account ID:** `terraform-deployer` (auto-generated)
   - **Description:** `Service account for Terraform to deploy observability infrastructure`
3. Click **"Create and Continue"**

### **1.3 Grant Required Roles**
Add the following roles:

| Role | Purpose |
|------|---------|
| `Logging Admin` | Create and manage log sinks |
| `Pub/Sub Admin` | Create Pub/Sub topics and subscriptions |
| `Service Account Admin` | Create service accounts for OIDC |
| `Secret Manager Admin` | Manage shared secrets |
| `Project IAM Admin` | Grant IAM permissions to service accounts |

**How to add:**
1. In the "Grant this service account access" section
2. Click "Select a role" dropdown
3. Search and add each role above
4. Click **"Continue"**
5. Click **"Done"**

---

## 🔑 **Step 2: Generate JSON Key File**

### **2.1 Navigate to Service Account Keys**
1. Click on the newly created service account (`terraform-deployer`)
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**

### **2.2 Download Key**
1. Select key type: **JSON** (recommended)
2. Click **"Create"**
3. Key file will be downloaded automatically (e.g., `terraform-deployer-abc123.json`)
4. **Save this file securely** - it contains credentials!

**Example filename:** `agentic-ai-integration-490716-1234567890ab.json`

### **2.3 Rename Key File (Optional)**
For easier reference, rename to:
```
terraform-sa-key.json
```

---

## 💻 **Step 3: Configure Terraform to Use Key**

### **Method 1: Environment Variable (Recommended)**

This is the **cleanest and most secure** method.

#### **Windows (PowerShell)**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\terraform-sa-key.json"
```

**Example:**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\yesuv\keys\terraform-sa-key.json"
```

#### **Windows (Command Prompt)**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\terraform-sa-key.json
```

#### **Linux/Mac**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/terraform-sa-key.json"
```

**To make it permanent (Linux/Mac):**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/user/keys/terraform-sa-key.json"
```

---

### **Method 2: Terraform Variable (Alternative)**

#### **Option A: Add to terraform.tfvars**
```hcl
gcp_credentials_file = "C:/Users/yesuv/keys/terraform-sa-key.json"
```

#### **Option B: Add to main.tf**
Update the provider block in `main.tf`:
```hcl
provider "google" {
  project     = var.gcp_project_id
  region      = var.gcp_region
  credentials = file("C:/path/to/terraform-sa-key.json")  # Add this line
}
```

**Note:** Use forward slashes `/` even on Windows in Terraform.

---

## ✅ **Step 4: Verify Setup**

### **4.1 Check Environment Variable (Method 1)**

**Windows (PowerShell):**
```powershell
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```

**Windows (CMD):**
```cmd
echo %GOOGLE_APPLICATION_CREDENTIALS%
```

**Linux/Mac:**
```bash
echo $GOOGLE_APPLICATION_CREDENTIALS
```

**Expected Output:** Path to your key file

### **4.2 Test Terraform Authentication**

```bash
cd terraform/
terraform init
```

**Success:** You'll see:
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
Terraform has been successfully initialized!
```

**Failure:** You'll see an error like:
```
Error: google: could not find default credentials
```

---

## 🚀 **Step 5: Run Terraform**

Once authenticated:

```bash
# Initialize (if not done already)
terraform init

# Review what will be created
terraform plan

# Deploy infrastructure
terraform apply
```

---

## 🔒 **Security Best Practices**

### **1. Never Commit Key Files to Git**

Add to `.gitignore`:
```
# Service account keys
*.json
terraform-sa-key.json
*-key.json

# Terraform files
*.tfstate
*.tfstate.backup
.terraform/
```

### **2. Secure Key Storage**

**Good:**
- Store in a secure directory with restricted permissions
- Use environment variables
- Use secret management tools (Vault, AWS Secrets Manager)

**Bad:**
- ❌ Commit to Git
- ❌ Share via email
- ❌ Store in public locations
- ❌ Hard-code in scripts

### **3. Key Rotation**

**Recommended:** Rotate keys every 90 days

**How to rotate:**
1. Create new key for same service account
2. Update environment variable to point to new key
3. Test Terraform
4. Delete old key in GCP Console

### **4. Principle of Least Privilege**

Only grant roles that Terraform actually needs. Review the roles list and remove any unnecessary permissions.

### **5. Separate Keys per Environment**

Create different service accounts for:
- Development
- Staging
- Production

---

## 🐛 **Troubleshooting**

### **Issue 1: "Could not find default credentials"**

**Cause:** Environment variable not set or pointing to wrong file

**Solution:**
```bash
# Check if variable is set
echo $GOOGLE_APPLICATION_CREDENTIALS

# Set it again
export GOOGLE_APPLICATION_CREDENTIALS="/correct/path/to/key.json"
```

---

### **Issue 2: "Permission denied" errors during terraform apply**

**Cause:** Service account missing required roles

**Solution:**
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click on `terraform-deployer` service account
3. Go to "Permissions" tab
4. Verify all required roles are present:
   - Logging Admin
   - Pub/Sub Admin
   - Service Account Admin
   - Secret Manager Admin
   - Project IAM Admin

---

### **Issue 3: Key file not found**

**Cause:** Wrong file path or file doesn't exist

**Solution:**
```bash
# Verify file exists (Windows PowerShell)
Test-Path "C:\path\to\terraform-sa-key.json"

# Verify file exists (Linux/Mac)
ls -l /path/to/terraform-sa-key.json

# Use absolute path, not relative
```

---

### **Issue 4: "Invalid credentials" error**

**Cause:** 
- Key file is corrupted
- Key was deleted in GCP Console
- Wrong project

**Solution:**
1. Download new key from GCP Console
2. Verify project ID matches in key file:
   ```bash
   cat terraform-sa-key.json | grep project_id
   ```
3. Update environment variable with new key

---

## 📝 **Complete Example Workflow**

### **Scenario: Fresh Machine Setup**

```bash
# 1. Download service account key from GCP Console
#    Save to: C:\Users\yesuv\keys\terraform-sa-key.json

# 2. Set environment variable (Windows PowerShell)
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\yesuv\keys\terraform-sa-key.json"

# 3. Verify
echo $env:GOOGLE_APPLICATION_CREDENTIALS
# Output: C:\Users\yesuv\keys\terraform-sa-key.json

# 4. Navigate to terraform directory
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup\lambda_poc\terraform

# 5. Copy and edit config
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 6. Initialize Terraform
terraform init

# 7. Plan deployment
terraform plan

# 8. Deploy
terraform apply
```

---

## 📚 **Key File Format Reference**

Your JSON key file contains:

```json
{
  "type": "service_account",
  "project_id": "agentic-ai-integration-490716",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "terraform-deployer@agentic-ai-integration-490716.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

**Important fields:**
- `project_id` - Must match your GCP project
- `client_email` - Service account email
- `private_key` - Used for authentication (keep secret!)

---

## 🔄 **Comparison: gcloud CLI vs Service Account Key**

| Aspect | gcloud CLI | Service Account Key |
|--------|------------|---------------------|
| **Setup** | Install gcloud, run login | Download JSON file |
| **Best For** | Interactive use, development | CI/CD, automation |
| **Security** | User credentials | Service account credentials |
| **Portability** | Machine-specific | Works anywhere |
| **Rotation** | Re-login periodically | Manual key rotation |
| **Audit** | User identity | Service account identity |

**Recommendation:** 
- **Development:** Use gcloud CLI (easier)
- **Production/CI/CD:** Use service account key (more reliable)

---

## ✅ **Checklist**

Before running Terraform, verify:

- [ ] Service account created in GCP Console
- [ ] All required roles granted (5 roles)
- [ ] JSON key file downloaded
- [ ] Key file saved in secure location
- [ ] Environment variable set correctly
- [ ] Environment variable verified (echo command)
- [ ] Key file NOT committed to Git
- [ ] terraform.tfvars configured
- [ ] AWS credentials also configured

---

## 📞 **Need Help?**

If authentication fails:
1. Check environment variable is set correctly
2. Verify file path is correct (use absolute paths)
3. Confirm service account has all required roles
4. Try creating a new key
5. Check GCP Console for any IAM policy issues

---

## 🔗 **Related Documentation**

- [Terraform Permissions Guide](./TERRAFORM_PERMISSIONS.md) - Full IAM requirements
- [Quick Start Guide](./TERRAFORM_QUICK_START.md) - Deployment steps
- [README](./README.md) - Main documentation

**Official Google Documentation:**
- Service Accounts: https://cloud.google.com/iam/docs/service-accounts
- Authentication: https://cloud.google.com/docs/authentication/getting-started

---

**Last Updated:** 2024-04-23
**Target Audience:** DevOps Engineers, CI/CD Pipeline Administrators
