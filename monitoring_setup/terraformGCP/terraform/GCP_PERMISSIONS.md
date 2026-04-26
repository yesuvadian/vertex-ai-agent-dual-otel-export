# GCP Permissions

## Service Account Used

**Email:** `agentic-ai-integration-490716@appspot.gserviceaccount.com`  
**Type:** App Engine default service account  
**Role:** Editor

## Permissions Included in Editor Role

The service account has Editor role which includes:

### Required for This Setup:
- `logging.sinks.create` - Create log sink
- `logging.sinks.update` - Update log sink
- `logging.sinks.delete` - Delete log sink
- `pubsub.topics.create` - Create Pub/Sub topic
- `pubsub.topics.publish` - Publish to topic
- `pubsub.subscriptions.create` - Create subscription
- `pubsub.subscriptions.update` - Update subscription
- `pubsub.subscriptions.delete` - Delete subscription

## What Clients Can Do

With the service account key, clients can:
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

- Key file provides Editor access
- Scope limited to what Terraform creates
- Rotate key every 90 days
- Send via secure channel only
