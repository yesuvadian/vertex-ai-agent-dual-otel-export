# Multi-Client Implementation Guide

## Overview

Both forwarders now support **automatic multi-client identification**. Each customer's logs are automatically tagged with their unique identifiers for filtering in Portal26.

---

## What Changed

### Enhanced Forwarders:

**Files Updated:**
- `monitoring_setup/continuous_forwarder.py` (pull-based)
- `push_based_forwarder/main.py` (push-based)

**New Function Added:**
```python
def extract_client_info(log_entry):
    """Extracts customer identification from log entry"""
    # Automatically gets customer project ID, engine ID, location, etc.
```

**Customer Attributes Added to OTEL:**
- `customer.project_id` - Customer's GCP project ID
- `customer.id` - Customer identifier (custom label or project ID)
- `customer.reasoning_engine_id` - Their Reasoning Engine ID
- `customer.agent_id` - Agent identifier (custom label or engine ID)
- `customer.agent_type` - Type of agent (custom label or "reasoning-engine")
- `customer.location` - GCP region (e.g., "us-central1")
- `customer.environment` - Environment tag (custom label or "production")

---

## How Customer Identification Works

### Automatic Extraction (No Configuration Needed):

**From GCP Resource Labels (Always Present):**
```
resource.labels.project_id         → customer.project_id
resource.labels.reasoning_engine_id → customer.reasoning_engine_id
resource.labels.location            → customer.location
```

**These are automatically in every log entry from GCP!**

### Optional: Customer Custom Labels

**If customers label their Reasoning Engines:**
```python
# When customer creates Reasoning Engine
engine = ReasoningEngine.create(
    my_agent,
    labels={
        "customer_id": "acme-corp",       # Custom customer ID
        "agent_id": "billing-agent",      # Friendly agent name
        "agent_type": "billing",          # Agent category
        "environment": "production"       # Environment
    }
)
```

**Forwarder uses custom labels if present, falls back to automatic IDs if not.**

---

## Portal26 Query Examples

### View All Customers:

```
service.name = "gcp-vertex-monitor" 
| stats count by customer.project_id
```

**Output:**
```
customer.project_id               | count
----------------------------------|-------
customer-a-project-123           | 450
customer-b-project-456           | 320
customer-c-project-789           | 180
```

---

### View Logs for Specific Customer:

```
customer.project_id = "customer-a-project-123"
```

---

### View Specific Customer's Agent:

```
customer.project_id = "customer-a-project-123" 
AND customer.reasoning_engine_id = "6010661182900273152"
```

---

### View All Errors for a Customer:

```
customer.project_id = "customer-a-project-123" 
AND severityText = "ERROR"
```

---

### Compare Agent Activity Across Customers:

```
service.name = "gcp-vertex-monitor"
| stats count by customer.project_id, customer.agent_type
| sort by count desc
```

---

### View Specific Agent Type Across All Customers:

```
customer.agent_type = "billing"
```

*(Only works if customers use custom labels)*

---

### View by Location:

```
customer.location = "us-central1"
```

---

### View by Environment:

```
customer.environment = "production"
```

---

## Customer Onboarding Process

### Step 1: You Create Centralized Topic (One-Time)

**Run once in YOUR GCP project:**

```bash
# Create centralized Pub/Sub topic
gcloud pubsub topics create all-customers-logs \
  --project=agentic-ai-integration-490716

# Create subscription for forwarder
gcloud pubsub subscriptions create all-customers-logs-sub \
  --topic=all-customers-logs \
  --ack-deadline=60 \
  --project=agentic-ai-integration-490716
```

---

### Step 2: Customer Creates Log Sink

**Give this script to each customer:**

```bash
#!/bin/bash
# Customer Onboarding Script

# Customer fills these variables
CUSTOMER_PROJECT_ID="their-project-id"
VENDOR_PROJECT_ID="agentic-ai-integration-490716"
VENDOR_TOPIC="all-customers-logs"

echo "Creating log sink in your project..."
gcloud logging sinks create send-logs-to-vendor \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --destination=pubsub.googleapis.com/projects/$VENDOR_PROJECT_ID/topics/$VENDOR_TOPIC \
  --project=$CUSTOMER_PROJECT_ID

echo ""
echo "Getting service account identity..."
SERVICE_ACCOUNT=$(gcloud logging sinks describe send-logs-to-vendor \
  --project=$CUSTOMER_PROJECT_ID \
  --format="value(writerIdentity)")

echo ""
echo "============================================"
echo "IMPORTANT: Send this to your vendor:"
echo "============================================"
echo "Service Account: $SERVICE_ACCOUNT"
echo "Customer Project: $CUSTOMER_PROJECT_ID"
echo "============================================"
```

