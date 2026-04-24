# OIDC Reference Files - Preserved Documentation

## 🎯 **Why These Files Are Kept**

OIDC (OpenID Connect) is the **current authentication method** used in production Terraform. These files are preserved as reference implementation and documentation.

---

## 📁 **OIDC Files Preserved**

### **1. lambda_with_oidc.py**
**Purpose:** Complete OIDC Lambda implementation reference

**What it does:**
- Receives Pub/Sub messages with OIDC JWT token
- Validates JWT token from Google Cloud
- Verifies token audience and issuer
- Processes authenticated log messages

**Use case:**
- Reference for OIDC JWT validation
- Example of Google OIDC token structure
- Troubleshooting authentication issues

**Location:** `lambda_poc/lambda_with_oidc.py`

---

### **2. lambda_with_oidc_simple.py**
**Purpose:** Simplified OIDC implementation for learning

**What it does:**
- Minimal OIDC validation example
- Easier to understand than full implementation
- Good starting point for customization

**Use case:**
- Learning how OIDC works
- Quick reference for key concepts
- Template for custom implementations

**Location:** `lambda_poc/lambda_with_oidc_simple.py`

---

### **3. setup_gcp_oidc.sh**
**Purpose:** Manual OIDC setup script for GCP

**What it does:**
- Creates service account for OIDC
- Grants Token Creator permissions
- Sets up Pub/Sub with OIDC authentication
- Configures push subscription

**Use case:**
- Understanding manual OIDC setup process
- Troubleshooting Terraform OIDC configuration
- Reference for OIDC service account permissions

**Location:** `lambda_poc/setup_gcp_oidc.sh`

**Commands it runs:**
```bash
# Create service account
gcloud iam service-accounts create pubsub-oidc-invoker

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"

# Create Pub/Sub subscription with OIDC
gcloud pubsub subscriptions create SUBSCRIPTION_NAME \
  --topic=TOPIC_NAME \
  --push-endpoint=LAMBDA_URL \
  --push-auth-service-account=pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com \
  --push-auth-token-audience=LAMBDA_URL
```

---

### **4. requirements_oidc.txt**
**Purpose:** Python dependencies for OIDC Lambda

**Contents:**
```
google-auth
cryptography
```

**What they do:**
- `google-auth`: Validates Google OIDC tokens
- `cryptography`: JWT decoding and verification

**Use case:**
- Package Lambda function with OIDC validation
- Reference for OIDC dependencies

**Location:** `lambda_poc/requirements_oidc.txt`

---

### **5. oidc_lambda_config.txt**
**Purpose:** OIDC configuration notes and examples

**Contains:**
- Lambda environment variables needed
- OIDC token structure examples
- Audience configuration
- Issuer URLs

**Use case:**
- Quick reference for OIDC configuration
- Troubleshooting token validation
- Understanding OIDC flow

**Location:** `lambda_poc/oidc_lambda_config.txt`

---

## 🔐 **How OIDC Works in This System**

### **Flow Diagram**
```
┌─────────────────────────────────────────────────────────────┐
│  GCP Cloud Logging                                          │
│  (Reasoning Engine logs)                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────┐
        │  Log Sink (Filter)         │
        └────────────┬───────────────┘
                     │
                     ↓
        ┌────────────────────────────┐
        │  Pub/Sub Topic             │
        └────────────┬───────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │  Pub/Sub Subscription              │
        │  - Push to Lambda                  │
        │  - Service Account: pubsub-oidc    │
        │  - Generate OIDC JWT token         │
        └────────────┬───────────────────────┘
                     │
                     ↓ (HTTP POST with Authorization: Bearer JWT)
        ┌────────────────────────────────────┐
        │  AWS Lambda Function URL           │
        │  1. Extract JWT from Authorization │
        │  2. Validate JWT signature         │
        │  3. Verify audience = Lambda URL   │
        │  4. Verify issuer = Google         │
        │  5. Check token expiry             │
        │  6. Process log message            │
        └────────────────────────────────────┘
```

### **OIDC Token Structure**
```json
{
  "aud": "https://LAMBDA_FUNCTION_URL.lambda-url.us-east-1.on.aws",
  "azp": "106410...",
  "email": "pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com",
  "email_verified": true,
  "exp": 1714000000,
  "iat": 1713996400,
  "iss": "https://accounts.google.com",
  "sub": "106410..."
}
```

**Key Fields:**
- `aud` (audience): Lambda URL - prevents token reuse
- `iss` (issuer): Google accounts - confirms token source
- `exp` (expiration): Token validity period
- `email`: Service account identity

---

## 🔄 **Relationship to Terraform**

### **Terraform Implementation**
The production Terraform uses OIDC automatically:

**File:** `terraform/gcp_log_sink_pubsub.tf`

