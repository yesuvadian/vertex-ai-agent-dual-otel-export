# Multi-Customer Lambda Architecture - Complete Workflow

## Overview: How Multiple Customers Work Together

```
Customer 1 (Session 1) → Lambda-customer1 → Portal26 (customer.id=customer1)
Customer 2 (Session 2) → Lambda-customer2 → Portal26 (customer.id=customer2)
Customer 3 (Session 3) → Lambda-customer3 → Portal26 (customer.id=customer3)
...
Customer 30 (Session 30) → Lambda-customer30 → Portal26 (customer.id=customer30)
```

Each customer has:
- ✅ Dedicated Lambda function
- ✅ Dedicated endpoint URL
- ✅ Isolated logs and metrics
- ✅ Independent configuration
- ✅ Separate data in Portal26

---

## Step-by-Step: Complete Multi-Customer Setup

### Phase 1: Infrastructure Setup (One Time)

#### Step 1.1: Create Shared Lambda Authorizer (Optional)

**If using OIDC authentication:**

```bash
# 1. Create authorizer Lambda code
cat > authorizer.py <<'EOF'
import json
import jwt
import requests
from functools import lru_cache

# Customer allowlist (service account → customer_id mapping)
CUSTOMER_ALLOWLIST = {
    "customer1@project.iam.gserviceaccount.com": "customer1",
    "customer2@project.iam.gserviceaccount.com": "customer2",
    "customer3@project.iam.gserviceaccount.com": "customer3",
}

@lru_cache(maxsize=1)
def get_google_public_keys():
    """Fetch Google's public keys for JWT verification"""
    response = requests.get("https://www.googleapis.com/oauth2/v3/certs")
    return response.json()

def lambda_handler(event, context):
    """Validate OIDC token from GCP Pub/Sub"""
    try:
        # Extract token from Authorization header
        token = event['headers'].get('Authorization', '').replace('Bearer ', '')
        
        # Verify JWT signature
        jwks = get_google_public_keys()
        decoded = jwt.decode(token, jwks, algorithms=["RS256"])
        
        # Extract service account email
        service_account = decoded.get('email')
        
        # Check if service account is in allowlist
        if service_account not in CUSTOMER_ALLOWLIST:
            return generate_policy('Deny', event['methodArn'])
        
        customer_id = CUSTOMER_ALLOWLIST[service_account]
        
        # Generate Allow policy with customer context
        return generate_policy('Allow', event['methodArn'], {
            'customer_id': customer_id,
            'service_account': service_account
        })
        
    except Exception as e:
        print(f"Authorization error: {str(e)}")
        return generate_policy('Deny', event['methodArn'])

def generate_policy(effect, resource, context=None):
    """Generate IAM policy document"""
    return {
        'principalId': context.get('customer_id', 'unknown') if context else 'unknown',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        },
        'context': context or {}
    }
EOF

# 2. Deploy authorizer Lambda
zip authorizer.zip authorizer.py
aws lambda create-function \
  --function-name gcp-pubsub-authorizer \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-authorizer-role \
  --handler authorizer.lambda_handler \
  --zip-file fileb://authorizer.zip \
  --region us-east-1
```

**Cost:** +$1.50/month (shared across all customers)

---

### Phase 2: Add Customer 1 (First Customer)

#### Step 2.1: Create Lambda Function for Customer 1

