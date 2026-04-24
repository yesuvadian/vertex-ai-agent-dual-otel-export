# Integration with Existing AWS Infrastructure

## 📋 **Overview**

This Terraform configuration integrates **existing Vertex AI agents in GCP** with **existing AWS Lambda or API Gateway endpoints**. It creates the GCP side of the pipeline without duplicating your existing AWS infrastructure.

---

## 🎯 **What This Does**

```
Existing GCP Agents → [NEW] Log Sink → [NEW] Pub/Sub → Existing AWS Endpoint
(already logging)      (Terraform)     (Terraform)     (already deployed)
```

### ✅ **Creates (GCP Side)**
- Log Sink (routes logs from Cloud Logging)
- Pub/Sub Topic (queues messages)
- Pub/Sub Subscription (pushes to your AWS endpoint)
- Service Account (for permissions)
- GCP Secret Manager (stores shared secret)

### ✅ **Creates (AWS Side - Minimal)**
- AWS Secrets Manager (stores same shared secret)
- IAM permissions (if needed)

### ❌ **Does NOT Create**
- Vertex AI agents (you already have them)
- Lambda function (you already have it)
- API Gateway (you already have it)
- S3 buckets
- Kinesis streams

---

## 🔧 **Configuration Options**

### **Option 1: Existing Lambda Function URL**

```hcl
# terraform.tfvars
aws_endpoint_type = "lambda_url"
aws_endpoint_url  = "https://abc123.lambda-url.us-east-1.on.aws/"
existing_lambda_function_name = "your-existing-lambda-name"
```

### **Option 2: Existing API Gateway**

```hcl
# terraform.tfvars
aws_endpoint_type = "api_gateway"
aws_endpoint_url  = "https://abc123.execute-api.us-east-1.amazonaws.com/prod/webhook"
```

### **Option 3: Generic HTTPS Endpoint**

```hcl
# terraform.tfvars
aws_endpoint_type = "https"
aws_endpoint_url  = "https://your-custom-endpoint.com/logs"
```

---

## 📦 **Required Information Checklist**

Before deploying, gather this information:

### **GCP Information**
- [ ] GCP Project ID: `_____________________`
- [ ] GCP Region: `_____________________`
- [ ] Vertex AI Reasoning Engine IDs (comma-separated):
  ```
  - _____________________
  - _____________________
  - _____________________
  ```

### **AWS Information**
- [ ] AWS Region: `_____________________`
- [ ] Endpoint Type: ☐ Lambda URL  ☐ API Gateway  ☐ HTTPS
- [ ] Endpoint URL: `_____________________`
- [ ] Lambda Function Name (if Lambda): `_____________________`

### **Authentication**
- [ ] Does your endpoint expect authentication?
  - ☐ Yes - Shared secret in message attributes
  - ☐ Yes - Shared secret in Authorization header
  - ☐ Yes - AWS IAM signature
  - ☐ No authentication

### **Payload Format**
- [ ] Expected payload format:
  - ☐ Standard Pub/Sub format (base64-encoded message.data)
  - ☐ Custom JSON structure
  - ☐ Raw log data

---

## 🚀 **Quick Start**

### **Step 1: Gather Information**

Fill out the checklist above.

### **Step 2: Configure Variables**

Create `terraform.tfvars`:

```hcl
# ============================================================================
# Integration Configuration - Existing AWS Infrastructure
# ============================================================================

# GCP Configuration
gcp_project_id = "your-gcp-project-id"
gcp_region     = "us-central1"

# Existing Vertex AI Reasoning Engine IDs
reasoning_engine_ids = [
  "8213677864684355584",
  "6010661182900273152"
]

# AWS Configuration
aws_region = "us-east-1"

# Existing AWS Endpoint
aws_endpoint_type = "lambda_url"  # or "api_gateway" or "https"
aws_endpoint_url  = "https://YOUR-LAMBDA-URL.lambda-url.us-east-1.on.aws/"

# If using Lambda, provide function name for IAM updates
existing_lambda_function_name = "your-existing-lambda-name"  # Optional

# Authentication Method
authentication_method = "shared_secret_attribute"  # or "shared_secret_header" or "none"

# Environment
environment = "production"
```

