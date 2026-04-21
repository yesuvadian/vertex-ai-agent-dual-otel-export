# GCP Pub/Sub → AWS Lambda - Proof of Concept Setup

## Step-by-Step Guide to Create and Test Integration

---

## Step 1: Create AWS Lambda Function

### 1.1 Create Simple Lambda Function

```python
# lambda_function.py
import json
import base64
from datetime import datetime

def lambda_handler(event, context):
    """
    Simple Lambda function to receive GCP Pub/Sub messages
    """
    print(f"[{datetime.utcnow().isoformat()}] Received event from GCP Pub/Sub")
    print(f"Event: {json.dumps(event, indent=2)}")
    
    try:
        # Parse the request body
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
        
        # Extract Pub/Sub message
        if 'message' in body:
            message = body['message']
            
            # Decode the message data
            if 'data' in message:
                message_data = base64.b64decode(message['data']).decode('utf-8')
                print(f"Message Data: {message_data}")
            
            # Extract message attributes
            if 'attributes' in message:
                print(f"Attributes: {message['attributes']}")
            
            # Extract message ID
            if 'messageId' in message:
                print(f"Message ID: {message['messageId']}")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'status': 'success',
                    'message': 'Message received from GCP Pub/Sub',
                    'messageId': message.get('messageId', 'unknown')
                })
            }
        else:
            print("No 'message' field found in body")
            return {
                'statusCode': 400,
                'body': json.dumps({'status': 'error', 'message': 'Invalid message format'})
            }
            
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
```

### 1.2 Deploy Lambda via AWS Console

**Option A: AWS Console (Web UI)**

1. Go to AWS Console → Lambda → Create function
2. Function name: `gcp-pubsub-test`
3. Runtime: Python 3.11
4. Architecture: x86_64
5. Click "Create function"
6. Copy the code above into the inline editor
7. Click "Deploy"
8. Note the Lambda ARN (you'll need this later)

**Option B: AWS CLI**

```bash
# Create lambda_function.py with the code above, then:

# Zip the function
zip function.zip lambda_function.py

# Create Lambda function
aws lambda create-function \
  --function-name gcp-pubsub-test \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --region us-east-1

# Note: You need to create the IAM role first or use an existing one
```

---

## Step 2: Create API Gateway to Expose Lambda

### 2.1 Create HTTP API (Simplest)

**AWS Console:**

1. Go to API Gateway → Create API
2. Choose "HTTP API" → Build
3. Add integration:
   - Integration type: Lambda
   - Lambda function: `gcp-pubsub-test`
   - Version: 2.0
4. API name: `gcp-pubsub-api`
5. Next → Configure routes:
   - Method: POST
   - Resource path: `/webhook`
6. Stage: `$default` (auto-deploy)
7. Review and Create
8. **Copy the Invoke URL** (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com`)

**AWS CLI:**

```bash
# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name gcp-pubsub-test --query 'Configuration.FunctionArn' --output text)

# Create HTTP API
API_ID=$(aws apigatewayv2 create-api \
  --name gcp-pubsub-api \
  --protocol-type HTTP \
  --target $LAMBDA_ARN \
  --query 'ApiId' \
  --output text)

# Get API endpoint
API_ENDPOINT=$(aws apigatewayv2 get-api --api-id $API_ID --query 'ApiEndpoint' --output text)

echo "API Endpoint: $API_ENDPOINT"
```

**Your endpoint will be:**
```
https://abc123.execute-api.us-east-1.amazonaws.com/webhook
```

---

## Step 3: Test Lambda Locally First

Before connecting GCP, test the Lambda works:

```bash
# Test with curl
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "data": "SGVsbG8gZnJvbSBHQ1A=",
      "messageId": "test-123",
      "publishTime": "2025-01-15T10:30:00Z"
    }
  }'

# Expected response:
# {
#   "status": "success",
#   "message": "Message received from GCP Pub/Sub",
#   "messageId": "test-123"
# }
```

**Check Lambda Logs:**

```bash
# View recent logs
aws logs tail /aws/lambda/gcp-pubsub-test --follow

# You should see:
# [2025-01-15T10:30:00] Received event from GCP Pub/Sub
# Message Data: Hello from GCP
# Message ID: test-123
```

---

## Step 4: Configure GCP Pub/Sub

### 4.1 Get Your GCP Project ID

```bash
gcloud config get-value project
# Output: agentic-ai-integration-490716
```

### 4.2 Create Test Topic (if not exists)

```bash
# Check if topic exists
gcloud pubsub topics list

# If vertex-telemetry-topic doesn't exist, create it:
gcloud pubsub topics create test-topic --project agentic-ai-integration-490716
```

### 4.3 Create Push Subscription to AWS Lambda

**Important:** For this POC, we'll use **no authentication** to verify the basic flow works. We'll add authentication in the next step.

```bash
# Create push subscription
gcloud pubsub subscriptions create test-aws-lambda-push \
  --topic test-topic \
  --push-endpoint https://abc123.execute-api.us-east-1.amazonaws.com/webhook \
  --project agentic-ai-integration-490716

# Verify subscription created
gcloud pubsub subscriptions describe test-aws-lambda-push \
  --project agentic-ai-integration-490716
```

**Expected Output:**
```yaml
ackDeadlineSeconds: 10
expirationPolicy:
  ttl: 2678400s
