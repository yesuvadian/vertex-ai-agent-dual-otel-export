# 🔒 Security Guide - Protecting Your Credentials

## ⚠️ Critical Security Information

Your `.env` file contains **SENSITIVE CREDENTIALS** that should **NEVER** be shared publicly or committed to Git.

---

## 🔴 NEVER Share These:

### 1. API Keys
```bash
GOOGLE_CLOUD_API_KEY=AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8
```
**Risk:** Anyone can use your Google Cloud quota and rack up charges.

### 2. Authentication Headers
```bash
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
```
**Risk:** This Base64 string decodes to your Portal26 username and password.

**Decode example:**
```bash
echo "dGl0YW5pYW06aGVsbG93b3JsZA==" | base64 --decode
# Output: titaniam:helloworld
```

### 3. Project IDs (Somewhat Sensitive)
```bash
GOOGLE_CLOUD_PROJECT=agentic-ai-integration-490716
```
**Risk:** While not critical, it reveals your GCP project structure.

---

## ✅ Safe to Share:

These configuration values are generally safe to share:

```bash
# Service configuration
OTEL_SERVICE_NAME=ai-agent
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_TRACES_EXPORTER=otlp

# Endpoints (public URLs)
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318

# Timing configurations
OTEL_METRIC_EXPORT_INTERVAL=1000
OTEL_LOGS_EXPORT_INTERVAL=500

# Agent settings
AGENT_MODE=manual
```

---

## 🛡️ How to Protect Your Secrets

### Method 1: Use `.env.example` (Recommended)

**✅ Created for you:** `.env.example`

This file contains placeholder values you can share:

```bash
# .env.example - Safe to commit to Git
GOOGLE_CLOUD_API_KEY=your-api-key-here
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic your-credentials-here
```

**In your repository:**
```bash
git add .env.example    # ✅ Safe - contains placeholders
git add .gitignore      # ✅ Safe - protects real secrets
# NEVER: git add .env   # ❌ DANGER - contains real secrets!
```

### Method 2: Use Google Secret Manager (Production)

For production deployments, use Secret Manager instead of environment variables:

#### Step 1: Create Secrets
```bash
# Store API key in Secret Manager
echo -n "AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8" | \
  gcloud secrets create gemini-api-key \
  --data-file=- \
  --replication-policy=automatic

# Store OTEL credentials
echo -n "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==" | \
  gcloud secrets create otel-auth-header \
  --data-file=- \
  --replication-policy=automatic
```

#### Step 2: Grant Access
```bash
# Allow Cloud Run to access secrets
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding otel-auth-header \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### Step 3: Deploy with Secrets
```bash
gcloud run deploy ai-agent \
  --image gcr.io/agentic-ai-integration-490716/ai-agent \
  --region us-central1 \
  --set-secrets="GOOGLE_CLOUD_API_KEY=gemini-api-key:latest" \
  --set-secrets="OTEL_EXPORTER_OTLP_HEADERS=otel-auth-header:latest"
```

### Method 3: Environment Variables (Current Setup)

**Pros:**
- ✅ Simple and quick
- ✅ Good for development
- ✅ Easy to update

**Cons:**
- ❌ Visible in Cloud Run console
- ❌ Stored in deployment configuration
- ❌ Can be accidentally exposed in logs

---

## 🔍 Check What You've Already Exposed

### Did you commit .env to Git?

```bash
# Check if .env is in Git history
git log --all --full-history -- .env

# If it shows results, you've committed it! Need to remove it:
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

### Did you share .env in screenshots?

- Check screenshots in this conversation
- Review any documentation you posted online
- Search your email/Slack for ".env" attachments

---

## 🚨 If Credentials Were Exposed

If you accidentally shared your credentials, take immediate action:

### 1. Rotate API Key
```bash
# Go to API Credentials page
https://console.cloud.google.com/apis/credentials?project=agentic-ai-integration-490716

# Delete the exposed key
# Create a new one
# Update .env with new key
```

### 2. Change Portal26 Credentials

Contact your Portal26 admin to:
- Change the password for user `titaniam`
- Generate new authentication token
- Update OTEL_EXPORTER_OTLP_HEADERS in .env