### **Step 3: Deploy**

```bash
cd terraform/

# Initialize
terraform init

# Review changes
terraform plan

# Deploy
terraform apply
```

---

## 🔐 **Authentication Integration**

### **Method 1: Shared Secret in Message Attributes (Recommended)**

**Why**: GCP Pub/Sub doesn't support custom HTTP headers, so attributes are the best option.

**Pub/Sub Configuration:**
```hcl
resource "google_pubsub_subscription" "reasoning_engine_to_existing" {
  push_config {
    push_endpoint = var.aws_endpoint_url
    
    attributes = {
      shared_secret = google_secret_manager_secret_version.aws_shared_secret_value.secret_data
      customer_id   = "your-customer-id"
    }
  }
}
```

**Your Lambda Must Extract Secret:**
```python
def lambda_handler(event, context):
    # Extract from Pub/Sub message attributes
    attributes = event.get('message', {}).get('attributes', {})
    provided_secret = attributes.get('shared_secret')
    
    # Verify against AWS Secrets Manager
    expected_secret = get_secret_from_aws_secrets_manager()
    
    if provided_secret != expected_secret:
        return {'statusCode': 403, 'body': 'Forbidden'}
    
    # Process message...
```

### **Method 2: No Authentication (Testing Only)**

```hcl
resource "google_pubsub_subscription" "reasoning_engine_to_existing" {
  push_config {
    push_endpoint = var.aws_endpoint_url
    # No authentication
  }
}
```

---

## 📤 **Payload Format from Pub/Sub**

Your existing Lambda/API Gateway will receive this format:

```json
{
  "message": {
    "data": "eyJsb2dOYW1lIjoicHJvamVjdHMvLi4uIiwgInRleHRQYXlsb2FkIjoiLi4uIn0=",
    "messageId": "1234567890",
    "publishTime": "2024-04-23T10:30:00.123Z",
    "attributes": {
      "shared_secret": "your-64-char-secret",
      "customer_id": "your-customer-id"
    }
  },
  "subscription": "projects/PROJECT/subscriptions/reasoning-engine-to-existing"
}
```

**Decoding the Data:**

```python
import json
import base64

def lambda_handler(event, context):
    # Extract base64-encoded log data
    encoded_data = event['message']['data']
    
    # Decode
    decoded_data = base64.b64decode(encoded_data).decode('utf-8')
    log_entry = json.loads(decoded_data)
    
    # log_entry now contains the original Cloud Logging entry
    print(f"Log: {log_entry.get('textPayload')}")
    print(f"Timestamp: {log_entry.get('timestamp')}")
```

---

## 🔄 **Lambda Code Updates**

### **Minimal Changes Required**

If your Lambda already processes logs, you only need to add:

1. **Pub/Sub message unwrapping**
2. **Shared secret verification** (optional but recommended)

