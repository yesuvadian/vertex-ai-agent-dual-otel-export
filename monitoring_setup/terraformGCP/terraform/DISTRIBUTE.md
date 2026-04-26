# How to Send to Clients

## 0. Generate Service Account Key (First Time Only)

If `appengine-sa-key.json` doesn't exist in `client_package/`:

### From GCP Console:
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=agentic-ai-integration-490716
2. Click on: `agentic-ai-integration-490716@appspot.gserviceaccount.com`
3. Go to **KEYS** tab
4. Click **ADD KEY** → **Create new key**
5. Select **JSON** → **CREATE**
6. Downloaded file will be named like: `agentic-ai-integration-490716-abc123.json`
7. Rename to: `appengine-sa-key.json`
8. Move to: `client_package/appengine-sa-key.json`

### Or from CLI:
```bash
cd client_package/
gcloud iam service-accounts keys create appengine-sa-key.json \
  --iam-account=agentic-ai-integration-490716@appspot.gserviceaccount.com
```

## 1. Zip the Package

```bash
zip -r client-setup.zip client_package/
```

Or just send the `client_package/` folder directly.

## 2. Send to Client

Send via secure channel:
- `client-setup.zip` (or `client_package/` folder)
- Their Lambda URL
- Their Reasoning Engine IDs

## 3. Email Template

```
Subject: GCP Log Sink Setup

Hi [Client],

Attached: client-setup.zip

Your information:
- Lambda URL: https://YOUR-LAMBDA-URL.on.aws
- Engine ID: YOUR-ENGINE-ID

Instructions inside CLIENT_GUIDE.md (3 steps, ~5 minutes)

Requirements: Terraform only (no AWS/GCP CLI needed)
```

## Security

- Key file gives Editor access to GCP project
- Send via secure channel only
- Rotate key every 90 days
