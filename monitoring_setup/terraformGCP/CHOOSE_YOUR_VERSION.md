# Choose Your Deployment Version

You have **two deployment options** for forwarding GCP Reasoning Engine logs to AWS Lambda:

---

## 🔐 Option 1: OIDC Authentication (Recommended for Production)

**Location**: `terraform/client_package_oidc/`

### ✅ Use This If:
- You're deploying to **production**
- You need **secure authentication**
- Your Lambda can validate JWT tokens
- You want **industry-standard security**

### Features:
- ✅ OIDC JWT token authentication
- ✅ Lambda validates every request
- ✅ Service account-based identity
- ✅ Token audience verification
- ✅ Automatic token refresh

### Requirements:
- Lambda must implement OIDC validation
- Python packages: `google-auth`, `cryptography`
- Slightly more complex setup

### Quick Start:
```bash
cd terraform/client_package_oidc
# Follow CLIENT_GUIDE_OIDC.md
```

**📖 Documentation:**
- `CLIENT_GUIDE_OIDC.md` - Setup instructions
- `LAMBDA_OIDC_GUIDE.md` - Lambda implementation
- `README.md` - Overview

---

## 🔓 Option 2: No Authentication (Simple, Testing Only)

**Location**: `terraform/client_package/`

### ✅ Use This If:
- You're doing **quick testing/POC**
- You want **simplest setup**
- Your Lambda is already secured by other means
- You're in a **controlled environment**

### Features:
- ✅ Simple, fast setup
- ✅ No Lambda code changes needed
- ✅ Works with any Lambda
- ⚠️ **No authentication** - public endpoint

### Requirements:
- Lambda accepts all requests
- No special packages needed
- Minimal configuration

### Quick Start:
```bash
cd terraform/client_package
# Follow CLIENT_GUIDE.md
```

**📖 Documentation:**
- `CLIENT_GUIDE.md` - Setup with service account key
- `CLIENT_GUIDE_USER_AUTH.md` - Setup with user account
- `README.md` - Overview

---

## 🆚 Detailed Comparison

| Feature | OIDC (Recommended) | No-Auth (Simple) |
|---------|-------------------|------------------|
| **Security** | ✅ JWT token validation | ❌ None |
| **Production Ready** | ✅ Yes | ⚠️ Testing only |
| **Setup Time** | 15-20 minutes | 5-10 minutes |
| **Lambda Complexity** | Medium (token validation) | Simple (no changes) |
| **Token in Header** | ✅ Yes | ❌ No |
| **Authentication** | Service Account OIDC | None |
| **GCP Resources** | + Service Account | Basic only |
| **Lambda Packages** | `google-auth`, `cryptography` | None |
| **Compliance** | ✅ SOC2, ISO27001 friendly | ⚠️ May not meet requirements |

---

## 🎯 Recommendation by Use Case

### Production Deployment
```
✅ Use: client_package_oidc/
📖 Read: LAMBDA_OIDC_GUIDE.md
🔒 Security: Full OIDC authentication
```

### Testing / POC
```
✅ Use: client_package/
📖 Read: CLIENT_GUIDE.md
⚡ Speed: Fastest setup
```

### Development Environment
```
✅ Use: client_package/
📖 Read: CLIENT_GUIDE_USER_AUTH.md
🔧 Flexibility: User account auth
```

### Compliance Required (SOC2, HIPAA, etc.)
```
✅ Use: client_package_oidc/
📖 Read: LAMBDA_OIDC_GUIDE.md
🔒 Security: Industry-standard OIDC
```

---

## 🚀 Quick Decision Tree

```
┌─────────────────────────────────┐
│ Is this for PRODUCTION?         │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │   YES   │ → Use client_package_oidc/ (OIDC)
    └─────────┘
         │
    ┌────┴────┐
    │   NO    │ → Is security important?
    └────┬────┘
         │
    ┌────┴────┐
    │   YES   │ → Use client_package_oidc/ (OIDC)
    └─────────┘
         │
    ┌────┴────┐
    │   NO    │ → Use client_package/ (No-Auth)
    └─────────┘
```

---

## 📋 Setup Summary

### For OIDC Version:
1. Choose `client_package_oidc/`
2. Read `LAMBDA_OIDC_GUIDE.md`
3. Implement Lambda OIDC validation
4. Deploy Lambda with dependencies
5. Follow `CLIENT_GUIDE_OIDC.md`
6. Deploy GCP infrastructure
7. Test with sample logs

### For No-Auth Version:
1. Choose `client_package/`
2. Read `CLIENT_GUIDE.md`
3. Configure `terraform.tfvars`
4. Run deploy script
5. Test with sample logs

---

## 🔄 Can I Switch Later?

**Yes!** The infrastructure is similar:

### From No-Auth → OIDC:
1. Implement OIDC validation in Lambda
2. Deploy Lambda with new dependencies
3. Run `terraform destroy` in `client_package/`
4. Deploy `client_package_oidc/` instead

### From OIDC → No-Auth:
1. Run `terraform destroy` in `client_package_oidc/`
2. Deploy `client_package/` instead
3. Simplify Lambda (remove OIDC validation)

---

## 💡 Pro Tips

- **Start with No-Auth** to test connectivity quickly
- **Upgrade to OIDC** before production
- **Both versions** can coexist (different subscriptions)
- **Test OIDC locally** before deploying to GCP
- **Monitor auth failures** when using OIDC

---

## 📞 Need Help Choosing?

| Question | Answer Suggests |
|----------|----------------|
| "Is this for production?" | Yes → OIDC |
| "Do I need compliance?" | Yes → OIDC |
| "Want fastest setup?" | Yes → No-Auth |
| "Just testing quickly?" | Yes → No-Auth |
| "Security matters?" | Yes → OIDC |

---

**Still unsure?** Start with `client_package/` (No-Auth) for quick testing, then migrate to `client_package_oidc/` for production.