```python
import json
import base64
import boto3

secrets_client = boto3.client('secretsmanager')

def lambda_handler(event, context):
    """
    Modified to handle Pub/Sub push format
    """
    try:
        # === NEW: Unwrap Pub/Sub message ===
        message = event.get('message', {})
        attributes = message.get('attributes', {})
        
        # === NEW: Verify shared secret ===
        if not verify_shared_secret(attributes.get('shared_secret')):
            return {'statusCode': 403, 'body': 'Forbidden'}
        
        # === NEW: Decode log data ===
        encoded_data = message.get('data', '')
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        log_entry = json.loads(decoded_data)
        
        # === EXISTING: Your processing logic ===
        process_log_entry(log_entry)  # Your existing function
        
        return {'statusCode': 200, 'body': 'Success'}
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}

def verify_shared_secret(provided_secret):
    """
    NEW: Verify shared secret from Pub/Sub
    """
    if not provided_secret:
        return False
    
    try:
        response = secrets_client.get_secret_value(
            SecretId='gcp-pubsub-shared-secret'
        )
        secret_data = json.loads(response['SecretString'])
        expected_secret = secret_data.get('secret_key')
        
        # Constant-time comparison
        return secrets_compare(provided_secret, expected_secret)
    except Exception as e:
        print(f"Secret verification error: {str(e)}")
        return False

def secrets_compare(a, b):
    """Constant-time string comparison"""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0

def process_log_entry(log_entry):
    """
    EXISTING: Your current log processing logic
    No changes needed here
    """
    # Your existing code...
    pass
```

### **API Gateway Alternative**

If using API Gateway, it transforms the payload differently:

```python
def lambda_handler(event, context):
    """
    API Gateway format (different from Lambda URL)
    """
    # API Gateway wraps in body
    body = json.loads(event.get('body', '{}'))
    message = body.get('message', {})
    
    # Rest is the same...
```

---

## 📋 **Deployment Checklist**

### **Before Deployment**

- [ ] Existing AWS endpoint is accessible and working
- [ ] You have AWS credentials configured (`aws configure`)
- [ ] You have GCP credentials configured (`gcloud auth login`)
- [ ] `terraform.tfvars` is filled out correctly
- [ ] Reasoning Engine IDs are correct

### **During Deployment**

- [ ] Run `terraform init` successfully
- [ ] Run `terraform plan` and review changes
- [ ] Run `terraform apply` and type `yes`
- [ ] Wait ~5-10 minutes for deployment
- [ ] Note the outputs (shared secret, Pub/Sub topic name)

### **After Deployment**

- [ ] Test with manual Pub/Sub publish (see Testing section below)
- [ ] Check your Lambda CloudWatch logs for incoming messages
- [ ] Verify shared secret is accessible in AWS Secrets Manager
- [ ] Monitor for 24 hours to ensure stability

---

## 🧪 **Testing**

### **Test 1: Manual Pub/Sub Publish**

```bash
# Get shared secret
export SHARED_SECRET=$(terraform output -raw shared_secret_value)

# Publish test message
gcloud pubsub topics publish reasoning-engine-logs-topic \
  --message='{"test": "message", "timestamp": "2024-04-23T10:30:00Z"}' \
  --attribute=shared_secret=$SHARED_SECRET,customer_id=test

# Wait 5 seconds, then check your Lambda logs
aws logs tail /aws/lambda/your-existing-lambda-name --since 1m --follow
```

### **Test 2: Trigger Agent Log**

```bash
# Trigger an action in your Vertex AI Reasoning Engine
# (This depends on your agent implementation)

# Wait 10 seconds for log to flow through pipeline

# Check Lambda received it
aws logs tail /aws/lambda/your-existing-lambda-name --since 1m
```

### **Test 3: Verify Secret Storage**

```bash
# Verify secret in AWS
aws secretsmanager get-secret-value \
  --secret-id gcp-pubsub-shared-secret \
  --query SecretString \
  --output text | jq .

# Verify secret in GCP
gcloud secrets versions access latest \
  --secret="aws-lambda-shared-secret" \
  --project=YOUR_PROJECT_ID
```

---

## 🐛 **Troubleshooting**

### **Issue: Lambda Not Receiving Messages**

```bash
# Check Pub/Sub subscription status
gcloud pubsub subscriptions describe reasoning-engine-to-existing

# Check for delivery errors
gcloud pubsub subscriptions pull reasoning-engine-to-existing --limit=5

# Verify endpoint URL is correct
terraform output aws_endpoint_url
```

### **Issue: Authentication Failing**

