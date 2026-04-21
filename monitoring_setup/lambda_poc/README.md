# GCP Pub/Sub to AWS Lambda - POC Implementation

Complete working code to test GCP Pub/Sub → AWS Lambda integration.

## Files

```
lambda_poc/
├── lambda_function.py    # Lambda handler code
├── deploy.sh            # Automated deployment script
├── test_local.py        # Local testing before deployment
└── README.md           # This file
```

---

## Quick Start

### Step 1: Test Locally

```bash
cd lambda_poc

# Test the Lambda function locally
python test_local.py
```

**Expected output:**
```
╔==========================================================╗
║          Lambda Function Local Tests                    ║
╚==========================================================╝

============================================================
TEST 1: Valid Pub/Sub Message
============================================================
[2025-01-15T10:30:00] === Received event from GCP Pub/Sub ===
...
✅ TEST PASSED

[All 5 tests pass]

╔==========================================================╗
║               ALL TESTS PASSED ✅                        ║
╚==========================================================╝
```

---

### Step 2: Deploy to AWS

```bash
# Make deploy script executable (Linux/Mac)
chmod +x deploy.sh

# Run deployment (works on Linux/Mac/Git Bash on Windows)
./deploy.sh
```

**Or on Windows (PowerShell):**
```powershell
# Convert to PowerShell or run via Git Bash
bash deploy.sh
```

**Deployment process:**
1. ✅ Creates deployment package (function.zip)
2. ✅ Creates/updates Lambda function (gcp-pubsub-test)
3. ✅ Creates IAM role (if needed)
4. ✅ Creates HTTP API Gateway
5. ✅ Configures Lambda permissions
6. ✅ Returns webhook URL

**Expected output:**
```
========================================
✓ DEPLOYMENT SUCCESSFUL!
========================================

Your webhook endpoint:
https://abc123.execute-api.us-east-1.amazonaws.com/webhook

Next steps:
1. Test the endpoint: [curl command]
2. Configure GCP Pub/Sub: [gcloud command]
3. Watch Lambda logs: [aws logs command]
```

---

### Step 3: Test AWS Lambda

```bash
# Get your webhook URL (saved by deploy script)
WEBHOOK_URL=$(cat webhook_url.txt)

# Test the Lambda endpoint
curl -X POST $WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "data": "SGVsbG8gZnJvbSBHQ1A=",
      "messageId": "test-123",
      "publishTime": "2025-01-15T10:30:00Z"
    }
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "message": "Message received and processed",
  "messageId": "test-123",
  "publishTime": "2025-01-15T10:30:00Z",
  "dataPreview": "Hello from GCP",
  "timestamp": "2025-01-15T10:30:05.123456"
}
```

**Check Lambda logs:**
```bash
aws logs tail /aws/lambda/gcp-pubsub-test --follow
```

---

### Step 4: Configure GCP Pub/Sub

```bash
# Get your webhook URL
WEBHOOK_URL=$(cat webhook_url.txt)

# Create test topic (if doesn't exist)
gcloud pubsub topics create test-topic \
  --project agentic-ai-integration-490716

# Create push subscription to AWS Lambda
gcloud pubsub subscriptions create test-aws-lambda-push \
  --topic test-topic \
  --push-endpoint $WEBHOOK_URL \
  --project agentic-ai-integration-490716
```

**Verify subscription:**
```bash
gcloud pubsub subscriptions describe test-aws-lambda-push \
  --project agentic-ai-integration-490716
```

---

### Step 5: Send Test Message

**Terminal 1: Watch Lambda logs**
```bash
aws logs tail /aws/lambda/gcp-pubsub-test --follow
```

**Terminal 2: Send message from GCP**
```bash
gcloud pubsub topics publish test-topic \
  --message "Hello from GCP Pub/Sub to AWS Lambda!" \
  --project agentic-ai-integration-490716
```

**Expected in Terminal 1 (within 1-2 seconds):**
```
[2025-01-15T10:35:00.123456] === Received event from GCP Pub/Sub ===
Request body parsed successfully
Message extracted successfully
✅ Message Data: Hello from GCP Pub/Sub to AWS Lambda!
📋 Message ID: 1234567890
📅 Publish Time: 2025-01-15T10:35:00.000Z
✅ SUCCESS: Message processed
```

---

