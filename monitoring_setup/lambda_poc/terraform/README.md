# Terraform Infrastructure - GCP to AWS Observability

## 📋 **Overview**

This Terraform configuration deploys a complete cross-cloud observability infrastructure that:
1. Captures logs from GCP Vertex AI Reasoning Engines
2. Forwards logs to AWS Lambda via Pub/Sub
3. Authenticates using shared secrets
4. Routes data to Portal26 (OTEL/S3/Kinesis) based on customer and size

---

## 🏗️ **Infrastructure Components**

### GCP Side
- **Log Sink**: Filters and forwards Reasoning Engine logs
- **Pub/Sub Topic**: Queues messages
- **Pub/Sub Subscription**: Push subscription with shared secret in attributes
- **Service Account**: For token generation
- **Secret Manager**: Stores shared secret

### AWS Side
- **Lambda Function**: Multi-customer log processor
- **Lambda Function URL**: Public endpoint for Pub/Sub
- **IAM Role**: Lambda execution role with required permissions
- **S3 Buckets**: Per-customer trace storage
- **Kinesis Streams**: Per-customer real-time streaming
- **Secrets Manager**: Stores shared secret
- **CloudWatch Logs**: Lambda execution logs

---

## 🚀 **Quick Start**

### Prerequisites

1. **Tools Installed:**
   ```bash
   terraform --version  # >= 1.0
   gcloud --version
   aws --version
   ```

2. **GCP Authentication:**
   ```bash
   gcloud auth application-default login
   # OR
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
   ```

3. **AWS Authentication:**
   ```bash
   aws configure
   # OR
   export AWS_ACCESS_KEY_ID="..."
   export AWS_SECRET_ACCESS_KEY="..."
   ```

4. **Permissions:** See `TERRAFORM_PERMISSIONS.md`

### Step-by-Step Deployment

#### 1. Clone and Configure

```bash
# Navigate to terraform directory
cd terraform/

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

#### 2. Update Configuration

Edit `terraform.tfvars`:

```hcl
gcp_project_id = "your-gcp-project-id"
gcp_region     = "us-central1"
aws_region     = "us-east-1"

reasoning_engine_ids = [
  "your-engine-id-1",
  "your-engine-id-2"
]

portal26_endpoints = {
  "customer1" = {
    otel_endpoint  = "https://customer1.portal26.com/v1/traces"
    s3_bucket      = "unique-bucket-name-customer1"
    kinesis_stream = "customer1-stream"
    customer_id    = "cust-001"
  }
}
```

#### 3. Package Lambda Code

```bash
# Create Lambda deployment package
cd ..  # Go to parent directory
zip -r terraform/lambda_package.zip lambda_multi_customer.py

# OR if you have dependencies
pip install -r requirements.txt -t package/
cd package/
zip -r ../terraform/lambda_package.zip .
cd ..
zip -g terraform/lambda_package.zip lambda_multi_customer.py
```

#### 4. Initialize Terraform

```bash
cd terraform/
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
- Finding hashicorp/aws versions matching "~> 5.0"...
Terraform has been successfully initialized!
```

#### 5. Plan (Dry Run)

```bash
terraform plan
```

Review the plan:
- Resources to be created
- No unexpected deletions
- Correct configuration values

#### 6. Apply

```bash
terraform apply
```

Type `yes` when prompted.

Deployment time: ~5-10 minutes

#### 7. Verify Deployment

```bash
# Check outputs
terraform output

# Test Lambda
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  --payload '{"test": "message"}' \
  response.json

# Check Lambda logs
aws logs tail /aws/lambda/$(terraform output -raw lambda_function_name) --follow
```

---

## 🔧 **Configuration**

### Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `gcp_project_id` | GCP Project ID | Yes | - |
| `gcp_region` | GCP Region | No | `us-central1` |
| `aws_region` | AWS Region | No | `us-east-1` |
| `reasoning_engine_ids` | List of Reasoning Engine IDs | Yes | - |
| `portal26_endpoints` | Portal26 endpoints per customer | Yes | - |
| `lambda_function_name` | Lambda function name | No | `gcp-pubsub-multi-customer-processor` |
| `environment` | Environment name | No | `production` |

### Portal26 Endpoints Structure

```hcl
portal26_endpoints = {
  "customer_identifier" = {
    otel_endpoint  = "https://customer.portal26.com/v1/traces"
    s3_bucket      = "unique-bucket-name"
    kinesis_stream = "stream-name"
    customer_id    = "customer-id"
  }
}
```

---

## 🔐 **Security**

### Shared Secret Authentication

The infrastructure uses **shared secrets** for authentication:

1. **Generation**: Terraform generates a 64-character random secret
2. **Storage**:
   - GCP: Secret Manager
   - AWS: Secrets Manager
3. **Usage**:
   - GCP Pub/Sub includes secret in message attributes
   - AWS Lambda verifies secret against Secrets Manager

### Accessing Secrets

#### View Secret (AWS)
```bash
aws secretsmanager get-secret-value \
  --secret-id gcp-pubsub-shared-secret \
  --query SecretString \
  --output text | jq .
```

#### View Secret (GCP)
```bash
gcloud secrets versions access latest \
  --secret="aws-lambda-shared-secret" \
  --project=PROJECT_ID
```

### Rotating Secrets

```bash
# Update Terraform variable (or regenerate random_password resource)
terraform apply -replace="random_password.shared_secret"

# This will:
# - Generate new secret
# - Update AWS Secrets Manager
# - Update GCP Secret Manager
# - Pub/Sub will automatically use new secret
```

---

## 📊 **Monitoring**

### Lambda Monitoring

```bash
# View recent invocations
aws lambda get-function \
  --function-name gcp-pubsub-multi-customer-processor

