# GCP Log Sink to AWS Lambda (WITH OIDC Authentication)

## 🔐 Secure Version - OIDC Authentication Required

This package deploys GCP infrastructure to forward Reasoning Engine logs to AWS Lambda **with OIDC authentication**. Your Lambda must validate JWT tokens.

---

## 📋 Quick Start

### 1. Prerequisites Check

- [ ] Terraform installed
- [ ] GCP service account key (Editor role)
- [ ] AWS Lambda URL
- [ ] **Lambda has OIDC validation enabled** ⚠️

### 2. Configure

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with YOUR values
```

### 3. Deploy

```bash
# Windows PowerShell
.\deploy.ps1

# Linux/Mac
./deploy.sh

# Windows CMD
deploy.bat
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `CLIENT_GUIDE_OIDC.md` | Complete setup instructions |
| `LAMBDA_OIDC_GUIDE.md` | Lambda implementation guide |
| `terraform.tfvars.example` | Configuration template |

---

## 🔒 Security Features

✅ **OIDC Authentication** - Every request includes JWT token  
✅ **Token Validation** - Lambda verifies signature and claims  
✅ **Audience Verification** - Token bound to specific Lambda URL  
✅ **Issuer Verification** - Only accepts Google-issued tokens  
✅ **Service Account** - Dedicated identity for token generation  

---

## ⚠️ IMPORTANT: Lambda Requirements

Your Lambda **MUST** validate OIDC tokens:

```python
from google.oauth2 import id_token
from google.auth.transport import requests

def lambda_handler(event, context):
    # Extract token from Authorization header
    token = event['headers']['authorization'].replace('Bearer ', '')
    
    # Validate token
    id_info = id_token.verify_oauth2_token(
        token, 
        requests.Request(), 
        "https://your-lambda-url.lambda-url.us-east-1.on.aws"
    )
    
    # Process authenticated request...
```

**See `LAMBDA_OIDC_GUIDE.md` for complete implementation.**

---

## 🏗️ What Gets Created

In your GCP project:

1. **Service Account** (`pubsub-oidc-invoker`)
   - Generates OIDC tokens for authentication
   - Has Token Creator role

2. **Pub/Sub Topic** (`reasoning-engine-logs-topic`)
   - Receives logs from Log Sink
   - 7-day message retention

3. **Pub/Sub Subscription** (`reasoning-engine-to-lambda-oidc`)
   - Pushes to your Lambda with OIDC token
   - Automatic retry on failure

4. **Log Sink** (`reasoning-engine-to-pubsub-oidc`)
   - Routes Reasoning Engine logs
   - Configurable filters

---

## 🔄 Comparison: OIDC vs No-Auth

| Feature | OIDC (This Package) | No-Auth (client_package) |
|---------|-------------------|-------------------------|
| Security | ✅ JWT token validation | ❌ Public endpoint |
| Lambda Complexity | Medium (token validation) | Simple (no validation) |
| Setup Complexity | Medium (service account) | Simple |
| Production Ready | ✅ Yes | ⚠️ Testing only |
| Token in Header | ✅ Yes | ❌ No |

**Recommendation**: Use OIDC for production deployments.

---

## 🧪 Testing

After deployment:

```bash
# 1. Generate test log in Reasoning Engine
# 2. Check Lambda CloudWatch logs
# 3. Verify OIDC token in headers:
#    "authorization": "Bearer eyJhbGc..."
```

---

## 🔧 Troubleshooting

### Lambda returns 401

**Cause**: OIDC token validation failed

**Check:**
- Token audience matches Lambda URL exactly
- Lambda has `google-auth` package installed
- Service account has Token Creator role

### No logs arriving

**Cause**: Pub/Sub can't reach Lambda or auth fails

**Check:**
- Lambda URL is correct in `terraform.tfvars`
- Lambda returns 200 for valid tokens
- Check GCP Pub/Sub subscription errors in Console

### Token validation errors

**Cause**: Token signature invalid or expired

**Check:**
- Lambda has internet access (to fetch Google public keys)
- Token hasn't expired (valid 1 hour)
- Verify issuer: `https://accounts.google.com`

---

## 🧹 Cleanup

Remove all created resources:

```bash
terraform destroy
```

Or use cleanup scripts:

```powershell
# PowerShell
.\cleanup-with-user-account.ps1

# Bash
./cleanup-with-user-account.sh
```

---

## 📖 Next Steps

1. ✅ Read `CLIENT_GUIDE_OIDC.md` for detailed setup
2. ✅ Implement Lambda OIDC validation (see `LAMBDA_OIDC_GUIDE.md`)
3. ✅ Deploy infrastructure
4. ✅ Test with sample logs
5. ✅ Monitor authentication in CloudWatch

---

## 🆚 Need No-Auth Version?

If you just want to test without OIDC (not recommended for production):

- Use `../client_package/` instead
- No Lambda changes required
- Less secure (public endpoint)

---

## 💡 Tips

- **Audience must match exactly** - No trailing slashes!
- **Monitor auth failures** - Set up CloudWatch alarms
- **Rotate service account keys** - Every 90 days
- **Test OIDC first** - Validate locally before deploying
- **Keep Lambda dependencies updated** - `google-auth` package

---

## 📞 Support

- **Setup Issues**: Check `CLIENT_GUIDE_OIDC.md`
- **Lambda Issues**: Check `LAMBDA_OIDC_GUIDE.md`
- **Authentication Issues**: Review OIDC token validation
- **Terraform Errors**: Check GCP permissions

---

**Ready to deploy?** Follow `CLIENT_GUIDE_OIDC.md` for step-by-step instructions.
