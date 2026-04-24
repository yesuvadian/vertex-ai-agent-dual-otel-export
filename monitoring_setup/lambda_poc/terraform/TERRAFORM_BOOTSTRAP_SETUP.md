# Terraform Bootstrap - Automated GCP Service Account Setup

## 🎯 **What This Does**

Automates the creation of a GCP service account with all required permissions for deploying the main infrastructure. **No manual Console clicking required!**

**Instead of:**
- ❌ Manually creating service account in Console
- ❌ Manually granting 6 different IAM roles
- ❌ Manually downloading key file

**You get:**
- ✅ Run one Terraform command
- ✅ Service account created automatically
- ✅ All permissions granted automatically
- ✅ Key file generated automatically

---

## 📋 **Prerequisites**

### **What You Need:**

1. **gcloud CLI installed** (for initial bootstrap only)
   ```bash
   gcloud --version
   ```

2. **Terraform installed**
   ```bash
   terraform --version  # >= 1.0
   ```

3. **Your personal GCP credentials** (Owner role)
   ```bash
   gcloud auth application-default login
   ```

4. **GCP Project ID**
   - Example: `agentic-ai-integration-490716`

---

## 🚀 **Quick Start (5 Minutes)**

### **Step 1: Navigate to Bootstrap Directory**
```bash
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup\lambda_poc\terraform\bootstrap
```

### **Step 2: Configure**
```bash
# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit with your project ID
notepad terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
gcp_project_id = "agentic-ai-integration-490716"  # Your project
gcp_region     = "us-central1"
```

### **Step 3: Deploy**
```bash
# Initialize
terraform init

# Review what will be created
terraform plan

# Create service account
terraform apply
```

Type `yes` when prompted.

### **Step 4: Save Key File**
```bash
# Extract and save the key
terraform output -raw service_account_key_file_content > terraform-sa-key.json
```

### **Step 5: Set Environment Variable**

**Windows (PowerShell):**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\terraform-sa-key.json"
```

**Windows (CMD):**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\terraform-sa-key.json
```

**Linux/Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"
```

### **Step 6: Deploy Main Infrastructure**
```bash
# Go to main terraform directory
cd ..

# Deploy main infrastructure
terraform init
terraform apply
```

**Done!** 🎉

---

## 📂 **Directory Structure**

```
terraform/
├── bootstrap/                    ← Bootstrap Terraform (run first)
│   ├── main.tf                  ← Service account creation
│   ├── terraform.tfvars.example ← Example config
│   ├── terraform.tfvars         ← Your config (gitignored)
│   ├── .gitignore               ← Protect sensitive files
│   └── terraform-sa-key.json    ← Generated key (gitignored)
│
├── main.tf                       ← Main infrastructure
├── gcp_log_sink_pubsub.tf
├── aws_lambda_multi_customer.tf
└── ...
```

---

## 🔍 **What Gets Created**

### **1. Service Account**
```
Name: terraform-deployer
Email: terraform-deployer@agentic-ai-integration-490716.iam.gserviceaccount.com
```

### **2. IAM Roles Granted**

| Role | Purpose |
|------|---------|
| `roles/logging.admin` | Create and manage log sinks |
| `roles/pubsub.admin` | Create Pub/Sub topics and subscriptions |
| `roles/iam.serviceAccountAdmin` | Create service accounts for OIDC |
| `roles/iam.serviceAccountUser` | Use service accounts |
| `roles/secretmanager.admin` | Manage shared secrets |
| `roles/resourcemanager.projectIamAdmin` | Grant IAM permissions |

### **3. Service Account Key**
- JSON key file
- Used for authenticating Terraform
- Stored as: `terraform-sa-key.json`

---

## 📝 **Step-by-Step Guide**

### **Phase 1: Initial Setup (First Time Only)**

#### **1.1 Authenticate with Your Personal Account**
```bash
# Login to GCP
gcloud auth application-default login

# Verify authentication
gcloud auth list

# Set default project
gcloud config set project agentic-ai-integration-490716
```

#### **1.2 Verify Your Permissions**
```bash
# Check if you're Owner/Editor
gcloud projects get-iam-policy agentic-ai-integration-490716 \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)" \
  --format="table(bindings.role)"
```

**Expected:** You should see `roles/owner` or `roles/editor`

---

### **Phase 2: Run Bootstrap Terraform**

#### **2.1 Navigate to Bootstrap Directory**
```bash
cd terraform/bootstrap/
```

#### **2.2 Create Configuration File**
```bash
# Copy example
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
```

**Edit `terraform.tfvars`:**
```hcl
gcp_project_id     = "agentic-ai-integration-490716"
gcp_region         = "us-central1"
service_account_id = "terraform-deployer"
```

#### **2.3 Initialize Terraform**
```bash
terraform init
```

**Expected Output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
Terraform has been successfully initialized!
```

#### **2.4 Review Plan**
```bash
terraform plan
```

**Review what will be created:**
- 1 service account
- 6 IAM role bindings
- 1 service account key