```hcl
# Service Account for OIDC
resource "google_service_account" "pubsub_oidc_invoker" {
  account_id   = "pubsub-oidc-invoker"
  display_name = "Pub/Sub OIDC Token Generator"
}

# Grant Token Creator permission
resource "google_project_iam_member" "pubsub_token_creator" {
  role   = "roles/iam.serviceAccountTokenCreator"
  member = "serviceAccount:${google_service_account.pubsub_oidc_invoker.email}"
}

# Pub/Sub Subscription with OIDC
resource "google_pubsub_subscription" "reasoning_engine_to_oidc" {
  name  = "reasoning-engine-to-oidc"
  topic = google_pubsub_topic.reasoning_engine_logs.name
  
  push_config {
    push_endpoint = var.aws_lambda_url
    
    oidc_token {
      service_account_email = google_service_account.pubsub_oidc_invoker.email
      audience              = var.aws_lambda_url
    }
  }
}
```

**What Terraform Does (Same as Manual Scripts):**
1. ✅ Creates service account
2. ✅ Grants Token Creator role
3. ✅ Configures Pub/Sub with OIDC
4. ✅ Sets audience to Lambda URL

**Advantage:** Reproducible, version-controlled, automated

---

## 📚 **When to Use These Files**

### **Use Case 1: Understanding OIDC Flow**
**Read:** `lambda_with_oidc_simple.py`
- See minimal JWT validation
- Understand token structure

### **Use Case 2: Debugging Authentication Issues**
**Read:** `lambda_with_oidc.py` + `oidc_lambda_config.txt`
- Check token validation logic
- Verify audience configuration
- Debug JWT errors

### **Use Case 3: Manual Setup (Without Terraform)**
**Run:** `setup_gcp_oidc.sh`
- Create OIDC setup manually
- Useful for testing/POC
- Learning GCP commands

### **Use Case 4: Custom Lambda Implementation**
**Reference:** `lambda_with_oidc.py` + `requirements_oidc.txt`
- Build custom Lambda function
- Add custom logic to validation
- Package with correct dependencies

### **Use Case 5: Comparing Terraform vs Manual**
**Compare:** `setup_gcp_oidc.sh` vs `terraform/gcp_log_sink_pubsub.tf`
- Understand what Terraform automates
- Troubleshoot Terraform issues
- Learn infrastructure as code

---

## 🔍 **OIDC vs Other Auth Methods**

| Method | Security | Complexity | Use Case |
|--------|----------|------------|----------|
| **OIDC** (Current) | ✅ High | Medium | **Production** - Token-based, no shared secrets |
| Shared Secret | ⚠️ Medium | Low | Testing - Simple but requires secret management |
| API Key | ❌ Low | Low | Development - Not recommended for production |

**Why OIDC?**
- ✅ No shared secrets to manage
- ✅ Short-lived tokens (automatic expiry)
- ✅ Service account identity verification
- ✅ Audience restriction (token only valid for specific Lambda)
- ✅ Google-signed tokens (cryptographically secure)

---

## ⚠️ **Important Notes**

### **These Files Are Reference Only**
- ❌ Do NOT deploy these directly
- ✅ Use Terraform for production deployment
- ✅ Use these for understanding and troubleshooting

### **Production Uses Terraform**
- Production Lambda: `terraform/lambda_multi_customer.py`
- Production config: `terraform/*.tf` files
- These reference files: For learning and debugging

### **Security**
- OIDC tokens are short-lived (~1 hour)
- Audience must match Lambda URL exactly
- Validate issuer is `https://accounts.google.com`
- Check token expiration before processing

---

## 🔗 **Related Documentation**

- **Terraform Setup:** `terraform/README.md`
- **Security Guide:** `SECURITY_SETUP.md`
- **Pub/Sub Deep Dive:** `PUBSUB_DEEP_DIVE.md`
- **GCP OIDC Official Docs:** https://cloud.google.com/pubsub/docs/push#using_push

---

## 📞 **Troubleshooting OIDC**

### **Issue: "Invalid JWT token"**
**Check:**
1. Token audience matches Lambda URL exactly
2. Token not expired
3. Issuer is `https://accounts.google.com`

**Reference:** `lambda_with_oidc.py` validation logic

---

### **Issue: "Service account missing permissions"**
**Check:**
```bash
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:pubsub-oidc-invoker@*"
```

**Should see:** `roles/iam.serviceAccountTokenCreator`

**Reference:** `setup_gcp_oidc.sh` permission grants

---

### **Issue: "Audience validation failed"**
**Cause:** Mismatch between subscription audience and Lambda validation

**Fix:**
1. Check Pub/Sub subscription audience: Should be Lambda URL
2. Check Lambda validation: Should expect same URL

**Reference:** `oidc_lambda_config.txt` audience examples

---

**Summary:** These OIDC reference files document the working authentication solution used in production Terraform. Keep them for troubleshooting, learning, and custom implementations.

**Last Updated:** 2024-04-24
