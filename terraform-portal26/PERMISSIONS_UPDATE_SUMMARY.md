# Permission Requirements Update - Summary

## What Was Added

### 1. Comprehensive Permission Documentation

**File:** `PERMISSIONS.md`
- Complete guide to GCP IAM permissions
- Covers both deployment approaches
- Service account setup instructions
- Security best practices
- Troubleshooting guide
- CI/CD configurations (GitHub Actions, GitLab CI)
- Custom role examples
- Workload Identity setup

### 2. Quick Reference Guide

**File:** `PERMISSIONS_QUICKREF.md`
- TL;DR version of permissions
- Quick commands for both approaches
- Verification steps
- Security checklist

### 3. Automated Setup Scripts

**Files:**
- `scripts/setup_terraform_sa.sh` - Creates service account with correct permissions
- `scripts/verify_permissions.sh` - Validates configuration

**Features:**
- ✅ Idempotent (safe to run multiple times)
- ✅ Colored output with status indicators
- ✅ Error handling and validation
- ✅ Automatic API enablement
- ✅ Key file security (600 permissions)

### 4. Updated Documentation

**Files Updated:**
- `README.md` - Added permissions section, references to new docs
- `CLIENT_FAQ.md` - Expanded permissions Q&A with script references
- `.gitignore` - Added service account key patterns

---

## How to Use

### For New Users

```bash
# 1. Setup service account (one time)
./scripts/setup_terraform_sa.sh your-project-id

# 2. Verify configuration
./scripts/verify_permissions.sh \
  portal26-terraform@your-project-id.iam.gserviceaccount.com \
  your-project-id

# 3. Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"

# 4. Deploy
cd terraform
terraform init
terraform apply
```

### For Existing Users

If you already have a service account, verify it has all required permissions:

```bash
./scripts/verify_permissions.sh YOUR_SA_EMAIL YOUR_PROJECT_ID
```

Missing permissions? Re-run the setup script to update:

```bash
./scripts/setup_terraform_sa.sh YOUR_PROJECT_ID
```

---

## Permission Requirements Summary

### Approach 1: One-Time Injection

**Minimum roles:**
- `roles/aiplatform.user`
- `roles/storage.objectAdmin`

**Who needs them:** Developer's user account

### Approach 2: Terraform Automation

**Required roles:**
- `roles/aiplatform.admin`
- `roles/storage.admin`
- `roles/iam.serviceAccountUser`
- `roles/serviceusage.serviceUsageAdmin`

**Who needs them:** Service account

**Setup:** `./scripts/setup_terraform_sa.sh PROJECT_ID`

---

## Security Improvements

1. **Principle of Least Privilege**
   - Documented minimum required permissions
   - Separate permissions for each approach
   - Custom role examples for production

2. **Key Management**
   - Automated key creation with secure permissions
   - Rotation instructions (90-day cycle)
   - Gitignore patterns for keys

3. **Audit & Verification**
   - Permission verification script
   - API enablement checks
   - Key age warnings

4. **Best Practices Documentation**
   - Time-limited access examples
   - Workload Identity for GKE
   - Organization policy considerations
   - CI/CD secret management

---

## Files Created

```
terraform-portal26/
├── PERMISSIONS.md                    # Complete permission guide
├── PERMISSIONS_QUICKREF.md          # Quick reference
├── PERMISSIONS_UPDATE_SUMMARY.md    # This file
└── scripts/
    ├── setup_terraform_sa.sh        # Automated setup (executable)
    └── verify_permissions.sh        # Verification (executable)
```

## Files Modified

```
terraform-portal26/
├── README.md          # Added permissions section
├── CLIENT_FAQ.md      # Expanded permissions Q&A
└── .gitignore         # Added key file patterns
```

---

## Next Steps for Users

### First-Time Setup

1. **Read** `PERMISSIONS_QUICKREF.md` (2 minutes)
2. **Run** `./scripts/setup_terraform_sa.sh PROJECT_ID` (30 seconds)
3. **Verify** with `./scripts/verify_permissions.sh` (10 seconds)
4. **Deploy** using existing instructions

### Existing Installations

1. **Verify** current permissions with verification script
2. **Update** if needed by re-running setup script
3. **Rotate** service account keys if >90 days old

### CI/CD Integration

1. **Read** CI/CD section in `PERMISSIONS.md`
2. **Create** CI/CD service account (same permissions)
3. **Configure** GitHub/GitLab secrets
4. **Enable** automated deployments

---

## Security Reminders

⚠️ **CRITICAL:**
- Never commit `*-key.json` files to git
- Rotate keys every 90 days
- Use minimum required permissions
- Enable Cloud Audit Logs
- Review access quarterly

---

## Support

**Quick help:** `PERMISSIONS_QUICKREF.md`

**Detailed guide:** `PERMISSIONS.md`

**Troubleshooting:** See "Troubleshooting" section in `PERMISSIONS.md`

**Scripts failing?**
1. Check `gcloud` is installed and authenticated
2. Verify project ID is correct
3. Ensure you have `roles/owner` or `roles/iam.admin` to create service accounts
