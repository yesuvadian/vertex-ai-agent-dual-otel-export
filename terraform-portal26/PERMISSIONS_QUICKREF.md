# Permissions Quick Reference

**TL;DR:** Run `./scripts/setup_terraform_sa.sh PROJECT_ID` and you're done.

For full details, see [PERMISSIONS.md](PERMISSIONS.md)

---

## Approach 1: One-Time Injection (Commit Code)

**Who:** Individual developer deploying locally

**Setup:**

```bash
# Grant permissions to your user
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/storage.objectAdmin"
```

**Required Roles:**
- ✅ `roles/aiplatform.user`
- ✅ `roles/storage.objectAdmin`

**What it enables:** Deploy agents with Portal 26 integration

---

## Approach 2: Terraform Automation

**Who:** Service account for automated deployments

**Setup:**

```bash
# Option A: Automated (recommended)
./scripts/setup_terraform_sa.sh PROJECT_ID

# Option B: Manual
gcloud iam service-accounts create portal26-terraform \
  --display-name="Portal 26 Terraform"

SA_EMAIL="portal26-terraform@PROJECT_ID.iam.gserviceaccount.com"

# Grant all required roles
for ROLE in \
  roles/aiplatform.admin \
  roles/storage.admin \
  roles/serviceusage.serviceUsageAdmin \
  roles/iam.serviceAccountUser
do
  gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE"
done

# Create key
gcloud iam service-accounts keys create terraform-sa-key.json \
  --iam-account=$SA_EMAIL

# Use it
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"
```

**Required Roles:**
- ✅ `roles/aiplatform.admin`
- ✅ `roles/storage.admin`
- ✅ `roles/serviceusage.serviceUsageAdmin`
- ✅ `roles/iam.serviceAccountUser`

**What it enables:** Full automated deployment via Terraform

---

## Verify Permissions

```bash
# Check if service account has all required permissions
./scripts/verify_permissions.sh SA_EMAIL PROJECT_ID

# Example
./scripts/verify_permissions.sh \
  portal26-terraform@my-project.iam.gserviceaccount.com \
  my-project
```

**Output:**
```
✅ Vertex AI Admin (roles/aiplatform.admin)      ✅ GRANTED
✅ Storage Admin (roles/storage.admin)          ✅ GRANTED
✅ Service Account User                         ✅ GRANTED
✅ Service Usage Admin                          ✅ GRANTED

✅ Vertex AI API                                ✅ ENABLED
✅ Cloud Build API                              ✅ ENABLED
✅ Cloud Storage API                            ✅ ENABLED

✅ All checks passed!
```

---

## Troubleshooting

### "Permission denied"

**Solution:** Run the setup script:
```bash
./scripts/setup_terraform_sa.sh PROJECT_ID
```

### "API not enabled"

**Solution:** Enable manually:
```bash
gcloud services enable \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  --project=PROJECT_ID
```

### "Cannot act as service account"

**Solution:** Grant `iam.serviceAccountUser`:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/iam.serviceAccountUser"
```

---

## Security Checklist

- [ ] Service account key stored securely (not in git)
- [ ] Key file added to `.gitignore`
- [ ] Minimum required permissions granted (not `roles/editor`)
- [ ] Key rotation schedule established (every 90 days)
- [ ] Audit logging enabled
- [ ] Access restricted to authorized personnel only

---

## Quick Commands

```bash
# Setup everything
./scripts/setup_terraform_sa.sh my-project

# Verify
./scripts/verify_permissions.sh portal26-terraform@my-project.iam.gserviceaccount.com my-project

# Use
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-sa-key.json"

# Deploy
cd terraform && terraform apply

# Rotate key (after 90 days)
gcloud iam service-accounts keys create new-key.json --iam-account=SA_EMAIL
# Update secrets/configs with new-key.json
gcloud iam service-accounts keys delete OLD_KEY_ID --iam-account=SA_EMAIL
```

---

**Full documentation:** [PERMISSIONS.md](PERMISSIONS.md)
