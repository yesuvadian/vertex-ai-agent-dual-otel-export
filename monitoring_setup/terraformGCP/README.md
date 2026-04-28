# GCP Log Sink to AWS Lambda - Terraform Setup

## Overview

Forward GCP Reasoning Engine logs to AWS Lambda using Terraform.

```
GCP Reasoning Engine Logs
    ↓
Log Sink (with filters)
    ↓
Pub/Sub Topic
    ↓
Pub/Sub Subscription
    ↓
Push to: AWS Lambda URL (with or without OIDC auth)
```

## 🎯 Two Deployment Options

### 🔐 Option 1: OIDC Authentication (Recommended for Production)
**Location**: `terraform/client_package_oidc/`
- ✅ Secure JWT token authentication
- ✅ Industry-standard OIDC
- ✅ Production-ready
- 📖 See `CHOOSE_YOUR_VERSION.md` for details

### 🔓 Option 2: No Authentication (Simple, Testing)
**Location**: `terraform/client_package/`
- ✅ Quick setup
- ✅ No Lambda changes needed
- ⚠️ Testing only - no authentication
- 📖 See `CHOOSE_YOUR_VERSION.md` for details

**👉 Read [`CHOOSE_YOUR_VERSION.md`](CHOOSE_YOUR_VERSION.md) to pick the right option!**

---

## Structure

```
terraformGCP/
├── CHOOSE_YOUR_VERSION.md   # 👈 START HERE - Choose OIDC vs No-Auth
├── terraform/
│   ├── client_package/       # No-Auth version (simple, testing)
│   │   ├── CLIENT_GUIDE.md
│   │   ├── CLIENT_GUIDE_USER_AUTH.md
│   │   ├── main.tf
│   │   ├── gcp_log_sink_pubsub.tf
│   │   ├── deploy scripts...
│   │   └── cleanup scripts...
│   │
│   ├── client_package_oidc/  # OIDC version (secure, production)
│   │   ├── CLIENT_GUIDE_OIDC.md
│   │   ├── LAMBDA_OIDC_GUIDE.md  # How to implement Lambda OIDC
│   │   ├── main.tf
│   │   ├── gcp_log_sink_pubsub_oidc.tf
│   │   ├── deploy scripts...
│   │   └── cleanup scripts...
│   │
│   ├── DISTRIBUTE.md         # Admin: How to distribute to clients
│   └── GCP_PERMISSIONS.md    # Required GCP permissions
│
└── README.md                 # This file
```

---

## Quick Start

### 1️⃣ Choose Your Version

**Production / Secure:**
```bash
cd terraform/client_package_oidc/
# Read CLIENT_GUIDE_OIDC.md
# Implement Lambda OIDC (see LAMBDA_OIDC_GUIDE.md)
```

**Testing / POC:**
```bash
cd terraform/client_package/
# Read CLIENT_GUIDE.md
```

### 2️⃣ Configure

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit with YOUR project ID, engine IDs, Lambda URL
```

### 3️⃣ Deploy

```bash
# Windows PowerShell
.\deploy.ps1

# Linux/Mac/Git Bash
./deploy.sh

# Windows CMD
deploy.bat
```

---

## What Gets Created

### No-Auth Version (`client_package/`)
- Pub/Sub Topic: `reasoning-engine-logs-topic`
- Pub/Sub Subscription: Pushes to Lambda (no auth)
- Log Sink: Filters and routes logs

### OIDC Version (`client_package_oidc/`)
- **Service Account**: For OIDC token generation
- Pub/Sub Topic: `reasoning-engine-logs-topic`
- Pub/Sub Subscription: Pushes to Lambda **with OIDC token**
- Log Sink: Filters and routes logs
- **IAM Permissions**: Token Creator role

---

## Requirements

### For Clients

**All versions need:**
- Terraform installed
- GCP Project with Reasoning Engines
- Service Account key (Editor role) OR user account
- Lambda URL
- Reasoning Engine IDs

**OIDC version additionally needs:**
- Lambda with OIDC validation implemented
- Python packages in Lambda: `google-auth`, `cryptography`

**Clients DON'T need:**
- gcloud CLI (unless using user account deployment)
- AWS CLI
- AWS account access

---

## Comparison Table

| Feature | No-Auth | OIDC |
|---------|---------|------|
| **Security** | None | JWT tokens |
| **Setup Time** | 5-10 min | 15-20 min |
| **Lambda Changes** | None | OIDC validation |
| **Production** | ⚠️ No | ✅ Yes |
| **Compliance** | ⚠️ No | ✅ Yes |

**👉 See [`CHOOSE_YOUR_VERSION.md`](CHOOSE_YOUR_VERSION.md) for detailed comparison**

---

## Security

### No-Auth Version:
- Uses App Engine service account key
- Editor role on GCP project
- ⚠️ No authentication - public Lambda endpoint
- Rotate key every 90 days

### OIDC Version:
- Uses App Engine service account key for deployment
- Creates dedicated OIDC service account for auth
- ✅ JWT token authentication on every request
- Lambda validates token signature, issuer, and audience
- Rotate keys every 90 days

---

## For Admins - Distribution

See [`terraform/DISTRIBUTE.md`](terraform/DISTRIBUTE.md) for:
- How to package for clients
- What to include/exclude
- Lambda URL and Engine ID instructions
- Which version to distribute

---

## Cleanup

Both versions include cleanup scripts:

```bash
# Terraform destroy
terraform destroy

# Or use cleanup scripts
.\cleanup-with-user-account.ps1  # PowerShell
./cleanup-with-user-account.sh   # Bash
```

---

## Next Steps

1. 📖 **Read** [`CHOOSE_YOUR_VERSION.md`](CHOOSE_YOUR_VERSION.md)
2. 🎯 **Choose** OIDC (production) or No-Auth (testing)
3. 📁 **Navigate** to chosen `client_package*` folder
4. 📋 **Follow** the CLIENT_GUIDE in that folder
5. 🚀 **Deploy** using provided scripts

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `CHOOSE_YOUR_VERSION.md` | Decide OIDC vs No-Auth |
| `client_package/CLIENT_GUIDE.md` | Setup (No-Auth, service account) |
| `client_package/CLIENT_GUIDE_USER_AUTH.md` | Setup (No-Auth, user account) |
| `client_package_oidc/CLIENT_GUIDE_OIDC.md` | Setup (OIDC, service account) |
| `client_package_oidc/LAMBDA_OIDC_GUIDE.md` | Implement Lambda OIDC |
| `terraform/DISTRIBUTE.md` | Admin distribution guide |
| `terraform/GCP_PERMISSIONS.md` | Required GCP permissions |

---

**Questions?** Start with [`CHOOSE_YOUR_VERSION.md`](CHOOSE_YOUR_VERSION.md)!
