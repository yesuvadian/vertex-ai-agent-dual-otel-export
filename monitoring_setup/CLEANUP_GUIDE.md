# Monitoring Setup - Cleanup Guide

## 🎯 **Current State**

The `monitoring_setup` folder contains:
- ✅ **Production Terraform setup** (in `lambda_poc/terraform/`)
- ❌ **Old POC files** (testing, experiments, deprecated scripts)
- ❌ **Duplicate documentation**
- ❌ **Unused deployment scripts**

---

## 📂 **What to Keep**

### **Keep: Terraform Infrastructure (Production)**
```
lambda_poc/terraform/
├── bootstrap/                          ✅ KEEP - Service account setup
├── main.tf                             ✅ KEEP - Main infrastructure
├── gcp_log_sink_pubsub.tf             ✅ KEEP - Log sink config
├── aws_lambda_multi_customer.tf       ✅ KEEP - Lambda config
├── security_shared_secret.tf          ✅ KEEP - Security config
├── gcp_agent_logging.tf               ✅ KEEP - Agent logging
├── main_existing_aws.tf               ✅ KEEP - AWS integration
├── lambda_multi_customer.py           ✅ KEEP - Lambda code
├── terraform.tfvars.example           ✅ KEEP - Config example
├── *.md files                          ✅ KEEP - Documentation
└── .gitignore                          ✅ KEEP - Git protection
```

### **Keep: OIDC Reference Files (Working Solution)**
```
lambda_poc/
├── lambda_with_oidc.py                ✅ KEEP - OIDC implementation reference
├── lambda_with_oidc_simple.py         ✅ KEEP - Simple OIDC example
├── setup_gcp_oidc.sh                  ✅ KEEP - OIDC manual setup script
├── requirements_oidc.txt              ✅ KEEP - OIDC dependencies
└── oidc_lambda_config.txt             ✅ KEEP - OIDC configuration notes
```

### **Keep: Documentation (Root Level)**
```
lambda_poc/
├── LOG_SINK_DEEP_DIVE.md              ✅ KEEP - Educational
├── PUBSUB_DEEP_DIVE.md                ✅ KEEP - Educational
├── CONCEPTUAL_EXPLANATION.md          ✅ KEEP - Educational
└── SECURITY_SETUP.md                  ✅ KEEP - Security guide
```

---

## 🗑️ **What to Remove**

### **Remove: Old Lambda POC Files (Deprecated)**
These were for testing, now replaced by Terraform:

```
lambda_poc/
├── ❌ function.zip                     # Old lambda package
├── ❌ lambda_api_key.zip               # Old POC - API key auth
├── ❌ lambda_oidc.zip                  # Compiled OIDC (4.7MB!) - keep .py version
├── ❌ lambda_oidc_simple.zip           # Compiled OIDC - keep .py version
├── ❌ lambda_shared_secret.zip         # Old POC - Shared secret
├── ❌ lambda_function.py               # Old simple lambda
├── ❌ lambda_with_api_key.py           # Old API key method
├── ✅ lambda_with_oidc.py              # KEEP - OIDC reference (working solution)
├── ✅ lambda_with_oidc_simple.py       # KEEP - Simple OIDC reference
├── ❌ lambda_with_shared_secret.py     # Old shared secret method
└── ❌ lambda_credentials.txt           # Old credentials (security risk!)
```

**Note:** OIDC is the current working authentication method used in production Terraform.

### **Remove: Old Deployment Scripts (Deprecated)**
These were manual deployment scripts, now replaced by Terraform:

```
lambda_poc/
├── ❌ deploy.sh                        # Old manual deploy
├── ❌ deploy_simple.sh                 # Old simple deploy
├── ❌ deploy_with_url.sh               # Old URL deploy
├── ❌ deploy_oidc_lambda.sh            # Old OIDC deploy (replaced by Terraform)
├── ❌ deploy_secured_lambdas.sh        # Old secured deploy
├── ❌ deploy_complete_integration.sh   # Old integration deploy
├── ❌ deploy_agent_with_logging.sh     # Old agent deploy
├── ❌ deploy_reasoning_engine.sh       # Old reasoning deploy
├── ❌ setup_gcp_pubsub_with_auth.sh    # Replaced by Terraform
├── ✅ setup_gcp_oidc.sh                # KEEP - OIDC setup reference
├── ❌ setup_log_sink_programmatic.py   # Replaced by Terraform
└── ❌ setup_reasoning_logs_to_aws.sh   # Replaced by Terraform
```