---

### Step 3: You Grant Permission

**After customer sends you their service account:**

```bash
# Variables (you fill these)
CUSTOMER_SERVICE_ACCOUNT="serviceAccount:o-123456@gcp-sa-logging.iam.gserviceaccount.com"
YOUR_PROJECT="agentic-ai-integration-490716"
YOUR_TOPIC="all-customers-logs"

# Grant permission
gcloud pubsub topics add-iam-policy-binding $YOUR_TOPIC \
  --member="$CUSTOMER_SERVICE_ACCOUNT" \
  --role=roles/pubsub.publisher \
  --project=$YOUR_PROJECT

echo "Done! Customer logs will now flow to your topic."
```

---

### Step 4: Update Forwarder Configuration

**For Continuous Forwarder:**

Edit `monitoring_setup/.env`:

```bash
# Update subscription to use centralized one
PUBSUB_SUBSCRIPTION=all-customers-logs-sub
```

**For Push-Based Forwarder:**

Redeploy with new trigger:

```bash
cd push_based_forwarder

# Edit deploy.bat, change:
# --trigger-topic vertex-telemetry-topic
# to:
# --trigger-topic all-customers-logs

deploy.bat
```

---

### Step 5: Verify Customer Logs Flowing

**Check Pub/Sub for messages:**

```bash
gcloud pubsub subscriptions pull all-customers-logs-sub \
  --limit=1 \
  --project=agentic-ai-integration-490716
```

**Check forwarder logs for customer ID:**

Look for log entries showing:
```
customer.project_id: customer-a-project-123
```

**Check Portal26:**

Query: `customer.project_id = "customer-a-project-123"`

---

## Customer Tracking Table

**Create a simple tracking spreadsheet:**

| Customer Name | Project ID | Service Account | Onboarded Date | Status |
|---------------|------------|-----------------|----------------|--------|
| Acme Corp | customer-a-project-123 | o-111111@gcp-sa-logging... | 2026-04-15 | Active |
| Beta Inc | customer-b-project-456 | o-222222@gcp-sa-logging... | 2026-04-16 | Active |
| Gamma LLC | customer-c-project-789 | o-333333@gcp-sa-logging... | 2026-04-17 | Testing |

---

## Advanced: Customer Lookup Table (Optional)

**If you want friendly customer names instead of project IDs:**

### Create `customers.json`:

```json
{
  "customer-a-project-123": {
    "customer_name": "Acme Corporation",
    "customer_id": "acme-corp",
    "contact_email": "admin@acme.com",
    "tier": "enterprise"
  },
  "customer-b-project-456": {
    "customer_name": "Beta Industries",
    "customer_id": "beta-inc",
    "contact_email": "admin@beta.com",
    "tier": "standard"
  }
}
```

### Modify Forwarder:

Add at top of forwarder:

```python
import json

# Load customer mapping (optional)
CUSTOMER_LOOKUP = {}
try:
    with open('customers.json', 'r') as f:
        CUSTOMER_LOOKUP = json.load(f)
except:
    pass  # No lookup table, use project IDs
```

Update `extract_client_info` function:

```python
def extract_client_info(log_entry):
    # ... existing code ...

    # Lookup friendly customer name (optional)
    if customer_project_id in CUSTOMER_LOOKUP:
        customer_data = CUSTOMER_LOOKUP[customer_project_id]
        customer_id = customer_data.get('customer_id', customer_project_id)
        customer_name = customer_data.get('customer_name', customer_project_id)
        tier = customer_data.get('tier', 'standard')
    else:
        customer_name = customer_project_id
        tier = 'unknown'

    return {
        'customer_project_id': customer_project_id,
        'customer_id': customer_id,
        'customer_name': customer_name,
        'customer_tier': tier,
        # ... rest of fields ...
    }
```

