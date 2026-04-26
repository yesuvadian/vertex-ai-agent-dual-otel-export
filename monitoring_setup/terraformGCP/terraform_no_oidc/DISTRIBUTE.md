# How to Distribute to Clients

## Package Contents

Send the `client_package/` folder containing:
- `CLIENT_GUIDE.md`
- `main.tf`
- `gcp_log_sink_pubsub.tf`
- `terraform.tfvars.example`
- `appengine-sa-key.json`

## What to Provide

Send to client:
1. The `client_package/` folder (or zip it)
2. Their AWS Lambda URL
3. Their Reasoning Engine IDs

## Client Requirements

Client needs:
- Terraform installed
- Lambda URL (just the URL string)
- Reasoning Engine IDs

Client does NOT need:
- gcloud CLI
- AWS CLI
- GCP account
- AWS account

## Security

- Send package via secure channel
- Key file gives Editor access to GCP project
- Rotate key every 90 days