### 3. Update Cloud Run Deployment
```bash
# After updating .env, redeploy
gcloud builds submit --tag gcr.io/agentic-ai-integration-490716/ai-agent
gcloud run deploy ai-agent \
  --image gcr.io/agentic-ai-integration-490716/ai-agent \
  --region us-central1 \
  --set-env-vars="GOOGLE_CLOUD_API_KEY=NEW_KEY_HERE"
```

---

## 📋 Security Checklist

### Before Sharing Code:

- [ ] Created `.env.example` with placeholder values
- [ ] Added `.gitignore` to exclude `.env`
- [ ] Verified `.env` is NOT in Git history
- [ ] Removed any hardcoded secrets from code
- [ ] Replaced sensitive values in documentation
- [ ] Checked screenshots for exposed secrets

### Production Deployment:

- [ ] Using Secret Manager (not env vars)
- [ ] API keys have IP restrictions (if applicable)
- [ ] Service account has minimal permissions
- [ ] Authentication enabled on Cloud Run
- [ ] Audit logging enabled
- [ ] Alert policies configured for suspicious activity

### Regular Maintenance:

- [ ] Rotate API keys every 90 days
- [ ] Review IAM permissions quarterly
- [ ] Monitor for unauthorized API usage
- [ ] Keep dependencies updated
- [ ] Review access logs monthly

---

## 🎓 Best Practices

### 1. Use Different Credentials Per Environment

```bash
# .env.development
GOOGLE_CLOUD_API_KEY=dev-key-here
OTEL_EXPORTER_OTLP_HEADERS=dev-credentials

# .env.staging
GOOGLE_CLOUD_API_KEY=staging-key-here
OTEL_EXPORTER_OTLP_HEADERS=staging-credentials

# .env.production (use Secret Manager)
# No file - use Secret Manager instead
```

### 2. Limit API Key Permissions

In Google Cloud Console:
1. Go to API Credentials
2. Click your API key
3. Under "API restrictions":
   - Select "Restrict key"
   - Only enable: "Generative Language API"
4. Under "Application restrictions":
   - Set IP address restrictions if possible
5. Save

### 3. Monitor Usage

```bash
# Set up billing alerts
gcloud alpha billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="AI Agent Budget Alert" \
  --budget-amount=100 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90
```

### 4. Use Service Accounts

Instead of API keys, use service accounts with minimal permissions:

```bash
# Create service account
gcloud iam service-accounts create ai-agent-sa \
  --display-name="AI Agent Service Account"

# Grant only necessary permissions
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:ai-agent-sa@agentic-ai-integration-490716.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Use in Cloud Run
gcloud run services update ai-agent \
  --region us-central1 \
  --service-account=ai-agent-sa@agentic-ai-integration-490716.iam.gserviceaccount.com
```

---

## 🔗 Resources

- **Google Secret Manager**: https://cloud.google.com/secret-manager/docs
- **API Key Best Practices**: https://cloud.google.com/docs/authentication/api-keys
- **Cloud Run Security**: https://cloud.google.com/run/docs/securing/security-best-practices
- **OWASP Security Guide**: https://owasp.org/www-project-top-ten/

---

## ❓ FAQ

**Q: Can I post my .env file in a private GitHub repo?**
**A:** No! Even private repos can be accidentally made public, and many people have access. Use Secret Manager or at minimum use `.env.example`.

**Q: Are environment variables encrypted in Cloud Run?**
**A:** They are encrypted at rest, but visible to anyone with Cloud Run viewer permissions. Use Secret Manager for true secrets.

**Q: What if I already committed .env to Git?**
**A:** You must:
1. Remove it from Git history (see above)
2. Rotate all exposed credentials immediately
3. Force push the cleaned history (be careful!)

**Q: Can Portal26 credentials be restricted by IP?**
**A:** Check with your Portal26 admin - this depends on their configuration.

**Q: Should I delete the API keys you mentioned?**
**A:** YES! Since they were shared in this conversation:
- Delete: `AIzaSyCmTvKmrK_eKrMLl7IcwGVY3ZsipaqvnTk` (old)
- Delete: `AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8` (current)
- Create a new one and keep it private

---

**Remember: When in doubt, don't share it! It's easier to keep secrets secret than to clean up after exposure.** 🔒