messageRetentionDuration: 604800s
name: projects/agentic-ai-integration-490716/subscriptions/test-aws-lambda-push
pushConfig:
  pushEndpoint: https://abc123.execute-api.us-east-1.amazonaws.com/webhook
topic: projects/agentic-ai-integration-490716/topics/test-topic
```

---

## Step 5: Test the Integration

### 5.1 Publish Test Message from GCP

```bash
# Publish a test message
gcloud pubsub topics publish test-topic \
  --message "Hello from GCP Pub/Sub to AWS Lambda!" \
  --project agentic-ai-integration-490716

# You should see:
# messageIds:
# - '1234567890'
```

### 5.2 Check AWS Lambda Logs

```bash
# In a separate terminal, watch Lambda logs
aws logs tail /aws/lambda/gcp-pubsub-test --follow

# You should see (within 1-2 seconds):
# [2025-01-15T10:35:00] Received event from GCP Pub/Sub
# Event: {
#   "body": "{\"message\": {\"data\": \"SGVsbG8gZnJvbSBHQ1AgUHViL1N1YiB0byBBV1MgTGFtYmRhIQ==\", \"messageId\": \"1234567890\", ...}}",
#   "headers": {...}
# }
# Message Data: Hello from GCP Pub/Sub to AWS Lambda!
# Message ID: 1234567890
```

### 5.3 Verify in GCP Pub/Sub Metrics

```bash
# Check subscription metrics
gcloud pubsub subscriptions describe test-aws-lambda-push \
  --project agentic-ai-integration-490716

# Check for successful deliveries in GCP Console:
# Go to: Cloud Console → Pub/Sub → Subscriptions → test-aws-lambda-push
# Look at: "Push requests" and "Push success rate" graphs
```

---

## Step 6: Verify Success

### ✅ Integration is Working If:

1. **GCP Pub/Sub shows successful pushes**
   - Go to GCP Console → Pub/Sub → Subscriptions → test-aws-lambda-push
   - Metrics tab shows "Push requests" > 0
   - "Push success rate" = 100%

2. **AWS Lambda shows invocations**
   - Go to AWS Console → Lambda → gcp-pubsub-test
   - Monitor tab shows invocations
   - Success rate = 100%
   - No errors

3. **CloudWatch Logs show message content**
   - Lambda logs show decoded message: "Hello from GCP Pub/Sub to AWS Lambda!"
   - Message ID is logged
   - No errors in logs

### ❌ Troubleshooting

**Problem: No logs in Lambda**

```bash
# Check Lambda permissions
aws lambda get-policy --function-name gcp-pubsub-test

# Lambda needs permission for API Gateway to invoke it
aws lambda add-permission \
  --function-name gcp-pubsub-test \
  --statement-id AllowAPIGateway \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com
```

**Problem: GCP shows "Push endpoint returned error"**

```bash
# Test the endpoint manually
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"data": "dGVzdA==", "messageId": "123"}}'

# If this fails, check API Gateway configuration
```

**Problem: Lambda receives request but crashes**

```bash
# Check CloudWatch Logs for error details
aws logs tail /aws/lambda/gcp-pubsub-test --follow

# Common issues:
# - JSON parsing error (check message format)
# - Missing fields in event (check API Gateway integration)
```

---

## Step 7: Load Test (Optional)

### Send Multiple Messages

```bash
# Send 10 messages
for i in {1..10}; do
  gcloud pubsub topics publish test-topic \
    --message "Test message #$i" \
    --project agentic-ai-integration-490716
  echo "Sent message $i"
  sleep 0.5
done

# Check Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=gcp-pubsub-test \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum

# Should show 10 invocations
```

---

## Step 8: Clean Up (After Testing)

```bash
# Delete GCP Pub/Sub subscription
gcloud pubsub subscriptions delete test-aws-lambda-push \
  --project agentic-ai-integration-490716

# Delete GCP topic (optional, if you created test-topic)
gcloud pubsub topics delete test-topic \
  --project agentic-ai-integration-490716

# Delete AWS API Gateway
aws apigatewayv2 delete-api --api-id $API_ID

# Delete AWS Lambda
aws lambda delete-function --function-name gcp-pubsub-test
```

---

## Success Criteria

**✅ You're ready to proceed if:**

1. ✅ Lambda function created and deployed
2. ✅ API Gateway exposes Lambda via HTTPS endpoint
3. ✅ GCP Pub/Sub push subscription configured
4. ✅ Test message sent from GCP appears in Lambda logs
5. ✅ GCP shows 100% push success rate
6. ✅ Lambda shows 100% success rate
7. ✅ No errors in CloudWatch Logs

**🎉 Integration Working! Next Steps:**

Once this POC works, we can add:
1. OIDC authentication (secure the endpoint)
2. Multiple customers (30 Lambda functions)
3. Portal26 forwarding (send to OTEL endpoint)
4. Monitoring and alerting
5. Production configuration

---

## Quick Checklist

```
□ AWS Lambda created (gcp-pubsub-test)
□ API Gateway created with POST /webhook endpoint
□ Lambda endpoint URL obtained (https://...execute-api...)
□ Lambda tested with curl (returns 200 OK)
□ GCP Pub/Sub subscription created (test-aws-lambda-push)
□ Test message published to GCP topic
□ Lambda logs show received message
□ GCP metrics show successful push
□ AWS metrics show successful invocation
□ No errors in CloudWatch Logs
```

**Ready to proceed?** Once all checkboxes are ✅, we can build the production architecture!