## Verification Checklist

```
□ Local tests pass (python test_local.py)
□ Lambda deployed to AWS (./deploy.sh)
□ Webhook URL obtained (cat webhook_url.txt)
□ Curl test returns 200 OK
□ Lambda logs show test message
□ GCP Pub/Sub subscription created
□ GCP test message sent
□ Lambda logs show GCP message
□ GCP metrics show successful push (100%)
□ AWS metrics show successful invocation (100%)
```

---

## Troubleshooting

### Lambda deployment fails

**Error: "Role does not exist"**
```bash
# Check IAM role
aws iam get-role --role-name lambda-gcp-pubsub-role

# If missing, deploy script will create it automatically
# Wait 10 seconds for IAM propagation
```

**Error: "Function already exists"**
```bash
# Delete existing function and redeploy
aws lambda delete-function --function-name gcp-pubsub-test
./deploy.sh
```

### Curl test fails

**Error: "Could not resolve host"**
```bash
# Check webhook URL
cat webhook_url.txt

# Ensure it starts with https://
```

**Error: "403 Forbidden"**
```bash
# Add Lambda permission for API Gateway
aws lambda add-permission \
  --function-name gcp-pubsub-test \
  --statement-id AllowAPIGateway \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com
```

### GCP push fails

**Error: "Push endpoint returned error"**
```bash
# Test Lambda endpoint directly
curl -X POST $(cat webhook_url.txt) \
  -H "Content-Type: application/json" \
  -d '{"message": {"data": "dGVzdA==", "messageId": "123"}}'

# If this works, check GCP subscription configuration
```

**No messages in Lambda logs**
```bash
# Check GCP subscription metrics
gcloud pubsub subscriptions describe test-aws-lambda-push \
  --project agentic-ai-integration-490716

# Check if messages are being published
gcloud pubsub topics list --project agentic-ai-integration-490716
```

---

## Monitoring

### View Lambda Metrics

```bash
# Invocations (last 5 minutes)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=gcp-pubsub-test \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum

# Errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=gcp-pubsub-test \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum
```

### View GCP Metrics

```bash
# In GCP Console
# Go to: Pub/Sub → Subscriptions → test-aws-lambda-push
# Click "Metrics" tab
# Look for:
#   - Push requests (should be > 0)
#   - Push success rate (should be 100%)
```

---

## Load Testing

```bash
# Send 100 messages
for i in {1..100}; do
  gcloud pubsub topics publish test-topic \
    --message "Test message #$i" \
    --project agentic-ai-integration-490716
  echo "Sent message $i"
  sleep 0.1
done

# Check Lambda handled all 100
aws logs filter-pattern /aws/lambda/gcp-pubsub-test --pattern "SUCCESS" --start-time -5m
```

---

## Clean Up

```bash
# Delete GCP subscription
gcloud pubsub subscriptions delete test-aws-lambda-push \
  --project agentic-ai-integration-490716

# Delete GCP topic (if created for test)
gcloud pubsub topics delete test-topic \
  --project agentic-ai-integration-490716

# Delete AWS resources
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='gcp-pubsub-api'].ApiId" --output text)
aws apigatewayv2 delete-api --api-id $API_ID

aws lambda delete-function --function-name gcp-pubsub-test

aws iam detach-role-policy \
  --role-name lambda-gcp-pubsub-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name lambda-gcp-pubsub-role
```

---

## Next Steps

Once POC is working:

1. ✅ **Add Authentication** - Implement OIDC token validation
2. ✅ **Add Multiple Customers** - Create 30 Lambda functions
3. ✅ **Forward to Portal26** - Send logs to OTEL endpoint
4. ✅ **Add Monitoring** - CloudWatch dashboards and alarms
5. ✅ **Production Config** - Environment variables, secrets

See `POC_SETUP_GUIDE.md` for detailed next steps.

---

## Success Criteria

**✅ POC is successful if:**

1. Local tests pass (5/5 tests)
2. Lambda deploys to AWS successfully
3. Curl test returns 200 OK with valid JSON
4. GCP Pub/Sub subscription created
5. Test message from GCP appears in Lambda logs within 2 seconds
6. GCP metrics show 100% push success rate
7. Lambda metrics show 100% invocation success rate
8. No errors in CloudWatch Logs

**🎉 Ready for production implementation!**
