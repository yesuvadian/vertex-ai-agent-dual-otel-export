# GCP Permissions Setup

## Service Account Used

**Email:** `agentic-ai-integration-490716@appspot.gserviceaccount.com`  
**Type:** App Engine default service account

## Required Roles

The service account needs **TWO roles** for this deployment:

### 1. Editor (for Pub/Sub)
**Role:** `roles/editor`  
**Permissions:**
- `pubsub.topics.create` - Create Pub/Sub topic
- `pubsub.topics.publish` - Publish to topic
- `pubsub.subscriptions.create` - Create subscription
- `pubsub.subscriptions.update` - Update subscription
- `pubsub.subscriptions.delete` - Delete subscription

### 2. Logging Admin (for Log Sinks) ⚠️ **REQUIRED!**
**Role:** `roles/logging.admin`  
**Permissions:**
- `logging.sinks.create` - Create log sink
- `logging.sinks.update` - Update log sink
- `logging.sinks.delete` - Delete log sink

**⚠️ IMPORTANT:** Editor role does NOT include logging.sinks permissions!

---

## How to Add Logging Admin Role

### Via GCP Console:
1. Go to: https://console.cloud.google.com/iam-admin/iam?project=agentic-ai-integration-490716
2. Find: `agentic-ai-integration-490716@appspot.gserviceaccount.com`
3. Click **Edit** (pencil icon)
4. Click **ADD ANOTHER ROLE**
5. Search and select: **`Logging Admin`**
6. Click **SAVE**

### Via gcloud CLI:
```bash
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="serviceAccount:agentic-ai-integration-490716@appspot.gserviceaccount.com" \
  --role="roles/logging.admin"
```

---

## What Clients Can Do

With the service account key (after both roles are added):
- ✅ Create/modify Pub/Sub resources
- ✅ Create/modify log sinks
- ✅ Deploy Terraform infrastructure

## What Clients Cannot Do

Clients CANNOT:
- ❌ Access GCP Console (no user account)
- ❌ Modify IAM policies
- ❌ Delete other project resources
- ❌ Access other services outside Terraform scope

## Security

- Key file provides Editor + Logging Admin access
- Scope limited to what Terraform creates
- Rotate key every 90 days
- Send via secure channel only

## Troubleshooting

**Error:** `Permission 'logging.sinks.update' denied`  
**Solution:** Add `roles/logging.admin` to the service account (see above)