```bash
# 1. Prepare Lambda code
cat > lambda_customer1.py <<'EOF'
import json
import base64
import requests
import os

CUSTOMER_ID = os.environ['CUSTOMER_ID']  # "customer1"
PORTAL26_ENDPOINT = os.environ['PORTAL26_ENDPOINT']

def lambda_handler(event, context):
    """Handler for Customer 1 messages"""
    try:
        # Parse Pub/Sub message
        body = json.loads(event['body'])
        message = body['message']
        
        # Decode message data
        message_data = base64.b64decode(message['data']).decode('utf-8')
        
        # Convert to OTEL format
        otel_log = {
            "timeUnixNano": str(int(time.time() * 1_000_000_000)),
            "severityText": "INFO",
            "severityNumber": 9,
            "body": {"stringValue": message_data},
            "attributes": [
                {"key": "customer.id", "value": {"stringValue": CUSTOMER_ID}},
                {"key": "messageId", "value": {"stringValue": message['messageId']}}
            ]
        }
        
        # Send to Portal26
        payload = {
            "resourceLogs": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": f"gcp-vertex-{CUSTOMER_ID}"}},
                        {"key": "customer.id", "value": {"stringValue": CUSTOMER_ID}}
                    ]
                },
                "scopeLogs": [{
                    "scope": {"name": "gcp-pubsub", "version": "1.0.0"},
                    "logRecords": [otel_log]
                }]
            }]
        }
        
        response = requests.post(
            f"{PORTAL26_ENDPOINT}/v1/logs",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success', 'customer': CUSTOMER_ID})
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
EOF

# 2. Package and deploy
zip function_customer1.zip lambda_customer1.py

aws lambda create-function \
  --function-name webhook-customer1 \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-gcp-pubsub-role \
  --handler lambda_customer1.lambda_handler \
  --zip-file fileb://function_customer1.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{CUSTOMER_ID=customer1,PORTAL26_ENDPOINT=https://otel.portal26.in:4318}" \
  --region us-east-1
```

#### Step 2.2: Create Function URL for Customer 1

```bash
# Create Function URL
CUSTOMER1_URL=$(aws lambda create-function-url-config \
  --function-name webhook-customer1 \
  --auth-type NONE \
  --region us-east-1 \
  --query 'FunctionUrl' \
  --output text)

# Add permission
aws lambda add-permission \
  --function-name webhook-customer1 \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region us-east-1

echo "Customer 1 URL: $CUSTOMER1_URL"
# Output: https://abc123.lambda-url.us-east-1.on.aws/
```

#### Step 2.3: Configure Customer 1's GCP Pub/Sub

```bash
# Customer 1 creates service account (in their GCP project)
gcloud iam service-accounts create customer1-pubsub \
  --display-name "Customer 1 Pub/Sub Forwarder" \
  --project customer1-gcp-project

# Customer 1 creates push subscription to their Lambda URL
gcloud pubsub subscriptions create customer1-aws-webhook \
  --topic customer1-telemetry-topic \
  --push-endpoint $CUSTOMER1_URL \
  --push-auth-service-account customer1-pubsub@customer1-gcp-project.iam.gserviceaccount.com \
  --project customer1-gcp-project
```

#### Step 2.4: Test Customer 1 Flow

```bash
# Terminal 1: Watch Lambda logs
aws logs tail /aws/lambda/webhook-customer1 --follow

# Terminal 2: Send test message
gcloud pubsub topics publish customer1-telemetry-topic \
  --message "Test from Customer 1" \
  --project customer1-gcp-project

# Expected in Terminal 1:
# [INFO] Processing message for customer1
# [SUCCESS] Forwarded to Portal26
```

**Result:** ✅ Customer 1 working independently

---

### Phase 3: Add Customer 2 (Second Customer)

#### Step 3.1: Create Lambda Function for Customer 2

```bash
# 1. Create Lambda (same code, different config)
cp lambda_customer1.py lambda_customer2.py

zip function_customer2.zip lambda_customer2.py

aws lambda create-function \
  --function-name webhook-customer2 \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-gcp-pubsub-role \
  --handler lambda_customer2.lambda_handler \
  --zip-file fileb://function_customer2.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{CUSTOMER_ID=customer2,PORTAL26_ENDPOINT=https://otel.portal26.in:4318}" \
  --region us-east-1
```

**Note:** Customer 2 uses 256MB (smaller) vs Customer 1's 512MB

#### Step 3.2: Create Function URL for Customer 2