---

## Testing Multi-Client Setup

### Test with Your Own Project First:

**Simulate customer by using a different GCP project (or same project):**

```bash
# In YOUR project, create test log sink
gcloud logging sinks create test-customer-sink \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --destination=pubsub.googleapis.com/projects/agentic-ai-integration-490716/topics/all-customers-logs \
  --project=agentic-ai-integration-490716

# Get service account
SA=$(gcloud logging sinks describe test-customer-sink \
  --project=agentic-ai-integration-490716 \
  --format="value(writerIdentity)")

# Grant permission
gcloud pubsub topics add-iam-policy-binding all-customers-logs \
  --member="$SA" \
  --role=roles/pubsub.publisher \
  --project=agentic-ai-integration-490716

# Trigger your Reasoning Engine
# Check Portal26 for logs with customer.project_id
```

---

## Scaling Considerations

### 10 Customers:
- Single forwarder handles easily
- Cost: ~$15-20/month
- No changes needed

### 100 Customers:
- Still single forwarder (if <10K logs/day per customer)
- Cost: ~$30-50/month
- May want 2 forwarders for redundancy

### 1000+ Customers:
- Option 1: Multiple forwarders (auto load-balanced via Pub/Sub)
- Option 2: Switch to push-based Cloud Function (auto-scales)
- Cost: ~$100-200/month

**Pub/Sub automatically distributes messages across multiple subscribers, so just deploy more forwarder instances if needed.**

---

## Security & Privacy

### Customer Data Isolation:

**In Portal26:**
- All customers' logs in YOUR Portal26 account
- Use customer.project_id to filter per customer
- Consider Portal26 RBAC if you have team members who should only see specific customers

**Network:**
- Customer logs flow through GCP's internal network
- Encrypted in transit (TLS)
- Customer never accesses your Portal26

**Credentials:**
- Customer's log sink service account only has permission to write to YOUR topic
- Customer cannot read from your topic
- Customer cannot access your Portal26

---

## Troubleshooting

### Customer logs not appearing?

**Check 1: Log sink exists in customer project**
```bash
gcloud logging sinks list --project=CUSTOMER_PROJECT
```

**Check 2: Service account has permission**
```bash
gcloud pubsub topics get-iam-policy all-customers-logs \
  --project=agentic-ai-integration-490716
```

Look for customer's service account in output.

**Check 3: Messages in topic**
```bash
gcloud pubsub subscriptions pull all-customers-logs-sub \
  --limit=1 \
  --project=agentic-ai-integration-490716
```

**Check 4: Forwarder processing**
Check forwarder logs for customer.project_id entries.

---

### Can't identify which customer?

**Check log attributes in Portal26:**
```
service.name = "gcp-vertex-monitor"
| fields customer.project_id, customer.reasoning_engine_id, body
```

All logs should have customer.project_id attribute.

---

### Customer wants to stop sending logs?

**Customer deletes log sink:**
```bash
gcloud logging sinks delete send-logs-to-vendor \
  --project=CUSTOMER_PROJECT
```

Logs stop immediately.

**You can also revoke permission (optional cleanup):**
```bash
gcloud pubsub topics remove-iam-policy-binding all-customers-logs \
  --member="serviceAccount:CUSTOMER_SA@gcp-sa-logging.iam.gserviceaccount.com" \
  --role=roles/pubsub.publisher \
  --project=agentic-ai-integration-490716
```

---

## Summary

**What you have now:**
- Automatic multi-client support
- Customer identification in every log
- Easy Portal26 filtering
- Scalable to thousands of customers
- Simple onboarding (2 commands per customer)

**Customer attributes extracted:**
- customer.project_id (always present)
- customer.reasoning_engine_id (always present)
- customer.location (always present)
- Custom labels (if customer adds them)

**Portal26 queries:**
- Filter by customer: `customer.project_id = "..."`
- View all customers: `stats count by customer.project_id`
- Customer errors: `customer.project_id = "..." AND severityText = "ERROR"`

**Deployment:**
- No code changes needed for new customers
- Just grant IAM permission (30 seconds)
- Logs start flowing automatically

**Ready for production multi-client deployment!**
