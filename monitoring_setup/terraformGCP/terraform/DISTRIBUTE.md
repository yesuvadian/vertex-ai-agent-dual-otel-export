# How to Send to Clients

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