```bash
CUSTOMER2_URL=$(aws lambda create-function-url-config \
  --function-name webhook-customer2 \
  --auth-type NONE \
  --region us-east-1 \
  --query 'FunctionUrl' \
  --output text)

aws lambda add-permission \
  --function-name webhook-customer2 \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region us-east-1

echo "Customer 2 URL: $CUSTOMER2_URL"
# Output: https://def456.lambda-url.us-east-1.on.aws/
```

#### Step 3.3: Configure Customer 2's GCP Pub/Sub

```bash
# Customer 2 setup (in their GCP project)
gcloud iam service-accounts create customer2-pubsub \
  --project customer2-gcp-project

gcloud pubsub subscriptions create customer2-aws-webhook \
  --topic customer2-telemetry-topic \
  --push-endpoint $CUSTOMER2_URL \
  --push-auth-service-account customer2-pubsub@customer2-gcp-project.iam.gserviceaccount.com \
  --project customer2-gcp-project
```

#### Step 3.4: Test Both Customers Working Together

```bash
# Terminal 1: Customer 1 logs
aws logs tail /aws/lambda/webhook-customer1 --follow

# Terminal 2: Customer 2 logs
aws logs tail /aws/lambda/webhook-customer2 --follow

# Terminal 3: Send messages from both customers
gcloud pubsub topics publish customer1-telemetry-topic \
  --message "Message from Customer 1" \
  --project customer1-gcp-project

gcloud pubsub topics publish customer2-telemetry-topic \
  --message "Message from Customer 2" \
  --project customer2-gcp-project
```

**Result:** 
- ✅ Terminal 1 shows only Customer 1 messages
- ✅ Terminal 2 shows only Customer 2 messages
- ✅ Complete isolation confirmed

---

### Phase 4: Add Customer 3 (Enterprise Customer)

#### Step 4.1: Create Lambda with Custom Configuration

```bash
# Enterprise customer gets more resources
aws lambda create-function \
  --function-name webhook-customer3 \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-gcp-pubsub-role \
  --handler lambda_customer3.lambda_handler \
  --zip-file fileb://function_customer3.zip \
  --timeout 120 \
  --memory-size 2048 \
  --reserved-concurrent-executions 200 \
  --environment Variables="{CUSTOMER_ID=customer3,PORTAL26_ENDPOINT=https://customer3.portal26.in:4318}" \
  --region us-east-1
```

**Enterprise Features:**
- 2048MB memory (vs 512MB standard)
- 120s timeout (vs 30s standard)
- Reserved 200 concurrent executions (guaranteed capacity)
- Custom Portal26 endpoint (dedicated instance)

#### Step 4.2: Create Function URL and Configure

```bash
# Same process as Customer 1 and 2
CUSTOMER3_URL=$(aws lambda create-function-url-config \
  --function-name webhook-customer3 \
  --auth-type NONE \
  --region us-east-1 \
  --query 'FunctionUrl' \
  --output text)

# GCP configuration by Customer 3
gcloud pubsub subscriptions create customer3-aws-webhook \
  --topic customer3-telemetry-topic \
  --push-endpoint $CUSTOMER3_URL \
  --project customer3-gcp-project
```

**Result:** ✅ 3 customers, each with dedicated infrastructure

---

## Complete Message Flow: Multi-Customer Sessions

### Session 1: Customer 1 Sends Message

```
Step 1: Customer 1's GCP Reasoning Engine generates log
  └─> GCP Logs → Pub/Sub topic: customer1-telemetry-topic

Step 2: GCP Pub/Sub pushes to Customer 1's Lambda URL
  └─> POST https://abc123.lambda-url.us-east-1.on.aws/
  └─> Headers: Authorization: Bearer <OIDC_TOKEN>
  └─> Body: {"message": {"data": "...", "messageId": "..."}}

Step 3: AWS Lambda-customer1 receives and processes
  └─> Decodes base64 data
  └─> Adds customer.id = "customer1"
  └─> Converts to OTEL format

Step 4: Lambda-customer1 forwards to Portal26
  └─> POST https://otel.portal26.in:4318/v1/logs
  └─> Attributes: customer.id = "customer1"

Step 5: Portal26 stores with customer isolation
  └─> Customer 1 queries: WHERE customer.id = "customer1"
  └─> Only sees their own logs
```