#### **2.5 Apply (Create Resources)**
```bash
terraform apply
```

**Type:** `yes`

**Wait:** 30-60 seconds

**Expected Output:**
```
Apply complete! Resources: 8 added, 0 changed, 0 destroyed.

Outputs:

instructions = <<EOT
============================================================================
Service Account Created Successfully!
============================================================================
...
EOT

service_account_email = "terraform-deployer@agentic-ai-integration-490716.iam.gserviceaccount.com"
```

---

### **Phase 3: Extract and Save Key**

#### **3.1 View Service Account Email**
```bash
terraform output service_account_email
```

#### **3.2 Save Key to File**
```bash
# Extract key and save
terraform output -raw service_account_key_file_content > terraform-sa-key.json

# Verify file was created (Windows)
dir terraform-sa-key.json

# Verify file was created (Linux/Mac)
ls -lh terraform-sa-key.json
```

**Expected:** File size ~2-3 KB

#### **3.3 Verify Key Format**
```bash
# Check if valid JSON (Windows PowerShell)
Get-Content terraform-sa-key.json | ConvertFrom-Json | Select-Object type, project_id, client_email

# Check if valid JSON (Linux/Mac)
cat terraform-sa-key.json | jq '.type, .project_id, .client_email'
```

**Expected Output:**
```
type: service_account
project_id: agentic-ai-integration-490716
client_email: terraform-deployer@...iam.gserviceaccount.com
```

---

### **Phase 4: Configure Environment**

#### **4.1 Set Environment Variable**

**Windows PowerShell:**
```powershell
# Set for current session
$env:GOOGLE_APPLICATION_CREDENTIALS="$pwd\terraform-sa-key.json"

# Verify
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```

**Windows CMD:**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\terraform-sa-key.json
echo %GOOGLE_APPLICATION_CREDENTIALS%
```

**Linux/Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"
echo $GOOGLE_APPLICATION_CREDENTIALS
```

#### **4.2 Make Permanent (Optional)**

**Windows (System Environment Variable):**
1. Search "Environment Variables" in Start menu
2. Click "Environment Variables"
3. Under "User variables", click "New"
4. Variable name: `GOOGLE_APPLICATION_CREDENTIALS`
5. Variable value: `C:\path\to\terraform-sa-key.json`

**Linux/Mac (Add to shell profile):**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/terraform-sa-key.json"' >> ~/.bashrc
source ~/.bashrc
```

---

### **Phase 5: Deploy Main Infrastructure**

#### **5.1 Navigate to Main Terraform Directory**
```bash
cd ..  # Go back to main terraform directory
pwd    # Should be: .../terraform/
```

#### **5.2 Verify You're Using Service Account**
```bash
# Test authentication
gcloud auth list

# The service account key will be used by Terraform (not shown in gcloud auth list)
```

#### **5.3 Configure Main Infrastructure**
```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your configuration
```

#### **5.4 Deploy**
```bash
terraform init
terraform plan
terraform apply
```

**Success!** Main infrastructure deployed using service account.

---

## 🔐 **Security Best Practices**

### **1. Protect the Key File**

```bash
# ✅ GOOD: Key is in gitignore
cat bootstrap/.gitignore | grep "*.json"

# ❌ BAD: Never commit to Git
git add terraform-sa-key.json  # DON'T DO THIS!
```

### **2. Secure Storage**

**Good locations:**
- `terraform/bootstrap/` (gitignored)
- Secure key management system (Vault, etc.)
- Encrypted storage

**Bad locations:**
- Desktop
- Downloads folder
- Shared network drives
- Email attachments

### **3. Key Rotation**

**Rotate every 90 days:**

```bash
# Delete old key
terraform destroy -target=google_service_account_key.terraform_deployer_key

# Create new key
terraform apply

# Extract new key
terraform output -raw service_account_key_file_content > terraform-sa-key.json
```

### **4. Principle of Least Privilege**

The service account only has permissions needed for infrastructure deployment. It does NOT have:
- ❌ Owner role
- ❌ Editor role
- ❌ Compute Admin
- ❌ Other unnecessary permissions

---

## 🔄 **Updating Service Account**

### **Add New Permission**

Edit `bootstrap/main.tf`, add new role binding:
```hcl
resource "google_project_iam_member" "new_permission" {
  project = var.gcp_project_id
  role    = "roles/compute.admin"  # Example
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}
```

Apply:
```bash
cd bootstrap/
terraform apply
```

### **Remove Permission**

Remove or comment out the role binding in `main.tf`:
```hcl
# resource "google_project_iam_member" "logging_admin" {
#   ...
# }
```

Apply:
```bash
terraform apply
```

---

## 🗑️ **Cleanup**

### **Delete Service Account**

**WARNING:** This will revoke Terraform access!

```bash
cd bootstrap/
terraform destroy
```

**When to do this:**
- Testing/learning completed
- Moving to production setup
- Security incident requiring credential rotation

---

## 🐛 **Troubleshooting**

### **Issue 1: "Permission Denied" during bootstrap**

**Cause:** Your personal account doesn't have Owner/Editor role

**Solution:**
```bash
# Check your roles
gcloud projects get-iam-policy agentic-ai-integration-490716 \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"