**Note:** `setup_gcp_oidc.sh` is kept as reference for manual OIDC setup understanding.

### **Remove: Test/POC Python Scripts**
These were for development/testing:

```
lambda_poc/
├── ❌ create_adk_style_agent.py        # POC script
├── ❌ create_agent_api.py              # POC script
├── ❌ create_reasoning_engine_with_logs.py
├── ❌ create_simple_adk_agent.py       # POC script
├── ❌ deploy_vertex_reasoning_engine.py
├── ❌ test_adk_style_agent.py          # Test script
├── ❌ test_from_console.py             # Test script
├── ❌ test_local.py                    # Test script
├── ❌ test_reasoning_engine.py         # Test script
├── ❌ test_reasoning_engine_new.py     # Test script
├── ❌ test_simple_adk_agent.py         # Test script
├── ❌ check_console_test.sh            # Test script
└── ❌ add_auth_headers.py              # Utility script
```

### **Remove: Old Requirements Files (Except OIDC)**
```
lambda_poc/
├── ❌ requirements.txt                 # Old dependencies
├── ✅ requirements_oidc.txt            # KEEP - OIDC dependencies reference
└── ❌ requirements_log_sink.txt        # Old log sink deps
```

### **Keep: OIDC Config Files**
```
lambda_poc/
└── ✅ oidc_lambda_config.txt           # KEEP - OIDC configuration reference
```

### **Remove: Old Agent Files (if not used)**
```
lambda_poc/adk_agent/
├── ❌ monitoring_agent_adk.py          # If not actively used
└── ❌ deploy_adk_agent.py              # If not actively used
```

### **Remove: Deprecated/Duplicate Documentation**
```
lambda_poc/
├── ❌ ARCHITECTURE_WRITEUP.md          # Superseded by terraform docs
├── ❌ COMPLETE_ARCHITECTURE_DIAGRAM.md # Superseded
├── ❌ COMPLETE_SETUP_SUMMARY.md        # Superseded
├── ❌ DEPLOYMENT_STATUS.md             # Old status
├── ❌ EMAIL_WRITEUP.md                 # Old writeup
├── ❌ FINAL_ARCHITECTURE.md            # Superseded
├── ❌ FINAL_DEPLOYMENT_SUMMARY.md      # Superseded
├── ❌ FINAL_INTEGRATED_ARCHITECTURE.md # Superseded
├── ❌ GCP_AGENT_SECURITY.md            # Superseded by terraform docs
├── ❌ HEADER_LIMITATION.md             # Old limitation doc
├── ❌ INTEGRATION_WITH_PORTAL26_PREPROCESSOR.md  # Old
└── ❌ MANUAL_HEADER_SETUP.md           # Manual process (deprecated)
```

### **Remove: Root Level Deprecated Docs**
```
monitoring_setup/
├── ❌ AGENT_ENGINE_LOGGING.md          # Superseded
├── ❌ AGENT_ENGINE_SOLUTION.md         # Superseded
├── ❌ ARCHITECTURE.md                  # Superseded
├── ❌ ARCHITECTURE_ONE_LAMBDA_PER_CUSTOMER.md  # Old architecture
├── ❌ AWS_DEPLOYMENT.md                # Superseded by Terraform
├── ❌ CONTINUOUS_OPERATION_GUIDE.md    # Old guide
├── ❌ DEPLOYMENT_SUMMARY.md            # Superseded
└── ❌ continuous_forwarder.py          # Old forwarder
```

---

## 🚀 **Cleanup Commands**