### Session 2: Customer 2 Sends Message (Parallel)

```
Step 1: Customer 2's GCP Reasoning Engine generates log
  └─> GCP Logs → Pub/Sub topic: customer2-telemetry-topic

Step 2: GCP Pub/Sub pushes to Customer 2's Lambda URL
  └─> POST https://def456.lambda-url.us-east-1.on.aws/
  └─> Different URL, different Lambda

Step 3: AWS Lambda-customer2 receives and processes
  └─> Completely separate from Lambda-customer1
  └─> Adds customer.id = "customer2"
  └─> Different CloudWatch Log group

Step 4: Lambda-customer2 forwards to Portal26
  └─> Same Portal26 endpoint
  └─> Attributes: customer.id = "customer2"

Step 5: Portal26 stores with customer isolation
  └─> Customer 2 queries: WHERE customer.id = "customer2"
  └─> Only sees their own logs
```

**Key Point:** Sessions run completely independently and in parallel.

---

## Scaling: Add Customers 4-30

### Automated Script for Adding Customers

```bash
#!/bin/bash
# add_customer.sh - Add a new customer

CUSTOMER_ID=$1
MEMORY_SIZE=${2:-512}  # Default 512MB
TIMEOUT=${3:-30}       # Default 30s

echo "Adding customer: $CUSTOMER_ID"

# 1. Create Lambda function
aws lambda create-function \
  --function-name webhook-$CUSTOMER_ID \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-gcp-pubsub-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout $TIMEOUT \
  --memory-size $MEMORY_SIZE \
  --environment Variables="{CUSTOMER_ID=$CUSTOMER_ID,PORTAL26_ENDPOINT=https://otel.portal26.in:4318}" \
  --region us-east-1

# 2. Create Function URL
CUSTOMER_URL=$(aws lambda create-function-url-config \
  --function-name webhook-$CUSTOMER_ID \
  --auth-type NONE \
  --region us-east-1 \
  --query 'FunctionUrl' \
  --output text)

# 3. Add permission
aws lambda add-permission \
  --function-name webhook-$CUSTOMER_ID \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region us-east-1

echo "Customer $CUSTOMER_ID added successfully!"
echo "Lambda URL: $CUSTOMER_URL"
echo ""
echo "Customer should configure GCP Pub/Sub:"
echo "  gcloud pubsub subscriptions create ${CUSTOMER_ID}-aws-webhook \\"
echo "    --topic ${CUSTOMER_ID}-telemetry-topic \\"
echo "    --push-endpoint $CUSTOMER_URL \\"
echo "    --project ${CUSTOMER_ID}-gcp-project"
```

### Add Customers 4-30

```bash
# Standard customers (512MB, 30s timeout)
for i in {4..29}; do
  ./add_customer.sh customer$i 512 30
  sleep 2
done

# Enterprise customer 30 (2048MB, 120s timeout, reserved concurrency)
./add_customer.sh customer30 2048 120

# Manually add reserved concurrency for enterprise
aws lambda put-function-concurrency \
  --function-name webhook-customer30 \
  --reserved-concurrent-executions 200
```

**Time:** ~2 minutes per customer = ~50 minutes for 26 customers

---

## Monitoring Multiple Customer Sessions

### Dashboard: All Customers Overview

```bash
# Create aggregate CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name all-customers-overview \
  --dashboard-body file://dashboard.json
```

**dashboard.json:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Invocations by Customer",
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Customer 1"}, {"dimensions": {"FunctionName": "webhook-customer1"}}],
          ["...", {"dimensions": {"FunctionName": "webhook-customer2"}}],
          ["...", {"dimensions": {"FunctionName": "webhook-customer3"}}]
        ],
        "period": 300,
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Error Rate by Customer",
        "metrics": [
          ["AWS/Lambda", "Errors", {"stat": "Sum"}],
          [".", "Invocations", {"stat": "Sum", "visible": false}]
        ],
        "period": 300
      }
    }
  ]
}
```

### Per-Customer Monitoring

```bash
# Watch specific customer's logs
aws logs tail /aws/lambda/webhook-customer1 --follow