# If missing permissions, ask project owner to grant:
# roles/owner OR roles/editor
```

---

### **Issue 2: "Key file not found" after extraction**

**Cause:** Output command failed or wrong directory

**Solution:**
```bash
# Ensure you're in bootstrap directory
cd terraform/bootstrap/

# Re-extract key
terraform output -raw service_account_key_file_content > terraform-sa-key.json

# Check if file exists
ls -l terraform-sa-key.json
```

---

### **Issue 3: "Invalid credentials" in main terraform**

**Cause:** Environment variable not set correctly

**Solution:**
```bash
# Check if variable is set
echo $GOOGLE_APPLICATION_CREDENTIALS  # Linux/Mac
echo %GOOGLE_APPLICATION_CREDENTIALS% # Windows CMD
echo $env:GOOGLE_APPLICATION_CREDENTIALS # Windows PowerShell

# Re-set the variable with absolute path
export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/terraform-sa-key.json"
```

---

### **Issue 4: Service account exists already**

**Cause:** Service account was created previously

**Solution:**

**Option A: Import existing service account**
```bash
terraform import google_service_account.terraform_deployer \
  projects/agentic-ai-integration-490716/serviceAccounts/terraform-deployer@agentic-ai-integration-490716.iam.gserviceaccount.com
```

**Option B: Use different service account ID**
Edit `terraform.tfvars`:
```hcl
service_account_id = "terraform-deployer-v2"
```

**Option C: Delete existing and recreate**
```bash
gcloud iam service-accounts delete \
  terraform-deployer@agentic-ai-integration-490716.iam.gserviceaccount.com \
  --project=agentic-ai-integration-490716
```

---

## 📊 **Comparison: Manual vs Automated**

| Aspect | Manual (Console) | Automated (Terraform) |
|--------|------------------|----------------------|
| **Time** | 15-20 minutes | 2-3 minutes |
| **Steps** | 10+ clicks | 3 commands |
| **Errors** | Easy to miss a role | Guaranteed consistent |
| **Documentation** | Manual notes | Code as documentation |
| **Reproducibility** | Hard | Easy (run again) |
| **Team Onboarding** | Needs training | Self-service |
| **Audit Trail** | Console audit logs | Terraform state + Git |

**Recommendation:** Use automated approach (Terraform bootstrap)

---

## 🔗 **What Happens Next**

### **After Bootstrap Success:**

1. ✅ Service account created
2. ✅ All permissions granted
3. ✅ Key file saved
4. ✅ Environment variable set

### **Next Steps:**

1. Navigate to main terraform directory
2. Configure `terraform.tfvars` (main infrastructure)
3. Run `terraform apply` (deploys GCP→AWS pipeline)
4. Monitor and optimize

---

## 📚 **Related Documentation**

- **Main Deployment:** `TERRAFORM_QUICK_START.md`
- **Filter Configuration:** `FILTERS_OVERVIEW.md`
- **Permissions Details:** `TERRAFORM_PERMISSIONS.md`
- **Architecture Overview:** `TERRAFORM_ARCHITECTURE.md`

---

## ✅ **Bootstrap Checklist**

```
Prerequisites:
□ gcloud CLI installed
□ Terraform installed
□ Authenticated with personal GCP account (Owner role)
□ Have GCP project ID

Bootstrap Steps:
□ cd terraform/bootstrap/
□ Copy terraform.tfvars.example → terraform.tfvars
□ Edit terraform.tfvars with project ID
□ terraform init
□ terraform plan (review)
□ terraform apply
□ Extract key: terraform output -raw service_account_key_file_content > terraform-sa-key.json
□ Set GOOGLE_APPLICATION_CREDENTIALS environment variable
□ Verify key file exists and is valid JSON

Security:
□ Verify .gitignore includes *.json
□ Verify key file NOT committed to Git
□ Store key securely
□ Document key location for team

Ready for Main Deployment:
□ cd .. (back to main terraform directory)
□ Configure main terraform.tfvars
□ terraform init
□ terraform apply
```

---

## 🎓 **Key Takeaways**

1. **Bootstrap runs ONCE** - Creates service account for main deployment
2. **Use personal credentials** - For bootstrap only (Owner/Editor role)
3. **Use service account credentials** - For all main infrastructure deployments
4. **Keep key secure** - Treat like a password
5. **Infrastructure as Code** - Reproducible, auditable, consistent

---

## 🆘 **Need Help?**

**Bootstrap issues:**
- Verify you have Owner/Editor role
- Check gcloud authentication
- Review Terraform plan output

**Main deployment issues:**
- Verify GOOGLE_APPLICATION_CREDENTIALS is set
- Check service account has all 6 roles
- Review main terraform documentation

---

**Last Updated:** 2024-04-23  
**Purpose:** Automate GCP service account creation for Terraform deployments  
**Target Audience:** DevOps Engineers, Platform Engineers, Cloud Administrators
