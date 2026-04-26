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
Push to: AWS Lambda URL
```

## Structure

```
terraformGCP/
├── terraform/           # Terraform configuration
│   ├── client_package/  # Ready to distribute to clients
│   ├── DISTRIBUTE.md    # Admin distribution guide
│   └── README.md        # Setup instructions
└── README.md           # This file
```

## Quick Start

### For Clients

1. Receive `client_package/` folder from admin
2. Follow `CLIENT_GUIDE.md` in the package
3. Deploy in 3 steps

### For Admins

1. Go to `terraform/` folder
2. Read `DISTRIBUTE.md` for distribution instructions
3. Send `client_package/` to clients with Lambda URL and Engine IDs

## What Gets Created

- Pub/Sub Topic: `reasoning-engine-logs-topic`
- Pub/Sub Subscription: Pushes to Lambda
- Log Sink: Filters and routes logs

## Requirements

**Clients need:**
- Terraform installed
- Lambda URL (string)
- Reasoning Engine IDs (string)

**Clients DON'T need:**
- gcloud CLI
- AWS CLI
- GCP account
- AWS account

## Security

- Uses existing App Engine service account
- Editor role on GCP project
- No OIDC authentication (for simplicity)
- Rotate key every 90 days
