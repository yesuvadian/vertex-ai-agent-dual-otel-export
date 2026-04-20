#!/bin/bash
# Vendor Script - Grant Permission to Customer
# Run this after customer sends you their service account

set -e

echo "=========================================="
echo "Grant Customer Permission to Pub/Sub Topic"
echo "=========================================="
echo ""

# Your configuration
YOUR_PROJECT="agentic-ai-integration-490716"
YOUR_TOPIC="all-customers-logs"

# Customer information (fill these after customer provides)
CUSTOMER_SERVICE_ACCOUNT=""
CUSTOMER_PROJECT_ID=""
CUSTOMER_NAME=""

# Check if variables are set
if [ -z "$CUSTOMER_SERVICE_ACCOUNT" ] || [ -z "$CUSTOMER_PROJECT_ID" ]; then
    echo "Please edit this script and fill in:"
    echo "  CUSTOMER_SERVICE_ACCOUNT - The service account customer sent you"
    echo "  CUSTOMER_PROJECT_ID - The customer's GCP project ID"
    echo "  CUSTOMER_NAME - (Optional) Customer friendly name for tracking"
    echo ""
    echo "Example:"
    echo "  CUSTOMER_SERVICE_ACCOUNT=\"serviceAccount:o-123456@gcp-sa-logging.iam.gserviceaccount.com\""
    echo "  CUSTOMER_PROJECT_ID=\"customer-project-123\""
    echo "  CUSTOMER_NAME=\"Acme Corporation\""
    exit 1
fi

echo "Configuration:"
echo "  Your Project: $YOUR_PROJECT"
echo "  Your Topic: $YOUR_TOPIC"
echo "  Customer SA: $CUSTOMER_SERVICE_ACCOUNT"
echo "  Customer Project: $CUSTOMER_PROJECT_ID"
echo "  Customer Name: $CUSTOMER_NAME"
echo ""
read -p "Grant permission? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Granting pubsub.publisher permission..."
gcloud pubsub topics add-iam-policy-binding $YOUR_TOPIC \
  --member="$CUSTOMER_SERVICE_ACCOUNT" \
  --role=roles/pubsub.publisher \
  --project=$YOUR_PROJECT

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "SUCCESS! Permission granted."
    echo "============================================"
    echo ""
    echo "Customer logs will now flow to your topic: $YOUR_TOPIC"
    echo ""
    echo "Tracking information:"
    echo "  Customer: $CUSTOMER_NAME"
    echo "  Project: $CUSTOMER_PROJECT_ID"
    echo "  Service Account: $CUSTOMER_SERVICE_ACCOUNT"
    echo "  Date: $(date)"
    echo ""
    echo "To verify logs arriving:"
    echo "  gcloud pubsub subscriptions pull all-customers-logs-sub --limit=5 --project=$YOUR_PROJECT"
    echo ""
    echo "To query in Portal26:"
    echo "  customer.project_id = \"$CUSTOMER_PROJECT_ID\""
    echo ""
    echo "============================================"
else
    echo "ERROR: Failed to grant permission"
    exit 1
fi