```bash
# Verify secrets match
aws secretsmanager get-secret-value --secret-id gcp-pubsub-shared-secret
gcloud secrets versions access latest --secret=aws-lambda-shared-secret

# Check Lambda environment variables
aws lambda get-function-configuration \
  --function-name your-existing-lambda-name \
  --query Environment
```

### **Issue: Log Sink Not Capturing Logs**

```bash
# Verify Log Sink filter
gcloud logging sinks describe reasoning-engine-to-pubsub

# Test if logs match filter
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine"' --limit=5

# Check if Reasoning Engine IDs are correct
gcloud ai reasoning-engines list --region=us-central1
```

---

## 🔄 **Update Existing Lambda Permissions**

Terraform will create the shared secret in AWS Secrets Manager. Your existing Lambda needs permission to read it:

```bash
# Add permission manually (or Terraform can do this)
aws lambda add-permission \
  --function-name your-existing-lambda-name \
  --statement-id AllowSecretsManagerAccess \
  --action secretsmanager:GetSecretValue \
  --principal secretsmanager.amazonaws.com

# Or attach policy to Lambda execution role
aws iam attach-role-policy \
  --role-name your-lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

---

## 📊 **Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD PLATFORM                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────┐                 │
│  │  Existing Vertex AI Reasoning Engines  │                 │
│  │  (NOT created by Terraform)            │                 │
│  │  • Agent 1: 8213677864684355584        │                 │
│  │  • Agent 2: 6010661182900273152        │                 │
│  └────────────────┬───────────────────────┘                 │
│                   │ Auto-logs                               │
│                   ↓                                          │
│  ┌────────────────────────────────────────┐                 │
│  │  Cloud Logging (GCP Managed)           │                 │
│  └────────────────┬───────────────────────┘                 │
│                   │                                          │
│                   ↓                                          │
│  ╔════════════════════════════════════════╗                 │
│  ║  [NEW] Log Sink                        ║                 │
│  ║  Terraform Creates                     ║                 │
│  ╚════════════════┬═══════════════════════╝                 │
│                   │                                          │
│                   ↓                                          │
│  ╔════════════════════════════════════════╗                 │
│  ║  [NEW] Pub/Sub Topic + Subscription    ║                 │
│  ║  Terraform Creates                     ║                 │
│  ║  • Includes shared secret in attributes║                 │
│  ╚════════════════┬═══════════════════════╝                 │
│                   │                                          │
│  ╔════════════════┴═══════════════════════╗                 │
│  ║  [NEW] GCP Secret Manager              ║                 │
│  ║  Terraform Creates                     ║                 │
│  ╚════════════════════════════════════════╝                 │
│                                                              │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ HTTPS POST
                   │
┌──────────────────┴───────────────────────────────────────────┐
│                    AMAZON WEB SERVICES                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ╔════════════════════════════════════════╗                 │
│  ║  [NEW] AWS Secrets Manager             ║                 │
│  ║  Terraform Creates                     ║                 │
│  ║  • Stores same shared secret           ║                 │
│  ╚════════════════┬═══════════════════════╝                 │
│                   │ Reads for verification                   │
│                   ↓                                          │
│  ┌────────────────────────────────────────┐                 │
│  │  Existing Lambda or API Gateway        │                 │
│  │  (NOT created by Terraform)            │                 │
│  │  • Receives Pub/Sub messages           │                 │
│  │  • Verifies shared secret              │                 │
│  │  • Processes logs                      │                 │
│  └────────────────────────────────────────┘                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Legend:
[NEW] = Created by Terraform
Existing = Already deployed (not touched by Terraform)
```

---

## 📝 **Next Steps**

1. Fill out the configuration checklist
2. Create `terraform.tfvars` with your values
3. Review modified Terraform files (see next section)
4. Deploy with `terraform apply`
5. Update your existing Lambda code (if needed)
6. Test end-to-end
7. Monitor for 24 hours

---

**Ready to proceed?** I'll create the modified Terraform files next!