# View logs
aws logs tail /aws/lambda/gcp-pubsub-multi-customer-processor --follow

# View metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=gcp-pubsub-multi-customer-processor \
  --start-time 2024-04-23T00:00:00Z \
  --end-time 2024-04-23T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### GCP Monitoring

```bash
# Check Pub/Sub metrics
gcloud pubsub topics list
gcloud pubsub subscriptions list

# View Log Sink status
gcloud logging sinks describe reasoning-engine-to-pubsub
```

---

## 🧪 **Testing**

### End-to-End Test

```bash
# 1. Publish test message to Pub/Sub
gcloud pubsub topics publish reasoning-engine-logs-topic \
  --message='{"test": "message"}' \
  --attribute=shared_secret=$(terraform output -raw shared_secret_value),customer_id=customer1

# 2. Wait 10 seconds

# 3. Check Lambda logs
aws logs tail /aws/lambda/gcp-pubsub-multi-customer-processor --since 1m

# Expected output:
# [OK] Shared secret verified
# [INFO] Customer identified: customer1
# [OTEL] Status: 200
```

### Test Lambda Directly

```bash
# Create test payload
cat > test_payload.json <<EOF
{
  "message": {
    "data": "eyJ0ZXN0IjogIm1lc3NhZ2UifQ==",
    "attributes": {
      "shared_secret": "YOUR_SHARED_SECRET",
      "customer_id": "customer1"
    },
    "messageId": "test-123"
  }
}
EOF

# Invoke Lambda
aws lambda invoke \
  --function-name gcp-pubsub-multi-customer-processor \
  --payload file://test_payload.json \
  output.json

# Check response
cat output.json
```

---

## 🔄 **Updates and Changes**

### Add New Customer

1. Update `terraform.tfvars`:
```hcl
portal26_endpoints = {
  # ... existing customers ...
  "new_customer" = {
    otel_endpoint  = "https://newcustomer.portal26.com/v1/traces"
    s3_bucket      = "portal26-newcustomer-traces"
    kinesis_stream = "portal26-newcustomer-stream"
    customer_id    = "cust-003"
  }
}
```

2. Apply changes:
```bash
terraform apply
```

### Add New Reasoning Engine

1. Update `terraform.tfvars`:
```hcl
reasoning_engine_ids = [
  "existing-id-1",
  "existing-id-2",
  "new-engine-id-3"  # Add new ID
]
```

2. Apply:
```bash
terraform apply
```

### Update Lambda Code

1. Modify `lambda_multi_customer.py`
2. Repackage:
```bash
zip -r terraform/lambda_package.zip lambda_multi_customer.py
```
3. Apply:
```bash
terraform apply
```

---

## 🗑️ **Cleanup**

### Destroy All Resources

```bash
terraform destroy
```

**WARNING**: This will delete:
- All S3 buckets (and data in them)
- All Kinesis streams
- Lambda function
- Pub/Sub topic and subscription
- Log Sink
- Secrets

### Selective Destroy

```bash
# Destroy only specific resource
terraform destroy -target=aws_lambda_function.multi_customer_processor

# Destroy only AWS resources
terraform destroy \
  -target=aws_lambda_function.multi_customer_processor \
  -target=aws_s3_bucket.customer_traces \
  -target=aws_kinesis_stream.customer_streams
```

---

## 🐛 **Troubleshooting**

### Issue: "Permission denied" errors

**Solution**: Check `TERRAFORM_PERMISSIONS.md` and verify all permissions are granted

### Issue: Lambda package too large

**Solution**: Use Lambda layers for dependencies
```bash
# Create layer
pip install requests -t python/
zip -r requests_layer.zip python/

# Upload layer
aws lambda publish-layer-version \
  --layer-name requests \
  --zip-file fileb://requests_layer.zip \
  --compatible-runtimes python3.11
```

### Issue: Pub/Sub subscription not receiving messages

**Check:**
```bash
# Verify Log Sink filter
gcloud logging sinks describe reasoning-engine-to-pubsub

# Check if logs match filter
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine"' --limit=5

# Check Pub/Sub metrics
gcloud pubsub topics describe reasoning-engine-logs-topic
```

### Issue: Lambda authentication failing

**Check:**
```bash
# Verify shared secret in AWS
aws secretsmanager get-secret-value --secret-id gcp-pubsub-shared-secret

# Verify shared secret in GCP
gcloud secrets versions access latest --secret="aws-lambda-shared-secret"

# Check if secrets match
```

---

## 📚 **Additional Resources**

- **Terraform Documentation**: https://www.terraform.io/docs
- **GCP Pub/Sub**: https://cloud.google.com/pubsub/docs
- **AWS Lambda**: https://docs.aws.amazon.com/lambda/
- **Portal26 OTEL**: (Your Portal26 documentation link)

---

## 📝 **File Structure**

```
terraform/
├── main.tf                          # Main configuration
├── gcp_agent_logging.tf             # GCP agent logging (automatic)
├── gcp_log_sink_pubsub.tf           # Log Sink and Pub/Sub
├── aws_lambda_multi_customer.tf     # Lambda and AWS resources
├── security_shared_secret.tf        # Shared secret configuration
├── terraform.tfvars.example         # Example variables
├── terraform.tfvars                 # Your actual variables (gitignored)
├── lambda_multi_customer.py         # Lambda function code
├── lambda_package.zip               # Lambda deployment package
├── TERRAFORM_PERMISSIONS.md         # Required permissions guide
└── README.md                        # This file
```

---

**Need Help?** Check the troubleshooting section or review the Terraform output for specific error messages!