# Get customer-specific metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=webhook-customer1 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## Testing Multi-Customer Sessions Simultaneously

### Load Test: All Customers Sending Messages

```bash
#!/bin/bash
# load_test_all_customers.sh

echo "Starting load test for all 30 customers..."

# Send messages from all customers in parallel
for i in {1..30}; do
  (
    for j in {1..10}; do
      gcloud pubsub topics publish customer${i}-telemetry-topic \
        --message "Load test message #$j from Customer $i" \
        --project customer${i}-gcp-project
      sleep 0.1
    done
  ) &
done

wait
echo "Load test complete! Sent 300 messages (10 per customer)"
```

### Verify All Sessions Working

```bash
# Check invocations for all customers
for i in {1..30}; do
  COUNT=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=webhook-customer$i \
    --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Sum \
    --query 'Datapoints[0].Sum' \
    --output text)
  
  echo "Customer $i: $COUNT invocations"
done
```

---

## Summary: Multi-Customer Session Architecture

### What "Multi-Session" Means

1. **Independent Sessions**: Each customer operates independently
2. **Parallel Processing**: All 30 customers can send messages simultaneously
3. **Isolated State**: Each Lambda has its own logs, metrics, configuration
4. **Separate Endpoints**: Each customer has unique URL
5. **No Cross-Talk**: Customer 1 cannot see Customer 2's data

### Resource Allocation

| Resource | Per Customer | 30 Customers Total |
|----------|-------------|-------------------|
| Lambda Functions | 1 | 30 |
| Lambda URLs | 1 | 30 |
| CloudWatch Log Groups | 1 | 30 |
| IAM Roles | Shared | 1 |
| Authorizer Lambda | Shared | 1 (optional) |

### Cost Breakdown (30 Customers)

| Component | Monthly Cost |
|-----------|-------------|
| 30 Lambda Functions | $6.06 |
| CloudWatch Logs | $15.00 |
| CloudWatch Metrics | $30.00 |
| CloudWatch Dashboards | $90.00 (optional) |
| Authorizer Lambda | $1.50 (optional) |
| **Total Basic** | **$51.06** |
| **Total with Dashboards** | **$142.56** |

**Cost per Customer:** $1.70 - $4.75/month

---

## Quick Start Checklist

```
Phase 1: Initial Setup
□ Create shared IAM role (lambda-gcp-pubsub-role)
□ Create Lambda function code (one template for all)
□ Create deployment script (add_customer.sh)
□ Optional: Create shared authorizer Lambda

Phase 2: Add First Customer
□ Deploy Lambda-customer1
□ Create Function URL
□ Test Lambda directly
□ Configure customer's GCP Pub/Sub
□ Verify end-to-end flow

Phase 3: Add Second Customer
□ Deploy Lambda-customer2
□ Create Function URL
□ Test both customers independently
□ Verify isolation between customers

Phase 4: Scale to 30 Customers
□ Use automated script to add customers 3-30
□ Verify all Lambda functions deployed
□ Configure GCP for each customer
□ Run load test across all customers

Phase 5: Monitoring
□ Create aggregate dashboard
□ Set up per-customer alarms
□ Configure log aggregation
□ Test failover scenarios
```

---

## Next Steps

1. **Complete POC** - Get Lambda Function URL working for customer 1
2. **Test Isolation** - Add customer 2, verify separate sessions
3. **Automate** - Create scripts to add customers quickly
4. **Monitor** - Set up dashboards and alarms
5. **Scale** - Add remaining customers (3-30)
6. **Secure** - Add OIDC authentication
7. **Optimize** - Right-size memory, add reserved concurrency for enterprise

**Total Time:** 
- POC (1 customer): 15 minutes
- Add customers 2-30: 1 hour
- Monitoring setup: 30 minutes
- **Total: ~2 hours to full 30-customer production system**