### **Option 1: Move to Archive (Recommended)**
```bash
# Create archive directory
mkdir -p "C:\Yesu\ai_agent_projectgcp\monitoring_setup\_archive"

# Move old files
cd "C:\Yesu\ai_agent_projectgcp\monitoring_setup\lambda_poc"

# Move zip files
mv *.zip ../_archive/ 2>/dev/null

# Move old lambda files
mv lambda_function.py lambda_with_*.py ../_archive/ 2>/dev/null

# Move old deployment scripts
mv deploy*.sh setup*.sh ../_archive/ 2>/dev/null

# Move test files
mv test_*.py create_*.py ../_archive/ 2>/dev/null

# Move old docs
mv ARCHITECTURE_WRITEUP.md COMPLETE_*.md DEPLOYMENT_STATUS.md \
   EMAIL_WRITEUP.md FINAL_*.md GCP_AGENT_SECURITY.md \
   HEADER_LIMITATION.md INTEGRATION_*.md MANUAL_*.md \
   ../_archive/ 2>/dev/null
```

### **Option 2: Delete Permanently (Use with Caution)**
```bash
cd "C:\Yesu\ai_agent_projectgcp\monitoring_setup\lambda_poc"

# Delete zip files
rm -f *.zip

# Delete old lambda files
rm -f lambda_function.py lambda_with_*.py lambda_credentials.txt

# Delete old scripts
rm -f deploy*.sh setup*.sh *.py
# (But keep lambda_multi_customer.py!)
# Better to do selectively:
rm -f add_auth_headers.py check_console_test.sh create_*.py
rm -f deploy_vertex_reasoning_engine.py test_*.py
rm -f setup_gcp_pubsub_with_auth.sh setup_gcp_oidc.sh
rm -f setup_log_sink_programmatic.py setup_reasoning_logs_to_aws.sh

# Delete old requirements
rm -f requirements.txt requirements_oidc.txt requirements_log_sink.txt

# Delete old configs
rm -f oidc_lambda_config.txt

# Delete old docs
rm -f ARCHITECTURE_WRITEUP.md COMPLETE_*.md DEPLOYMENT_STATUS.md
rm -f EMAIL_WRITEUP.md FINAL_*.md GCP_AGENT_SECURITY.md
rm -f HEADER_LIMITATION.md INTEGRATION_*.md MANUAL_*.md
```

---

## 📊 **Size Savings**

**Before Cleanup:**
- Total size: ~10+ MB
- Files: ~80+ files

**After Cleanup:**
- Total size: ~2 MB
- Files: ~30 files (production only)

**Biggest savings:**
- `lambda_oidc.zip` (4.7 MB) ❌
- All old zip files ❌
- Duplicate documentation ❌

---

## ✅ **Final Directory Structure (After Cleanup)**

```
monitoring_setup/
├── lambda_poc/
│   ├── terraform/                      ← Production infrastructure
│   │   ├── bootstrap/                  ← Bootstrap setup
│   │   ├── main.tf
│   │   ├── *.tf files
│   │   ├── lambda_multi_customer.py    ← Production lambda
│   │   ├── terraform.tfvars.example
│   │   └── *.md documentation files
│   │
│   ├── LOG_SINK_DEEP_DIVE.md          ← Educational docs
│   ├── PUBSUB_DEEP_DIVE.md
│   └── CONCEPTUAL_EXPLANATION.md
│
└── _archive/                           ← Old POC files (if archived)
    └── ... (old files for reference)
```

---

## 🔍 **Before You Delete - Verify**

### **Check if anything is still referenced:**
```bash
# Search for references to old files
cd "C:\Yesu\ai_agent_projectgcp"
grep -r "lambda_function.py" --include="*.md" --include="*.tf"
grep -r "deploy.sh" --include="*.md" --include="*.tf"
```

### **Check Git Status:**
```bash
cd "C:\Yesu\ai_agent_projectgcp"
git status
# Make sure you're not deleting uncommitted work
```

---

## ⚠️ **Important Notes**

1. **Backup First:** Consider archiving instead of deleting
2. **Git History:** Old files are preserved in git history
3. **Team Sync:** Inform team before cleanup
4. **Documentation:** Update any references to removed files
5. **Terraform Only:** Production uses Terraform now, old scripts not needed

---

## 🎯 **Recommended Approach**

**Phase 1: Archive (Safe)**
```bash
mkdir _archive
mv old_files/* _archive/
# Test everything still works
```

**Phase 2: Delete After Testing (1-2 weeks)**
```bash
# If everything works fine after 1-2 weeks
rm -rf _archive/
```

---

**Summary:** Remove ~50 old POC/test files, keep ~30 production Terraform files. Size reduction: ~80% (10MB → 2MB).
