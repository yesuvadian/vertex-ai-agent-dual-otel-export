# One Lambda Per Customer - Complete Architecture

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Customer 1 (GCP Pub/Sub)                                        │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ HTTPS POST
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ API Gateway                                                     │
│ POST /webhook/customer1                                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda-customer1                                                │
│ - Dedicated function for Customer 1                             │
│ - Memory: 512MB                                                 │
│ - Timeout: 60s                                                  │
│ - Env: CUSTOMER_ID=customer1                                    │
│ - Env: PORTAL26_ENDPOINT=https://customer1.portal26.in:4318    │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
       Portal26 OTEL Endpoint 1
       (Dedicated or shared with customer.id)

┌─────────────────────────────────────────────────────────────────┐
│ Customer 2 (GCP Pub/Sub)                                        │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ HTTPS POST
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ API Gateway                                                     │
│ POST /webhook/customer2                                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda-customer2                                                │
│ - Dedicated function for Customer 2                             │
│ - Memory: 256MB (smaller customer)                              │
│ - Timeout: 60s                                                  │
│ - Env: CUSTOMER_ID=customer2                                    │
│ - Env: PORTAL26_ENDPOINT=https://customer2.portal26.in:4318    │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
       Portal26 OTEL Endpoint 2
       (Dedicated or shared with customer.id)

┌─────────────────────────────────────────────────────────────────┐
│ Customer 3 (GCP Pub/Sub)                                        │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ HTTPS POST
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ API Gateway                                                     │
│ POST /webhook/customer3                                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Lambda-customer3                                                │
│ - Dedicated function for Customer 3                             │
│ - Memory: 1024MB (enterprise customer)                          │
│ - Timeout: 120s                                                 │
│ - Env: CUSTOMER_ID=customer3                                    │
│ - Env: PORTAL26_ENDPOINT=https://customer3.portal26.in:4318    │
│ - Reserved Concurrency: 200                                     │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
       Portal26 OTEL Endpoint 3
       (Dedicated or shared with customer.id)
```

**Key Characteristics:**
- ✅ One AWS Lambda function per customer
- ✅ One API Gateway endpoint per customer (`/webhook/customer-id`)
- ✅ Each Lambda has customer-specific configuration
- ✅ Each Lambda can connect to dedicated or shared Portal26 endpoint
- ✅ Complete isolation between customers

---

## Portal26 Endpoint Options

### Option A: Shared Portal26 Endpoint (Customer Isolation via Attributes)

```
All Lambdas → Same Portal26 Endpoint (https://otel.portal26.in:4318)

Lambda-customer1 → Adds attribute: customer.id = "customer1"
Lambda-customer2 → Adds attribute: customer.id = "customer2"
Lambda-customer3 → Adds attribute: customer.id = "customer3"

Portal26 Query Examples:
- Customer 1 view: WHERE customer.id = "customer1"
- Customer 2 view: WHERE customer.id = "customer2"
```

**Pros:**
- ✅ Single Portal26 deployment
- ✅ Lower Portal26 cost
- ✅ Easier to manage
- ✅ Cross-customer analytics possible

**Cons:**
- ❌ Data commingled (logical isolation only)
- ❌ All customers see same Portal26 URL in Lambda config
- ❌ Customer A could potentially query Customer B data (if Portal26 security misconfigured)

### Option B: Dedicated Portal26 Endpoint Per Customer

```
Lambda-customer1 → https://customer1.portal26.in:4318 (Dedicated instance)
Lambda-customer2 → https://customer2.portal26.in:4318 (Dedicated instance)
Lambda-customer3 → https://customer3.portal26.in:4318 (Dedicated instance)

Each customer has completely separate Portal26 instance.
```

**Pros:**
- ✅ Complete physical isolation
- ✅ No chance of data leakage between customers
- ✅ Customer-specific Portal26 configuration
- ✅ Can give customer direct Portal26 access
- ✅ Meets strictest compliance requirements

**Cons:**
- ❌ High Portal26 cost (30 instances for 30 customers)
- ❌ 30× Portal26 maintenance overhead
- ❌ No cross-customer analytics
- ❌ Must manage 30 Portal26 deployments

### Recommendation

**Use Shared Portal26 with customer.id attributes for 99% of use cases.**

Only use dedicated Portal26 endpoints if:
- Customer contract requires dedicated infrastructure
- Compliance mandates physical separation (HIPAA, PCI-DSS Level 1)
- Customer pays for dedicated Portal26 ($100-500/month extra)

---

## Security Architecture

### Layer 1: API Gateway Security

```yaml
API Gateway Configuration:

/webhook/customer1:
  Method: POST
  Authorization: CUSTOM (Lambda Authorizer) OR AWS_IAM OR NONE
  Rate Limiting: 1000 req/sec
  Usage Plan: customer1-plan
  API Key: Optional
  IP Allowlist: Optional (customer1's GCP IPs)
  
/webhook/customer2:
  Method: POST
  Authorization: CUSTOM (Lambda Authorizer) OR AWS_IAM OR NONE
  Rate Limiting: 500 req/sec
  Usage Plan: customer2-plan
  API Key: Optional
  IP Allowlist: Optional (customer2's GCP IPs)
  
/webhook/customer3:
  Method: POST
  Authorization: CUSTOM (Lambda Authorizer) OR AWS_IAM OR NONE
  Rate Limiting: 2000 req/sec (enterprise)
  Usage Plan: customer3-plan
  API Key: Optional
  IP Allowlist: Optional (customer3's GCP IPs)
```

**Security Questions:**

#### Do You Need Authentication?

Since each customer has dedicated Lambda and endpoint, there are three approaches:

**Approach 1: No Authentication (Lambda Endpoint = Identity)**
```
Security Model:
- API Gateway route /webhook/customer1 → Lambda-customer1 only
- Customer 1 cannot reach Lambda-customer2 (different route)
- Endpoint URL itself is the security boundary

Acceptable When:
- ✅ API Gateway has IP allowlisting (only customer's GCP IPs)
- ✅ Endpoint URL is not publicly documented
- ✅ Low-medium security requirements
- ✅ Internal use case

Risk:
- ⚠️ Anyone with URL can send data to that customer's endpoint
- ⚠️ Must rely on IP allowlisting for security
- ⚠️ If URL leaks, attacker can inject fake data

Cost: $0 (no authorizer Lambda needed)
```

**Approach 2: OIDC Token Authentication (Recommended)**
```
Security Model:
- Customer's GCP Pub/Sub sends OIDC token in Authorization header
- Lambda Authorizer validates token before allowing request
- Even with dedicated Lambda, validate requests come from customer's GCP

Implementation:
- Lambda Authorizer validates JWT signature
- Checks service account in allowlist
- Ensures service account matches customer

Benefits:
- ✅ Cryptographic proof of origin
- ✅ Cannot forge without Google's private key
- ✅ Audit trail (token includes timestamp)
- ✅ Defense in depth

Cost: +$1.50/month (authorizer Lambda)
```

**Approach 3: API Key (Simple but Less Secure)**
```
Security Model:
- Customer's GCP Pub/Sub sends X-API-Key header
- API Gateway validates key before invoking Lambda
- Simple string comparison

Implementation:
- Generate unique API key per customer
- Configure API Gateway API key
- Customer adds key to Pub/Sub push subscription

Benefits:
- ✅ Simple to implement
- ✅ No Lambda Authorizer needed
- ✅ API Gateway handles validation

Risks:
- ⚠️ Key can leak (logs, Git commits)
- ⚠️ No auto-rotation
- ⚠️ Must manually rotate keys

Cost: +$0.40/month per customer (Secrets Manager storage)
```

### Security Recommendation by Customer Tier

| Customer Tier | Recommended Security | Cost | Complexity |
|--------------|---------------------|------|------------|
| **Small/Internal** | IP Allowlisting only | $0 | Low |
| **Standard SaaS** | OIDC Token | +$1.50/month | Medium |
| **Enterprise** | OIDC + IP Allowlisting | +$1.50/month | Medium |
| **High Security** | mTLS | +$35/month (ALB) | High |

---

## Complete Security Flow

### With OIDC Authentication (Recommended)

```python
"""
Security Flow: GCP Pub/Sub → API Gateway → Authorizer → Lambda → Portal26
"""

# Step 1: Customer's GCP Pub/Sub sends request
"""
POST /webhook/customer1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "message": {
    "data": "base64_encoded_log_entry",
    "messageId": "123456",
    "publishTime": "2025-01-15T10:30:00Z"
  }
}
"""

# Step 2: API Gateway invokes Lambda Authorizer
"""
Lambda Authorizer receives:
{
  "type": "REQUEST",
  "methodArn": "arn:aws:execute-api:us-east-1:123456789012:api-id/prod/POST/webhook/customer1",
  "headers": {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
"""

# Step 3: Lambda Authorizer validates token
def authorizer_handler(event, context):
    """
    Validates OIDC token from GCP Pub/Sub
    """
    # Extract JWT
    token = event['headers']['Authorization'].replace('Bearer ', '')
    
    # Verify signature using Google's public keys
    decoded = verify_jwt_signature(token)  # Cryptographic verification
    
    # Extract service account
    service_account = decoded['email']  # e.g., customer1@project.iam.gserviceaccount.com
    
    # Check allowlist
    CUSTOMER_ALLOWLIST = {
        "customer1@project.iam.gserviceaccount.com": "customer1",
        "customer2@project.iam.gserviceaccount.com": "customer2",
        # ...
    }
    
    if service_account not in CUSTOMER_ALLOWLIST:
        return generate_policy('Deny', event['methodArn'])
    
    customer_id = CUSTOMER_ALLOWLIST[service_account]
    
    # CRITICAL: Verify customer_id matches endpoint
    endpoint_customer = extract_customer_from_arn(event['methodArn'])  # "customer1" from path
    
    if customer_id != endpoint_customer:
        # Customer1's token trying to access customer2's endpoint
        logger.warning(f"Auth violation: {customer_id} tried to access {endpoint_customer}")
        return generate_policy('Deny', event['methodArn'])
    
    # Allow with context
    return generate_policy('Allow', event['methodArn'], {
        'customer_id': customer_id,
        'service_account': service_account
    })

# Step 4: If authorized, API Gateway invokes Lambda-customer1
"""
Lambda-customer1 receives:
{
  "body": "{\"message\": {...}}",
  "requestContext": {
    "authorizer": {
      "customer_id": "customer1",
      "service_account": "customer1@project.iam.gserviceaccount.com"
    }
  }
}
"""

# Step 5: Lambda-customer1 processes message
def lambda_customer1_handler(event, context):
    """
    Dedicated Lambda for Customer 1
    """
    # Extract customer context (already validated by authorizer)
    customer_id = event['requestContext']['authorizer']['customer_id']
    
    # Parse Pub/Sub message
    body = json.loads(event['body'])
    message_data = base64.b64decode(body['message']['data'])
    log_entry = json.loads(message_data)
    
    # Convert to OTEL format
    otel_log = convert_to_otel(log_entry)
    
    # Add customer isolation attribute
    otel_log['attributes'].append({
        "key": "customer.id",
        "value": {"stringValue": customer_id}
    })
    
    # Send to Portal26 (customer-specific endpoint from env var)
    portal26_endpoint = os.environ['PORTAL26_ENDPOINT']
    success = send_to_portal26(otel_log, portal26_endpoint)
    
    return {
        'statusCode': 200 if success else 500,
        'body': json.dumps({'status': 'success' if success else 'error'})
    }
```

---

## Cost Analysis

### Detailed Cost Breakdown (30 customers, 300K requests/month = 10K per customer)

| Service | Configuration | Calculation | Monthly Cost |
|---------|--------------|-------------|--------------|
| **API Gateway** | 30 endpoints | 300K requests × $3.50/million | $1.05 |
| **Lambda Invocations** | 30 functions | 300K × $0.20/million | $0.06 |
| **Lambda Duration** | 30 functions, 500ms avg | 300K × 500ms × $0.0000000167/ms | $2.50 |
| **Lambda Memory** | 30 functions, 512MB avg | 300K × 512MB × 500ms × $0.0000000167 | $2.50 |
| **Lambda Authorizer** (optional) | Shared across customers | 60K invocations (80% cached) × 150ms | $1.50 |
| **CloudWatch Logs** | 30 log groups | 30 × $0.50 | $15.00 |
| **CloudWatch Metrics** | Per-function metrics | 30 functions × custom metrics | $30.00 |
| **CloudWatch Dashboards** | Optional per-customer | 30 × $3 (optional) | $90.00 |
| **Secrets Manager** (optional) | Store customer configs | 30 secrets × $0.40 | $12.00 |
| **TOTAL (Basic)** | Without dashboards | | **$52.61** |
| **TOTAL (Full Monitoring)** | With dashboards | | **$142.61** |

**Cost per Customer:**
- Basic: $1.75/month
- Full Monitoring: $4.75/month

### Cost by Customer Tier

Customers can have different configurations:

| Customer Tier | Requests/Month | Memory | Timeout | Reserved Concurrency | Monthly Cost |
|---------------|----------------|--------|---------|---------------------|--------------|
| **Startup** | 1,000 | 256MB | 30s | None | $0.50 |
| **Small** | 5,000 | 256MB | 60s | None | $1.50 |
| **Medium** | 10,000 | 512MB | 60s | None | $2.50 |
| **Large** | 50,000 | 1024MB | 120s | 100 | $12.00 |
| **Enterprise** | 100,000 | 2048MB | 300s | 200 | $25.00 |

### Cost Scaling Analysis

| Number of Customers | Total Requests/Month | Monthly Cost (Basic) | Monthly Cost (Full) | Cost per Customer |
|---------------------|---------------------|---------------------|---------------------|-------------------|
| 10 | 100K | $20.00 | $50.00 | $2.00 - $5.00 |
| 30 | 300K | $52.61 | $142.61 | $1.75 - $4.75 |
| 50 | 500K | $85.00 | $235.00 | $1.70 - $4.70 |
| 100 | 1M | $165.00 | $465.00 | $1.65 - $4.65 |
| 200 | 2M | $325.00 | $925.00 | $1.63 - $4.63 |

**Cost Analysis:**
- ✅ Cost per customer decreases slightly as you scale (shared services like authorizer)
- ⚠️ CloudWatch monitoring is 60-65% of total cost
- ⚠️ Can reduce cost by using single aggregate dashboard instead of per-customer dashboards

### Cost Comparison vs Other Architectures

| Architecture | 30 Customers Cost | Cost per Customer | CloudWatch Cost |
|--------------|-------------------|-------------------|-----------------|
| **Shared Lambda** | $5.05 | $0.17 | $1.00 |
| **One Lambda per Customer (Basic)** | $52.61 | $1.75 | $15.00 |
| **One Lambda per Customer (Full)** | $142.61 | $4.75 | $105.00 |
| **ECS Fargate Containers** | $200.00 | $6.67 | $15.00 |

**Key Insight:** One Lambda per customer is 10× more expensive than shared Lambda, but 30% cheaper than ECS containers.

---

## Deployment Architecture

### Infrastructure as Code (Terraform)

```hcl
# variables.tf
variable "customers" {
  description = "List of customers with configurations"
  type = map(object({
    memory              = number
    timeout             = number
    reserved_concurrency = number
    rate_limit          = number
    portal26_endpoint   = string
  }))
  
  default = {
    customer1 = {
      memory              = 512
      timeout             = 60
      reserved_concurrency = 0
      rate_limit          = 1000
      portal26_endpoint   = "https://otel.portal26.in:4318"
    }
    customer2 = {
      memory              = 256
      timeout             = 60
      reserved_concurrency = 0
      rate_limit          = 500
      portal26_endpoint   = "https://otel.portal26.in:4318"
    }
    customer3 = {
      memory              = 1024
      timeout             = 120
      reserved_concurrency = 200
      rate_limit          = 2000
      portal26_endpoint   = "https://customer3.portal26.in:4318"  # Dedicated endpoint
    }
  }
}

# api_gateway.tf
resource "aws_api_gateway_rest_api" "webhook" {
  name = "customer-webhook-api"
}

resource "aws_api_gateway_resource" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  parent_id   = aws_api_gateway_rest_api.webhook.root_resource_id
  path_part   = "webhook"
}

# Create API Gateway resource per customer
resource "aws_api_gateway_resource" "customer" {
  for_each = var.customers
  
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  parent_id   = aws_api_gateway_resource.webhook.id
  path_part   = each.key  # "customer1", "customer2", etc.
}

# Create POST method per customer
resource "aws_api_gateway_method" "customer_post" {
  for_each = var.customers
  
  rest_api_id   = aws_api_gateway_rest_api.webhook.id
  resource_id   = aws_api_gateway_resource.customer[each.key].id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.oidc.id
}

# Lambda Authorizer (shared across all customers)
resource "aws_lambda_function" "authorizer" {
  function_name = "webhook-authorizer"
  role         = aws_iam_role.authorizer.arn
  handler      = "authorizer.lambda_handler"
  runtime      = "python3.11"
  timeout      = 30
  memory_size  = 512
  
  filename         = "authorizer.zip"
  source_code_hash = filebase64sha256("authorizer.zip")
  
  environment {
    variables = {
      CUSTOMER_ALLOWLIST = jsonencode({
        "customer1@project.iam.gserviceaccount.com" = "customer1"
        "customer2@project.iam.gserviceaccount.com" = "customer2"
        "customer3@project.iam.gserviceaccount.com" = "customer3"
      })
    }
  }
}

resource "aws_api_gateway_authorizer" "oidc" {
  name                   = "oidc-authorizer"
  rest_api_id           = aws_api_gateway_rest_api.webhook.id
  authorizer_uri        = aws_lambda_function.authorizer.invoke_arn
  authorizer_credentials = aws_iam_role.authorizer_invocation.arn
  type                  = "REQUEST"
  identity_source       = "method.request.header.Authorization"
  authorizer_result_ttl_in_seconds = 300  # Cache for 5 minutes
}

# Lambda functions (one per customer)
resource "aws_lambda_function" "customer_webhook" {
  for_each = var.customers
  
  function_name = "webhook-${each.key}"
  role         = aws_iam_role.lambda[each.key].arn
  handler      = "handler.lambda_handler"
  runtime      = "python3.11"
  timeout      = each.value.timeout
  memory_size  = each.value.memory
  
  filename         = "handler.zip"
  source_code_hash = filebase64sha256("handler.zip")
  
  # Customer-specific environment variables
  environment {
    variables = {
      CUSTOMER_ID       = each.key
      PORTAL26_ENDPOINT = each.value.portal26_endpoint
      OTEL_SERVICE_NAME = "gcp-vertex-monitor-${each.key}"
      TENANT_ID         = "tenant1"
    }
  }
  
  # Reserved concurrency (if specified)
  reserved_concurrent_executions = each.value.reserved_concurrency > 0 ? each.value.reserved_concurrency : null
}

# API Gateway integration per customer
resource "aws_api_gateway_integration" "customer" {
  for_each = var.customers
  
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  resource_id = aws_api_gateway_resource.customer[each.key].id
  http_method = aws_api_gateway_method.customer_post[each.key].http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.customer_webhook[each.key].invoke_arn
}

# Lambda invoke permission per customer
resource "aws_lambda_permission" "api_gateway" {
  for_each = var.customers
  
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.customer_webhook[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.webhook.execution_arn}/*/*"
}

# Usage Plan per customer (for rate limiting)
resource "aws_api_gateway_usage_plan" "customer" {
  for_each = var.customers
  
  name = "${each.key}-usage-plan"
  
  api_stages {
    api_id = aws_api_gateway_rest_api.webhook.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }
  
  throttle_settings {
    rate_limit  = each.value.rate_limit
    burst_limit = each.value.rate_limit * 2
  }
}

# CloudWatch Log Group per customer
resource "aws_cloudwatch_log_group" "customer" {
  for_each = var.customers
  
  name              = "/aws/lambda/webhook-${each.key}"
  retention_in_days = 30
}

# Optional: CloudWatch Dashboard per customer
resource "aws_cloudwatch_dashboard" "customer" {
  for_each = var.customers
  
  dashboard_name = "webhook-${each.key}"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", { stat = "Sum", label = "Invocations" }],
            [".", "Errors", { stat = "Sum", label = "Errors" }],
            [".", "Duration", { stat = "Average", label = "Avg Duration" }],
            [".", "Throttles", { stat = "Sum", label = "Throttles" }]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
          title  = "Lambda Metrics - ${each.key}"
          dimensions = {
            FunctionName = ["webhook-${each.key}"]
          }
        }
      }
    ]
  })
}

# IAM Role per customer (for fine-grained permissions)
resource "aws_iam_role" "lambda" {
  for_each = var.customers
  
  name = "lambda-webhook-${each.key}-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  for_each = var.customers
  
  role       = aws_iam_role.lambda[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Customer-specific secrets access (if needed)
resource "aws_iam_role_policy" "secrets_access" {
  for_each = var.customers
  
  name = "secrets-access-${each.key}"
  role = aws_iam_role.lambda[each.key].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = "arn:aws:secretsmanager:*:*:secret:portal26/${each.key}/*"
    }]
  })
}
```

### Deployment Script

```bash
#!/bin/bash
# deploy.sh - Deploy infrastructure for all customers

set -e

echo "Deploying One Lambda Per Customer Architecture..."

# Build Lambda packages
echo "Building Lambda packages..."
cd lambda
pip install -r requirements.txt -t package/
cp handler.py package/
cd package && zip -r ../handler.zip . && cd ..
cp authorizer.py package/
cd package && zip -r ../authorizer.zip . && cd ..
cd ..

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Plan
echo "Planning Terraform changes..."
terraform plan -out=tfplan

# Apply
echo "Applying Terraform changes..."
terraform apply tfplan

# Get API Gateway URL
API_URL=$(terraform output -raw api_gateway_url)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "API Endpoints:"
echo "  Customer 1: ${API_URL}/webhook/customer1"
echo "  Customer 2: ${API_URL}/webhook/customer2"
echo "  Customer 3: ${API_URL}/webhook/customer3"
echo ""
echo "Next steps:"
echo "1. Configure GCP Pub/Sub push subscriptions"
echo "2. Test with: curl -X POST ${API_URL}/webhook/customer1 -H 'Authorization: Bearer <token>' -d '{...}'"
echo "3. Monitor CloudWatch dashboards"
```

---

## Lambda Handler Code

### Shared Handler Code (Deployed to All Customer Lambdas)

```python
"""
handler.py
Shared Lambda handler code deployed to all customer-specific Lambda functions.
Customer-specific configuration via environment variables.
"""
import json
import os
import base64
import requests
import logging
from datetime import datetime, timezone

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Customer-specific configuration from environment variables
CUSTOMER_ID = os.environ.get('CUSTOMER_ID')
PORTAL26_ENDPOINT = os.environ.get('PORTAL26_ENDPOINT')
OTEL_SERVICE_NAME = os.environ.get('OTEL_SERVICE_NAME', f'gcp-vertex-monitor-{CUSTOMER_ID}')
TENANT_ID = os.environ.get('TENANT_ID', 'tenant1')
OTEL_AUTH_HEADER = os.environ.get('OTEL_AUTH_HEADER', '')

def lambda_handler(event, context):
    """
    Main Lambda handler for customer-specific webhook
    
    This same code is deployed to all customer Lambdas.
    Customer identification comes from environment variables, not from request.
    """
    logger.info(f"Processing webhook request for customer: {CUSTOMER_ID}")
    
    try:
        # Extract customer context from authorizer (if using OIDC)
        if 'authorizer' in event.get('requestContext', {}):
            authorized_customer = event['requestContext']['authorizer'].get('customer_id')
            service_account = event['requestContext']['authorizer'].get('service_account')
            
            # Verify authorized customer matches Lambda's customer
            if authorized_customer != CUSTOMER_ID:
                logger.error(f"Authorization mismatch: {authorized_customer} != {CUSTOMER_ID}")
                return error_response(403, "Forbidden")
            
            logger.info(f"Authorized: {service_account}")
        
        # Parse request body
        body = json.loads(event['body'])
        
        # Validate Pub/Sub message structure
        if 'message' not in body or 'data' not in body['message']:
            return error_response(400, "Invalid Pub/Sub message structure")
        
        # Decode Pub/Sub message
        message_data = base64.b64decode(body['message']['data']).decode('utf-8')
        log_entry = json.loads(message_data)
        
        # Filter for Reasoning Engine logs (optional)
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', '')
        
        if resource_type != 'aiplatform.googleapis.com/ReasoningEngine':
            logger.info(f"Skipping non-Reasoning Engine log: {resource_type}")
            return success_response("Skipped")
        
        # Convert to OTEL format
        otel_log = convert_to_otel(log_entry)
        
        # Send to Portal26
        success = send_to_portal26([otel_log])
        
        if success:
            logger.info(f"Successfully forwarded log to Portal26 for {CUSTOMER_ID}")
            return success_response("Success")
        else:
            logger.error(f"Failed to forward log to Portal26 for {CUSTOMER_ID}")
            return error_response(500, "Failed to forward to Portal26")
            
    except Exception as e:
        logger.error(f"Error processing webhook for {CUSTOMER_ID}: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")

def convert_to_otel(log_entry):
    """
    Convert GCP log entry to OTEL log format
    """
    timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)
    
    severity = log_entry.get('severity', 'INFO')
    text_payload = log_entry.get('textPayload', '')
    json_payload = log_entry.get('jsonPayload', {})
    resource = log_entry.get('resource', {})
    labels = log_entry.get('labels', {})
    
    # Severity mapping
    severity_map = {
        "DEBUG": 5, "INFO": 9, "NOTICE": 10, "WARNING": 13,
        "ERROR": 17, "CRITICAL": 21, "ALERT": 22, "EMERGENCY": 23
    }
    
    otel_log = {
        "timeUnixNano": str(timestamp_ns),
        "severityText": severity,
        "severityNumber": severity_map.get(severity, 9),
        "body": {
            "stringValue": text_payload if text_payload else json.dumps(json_payload)
        },
        "attributes": []
    }
    
    # Add customer isolation attribute (CRITICAL)
    otel_log["attributes"].append({
        "key": "customer.id",
        "value": {"stringValue": CUSTOMER_ID}
    })
    
    # Add resource attributes
    resource_labels = resource.get('labels', {})
    for key, value in resource_labels.items():
        otel_log["attributes"].append({
            "key": f"resource.{key}",
            "value": {"stringValue": str(value)}
        })
    
    # Add log labels
    for key, value in labels.items():
        otel_log["attributes"].append({
            "key": key,
            "value": {"stringValue": str(value)}
        })
    
    # Add trace/span IDs
    if 'trace' in log_entry:
        trace_id = log_entry['trace'].split('/')[-1] if '/' in log_entry['trace'] else log_entry['trace']
        otel_log["traceId"] = trace_id
    if 'spanId' in log_entry:
        otel_log["spanId"] = log_entry['spanId']
    
    return otel_log

def send_to_portal26(logs):
    """
    Send logs to Portal26 OTEL endpoint
    """
    if not logs:
        return True
    
    # Build OTEL payload
    payload = {
        "resourceLogs": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": OTEL_SERVICE_NAME}},
                    {"key": "source", "value": {"stringValue": "gcp-pubsub"}},
                    {"key": "customer.id", "value": {"stringValue": CUSTOMER_ID}},
                    {"key": "tenant.id", "value": {"stringValue": TENANT_ID}}
                ]
            },
            "scopeLogs": [{
                "scope": {
                    "name": f"gcp-pubsub-monitor-{CUSTOMER_ID}",
                    "version": "1.0.0"
                },
                "logRecords": logs
            }]
        }]
    }
    
    try:
        # Send to Portal26
        url = f"{PORTAL26_ENDPOINT}/v1/logs"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authentication header
        if OTEL_AUTH_HEADER:
            auth_parts = OTEL_AUTH_HEADER.split('=', 1)
            if len(auth_parts) == 2:
                headers[auth_parts[0]] = auth_parts[1]
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Sent {len(logs)} logs to Portal26")
            return True
        else:
            logger.error(f"Portal26 returned {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send to Portal26: {str(e)}")
        return False

def success_response(message):
    """Return success response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'status': 'success',
            'customer_id': CUSTOMER_ID,
            'message': message
        })
    }

def error_response(status_code, message):
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'status': 'error',
            'message': message
        })
    }
```

### Authorizer Lambda Code

```python
"""
authorizer.py
Shared Lambda Authorizer for all customers.
Validates OIDC token and ensures customer can only access their own endpoint.
"""
import json
import os
import jwt
import requests
from functools import lru_cache

# Customer allowlist (service account → customer_id mapping)
CUSTOMER_ALLOWLIST = json.loads(os.environ.get('CUSTOMER_ALLOWLIST', '{}'))

# Google's JWKS endpoint
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"

@lru_cache(maxsize=1)
def get_google_public_keys():
    """
    Fetch Google's public keys for JWT verification
    Cached for 1 hour
    """
    response = requests.get(GOOGLE_JWKS_URL, timeout=10)
    return response.json()

def lambda_handler(event, context):
    """
    Lambda Authorizer handler
    Validates OIDC token from GCP Pub/Sub
    """
    try:
        # Extract token from Authorization header
        token = event['headers'].get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return generate_policy('Deny', event['methodArn'])
        
        # Verify JWT signature
        jwks = get_google_public_keys()
        decoded = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_signature": True, "verify_exp": True}
        )
        
        # Extract service account email
        service_account = decoded.get('email')
        if not service_account:
            return generate_policy('Deny', event['methodArn'])
        
        # Check if service account is in allowlist
        if service_account not in CUSTOMER_ALLOWLIST:
            return generate_policy('Deny', event['methodArn'])
        
        customer_id = CUSTOMER_ALLOWLIST[service_account]
        
        # Extract customer from endpoint path
        # methodArn: arn:aws:execute-api:region:account:api-id/stage/method/webhook/customer1
        endpoint_customer = extract_customer_from_arn(event['methodArn'])
        
        # CRITICAL: Verify customer_id matches endpoint
        if customer_id != endpoint_customer:
            print(f"Authorization violation: {customer_id} tried to access {endpoint_customer}")
            return generate_policy('Deny', event['methodArn'])
        
        # Generate Allow policy with customer context
        return generate_policy('Allow', event['methodArn'], {
            'customer_id': customer_id,
            'service_account': service_account,
            'token_expiry': str(decoded.get('exp'))
        })
        
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {str(e)}")
        return generate_policy('Deny', event['methodArn'])
    except Exception as e:
        print(f"Authorization error: {str(e)}")
        return generate_policy('Deny', event['methodArn'])

def extract_customer_from_arn(method_arn):
    """
    Extract customer ID from methodArn
    Example: arn:aws:execute-api:us-east-1:123456789012:api-id/prod/POST/webhook/customer1
    Returns: "customer1"
    """
    parts = method_arn.split('/')
    if len(parts) >= 5 and parts[-2] == 'webhook':
        return parts[-1]
    return None

def generate_policy(effect, resource, context=None):
    """
    Generate IAM policy document
    """
    policy = {
        'principalId': context.get('customer_id', 'unknown') if context else 'unknown',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy
```

---

## Customer Onboarding Process

### Adding a New Customer

**Step 1: Update Terraform Configuration**

```hcl
# terraform.tfvars
customers = {
  # ... existing customers ...
  
  customer4 = {
    memory              = 512
    timeout             = 60
    reserved_concurrency = 0
    rate_limit          = 1000
    portal26_endpoint   = "https://otel.portal26.in:4318"
  }
}
```

**Step 2: Deploy Infrastructure**

```bash
# Plan changes
terraform plan

# Expected output:
# + aws_lambda_function.customer_webhook["customer4"]
# + aws_api_gateway_resource.customer["customer4"]
# + aws_api_gateway_method.customer_post["customer4"]
# + aws_cloudwatch_log_group.customer["customer4"]
# ... etc

# Apply changes
terraform apply

# Time: ~5 minutes
```

**Step 3: Get Endpoint URL**

```bash
API_URL=$(terraform output -raw api_gateway_url)
echo "Customer 4 endpoint: ${API_URL}/webhook/customer4"
```

**Step 4: Update Authorizer Allowlist**

```bash
# Update authorizer Lambda environment variable
aws lambda update-function-configuration \
  --function-name webhook-authorizer \
  --environment Variables="{CUSTOMER_ALLOWLIST=$(jq -n --arg sa 'customer4@project.iam.gserviceaccount.com' --arg cid 'customer4' '$ENV.CUSTOMER_ALLOWLIST + {($sa): $cid}')}"
```

**Step 5: Configure Customer's GCP Pub/Sub**

```bash
# Customer runs this in their GCP project
gcloud iam service-accounts create customer4-pubsub \
  --display-name "Customer 4 Pub/Sub Forwarder"

gcloud pubsub subscriptions create customer4-telemetry \
  --topic vertex-telemetry-topic \
  --push-endpoint https://your-api.execute-api.us-east-1.amazonaws.com/prod/webhook/customer4 \
  --push-auth-service-account customer4-pubsub@customer-project.iam.gserviceaccount.com \
  --push-auth-audience https://your-api.execute-api.us-east-1.amazonaws.com/prod/webhook
```

**Step 6: Test**

```bash
# Trigger customer's Reasoning Engine to generate logs
# Check CloudWatch Logs for customer4
aws logs tail /aws/lambda/webhook-customer4 --follow

# Check Portal26 dashboard
# Query: WHERE customer.id = "customer4"
```

**Total Time:** 15-30 minutes per customer

---

## Monitoring & Observability

### CloudWatch Dashboards

#### Option 1: Aggregate Dashboard (All Customers)

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Invocations by Customer",
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Customer1"}, {"dimensions": {"FunctionName": "webhook-customer1"}}],
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
          [".", "Invocations", {"stat": "Sum", "visible": false, "id": "invocations"}]
        ],
        "period": 300,
        "yAxis": {"left": {"min": 0, "max": 100}},
        "stat": "Average"
      }
    }
  ]
}
```

Cost: $3/month (single dashboard)

#### Option 2: Per-Customer Dashboards

```python
# Generate dashboard per customer automatically
for customer in customers:
    create_dashboard(f"webhook-{customer}", [
        metric_widget("Invocations", customer),
        metric_widget("Errors", customer),
        metric_widget("Duration", customer),
        metric_widget("Throttles", customer)
    ])
```

Cost: $3/month × 30 customers = $90/month

### CloudWatch Alarms

```hcl
# alarm.tf
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = var.customers
  
  alarm_name          = "webhook-${each.key}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "High error rate for ${each.key}"
  
  dimensions = {
    FunctionName = "webhook-${each.key}"
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  for_each = var.customers
  
  alarm_name          = "webhook-${each.key}-throttled"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Lambda throttled for ${each.key}"
  
  dimensions = {
    FunctionName = "webhook-${each.key}"
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

Cost: $0.10/alarm × 2 alarms × 30 customers = $6/month

### Log Insights Queries

```sql
-- Find errors for specific customer
fields @timestamp, @message
| filter @message like /ERROR/
| filter customer_id = "customer1"
| sort @timestamp desc
| limit 100

-- Count requests per customer
stats count() by customer_id

-- Average latency per customer
filter @type = "REPORT"
| stats avg(@duration) by customer_id

-- Find slow requests (>2s)
filter @type = "REPORT"
| filter @duration > 2000
| fields @timestamp, customer_id, @duration
| sort @duration desc
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Forbidden" or 403 Error

**Symptom:** Customer receives 403 Forbidden

**Possible Causes:**
1. Service account not in allowlist
2. Token expired
3. Service account trying to access wrong endpoint

**Debug:**
```bash
# Check authorizer logs
aws logs tail /aws/lambda/webhook-authorizer --follow

# Look for:
# "Authorization violation: customer1 tried to access customer2"
# "Service account not in allowlist"
# "Invalid token"
```

**Fix:**
```bash
# Add service account to allowlist
# Update authorizer Lambda environment variable
```

#### Issue 2: "Internal Server Error" or 500 Error

**Symptom:** Customer receives 500 error

**Possible Causes:**
1. Lambda crashed
2. Portal26 endpoint unreachable
3. Invalid Pub/Sub message format

**Debug:**
```bash
# Check customer's Lambda logs
aws logs tail /aws/lambda/webhook-customer1 --follow

# Look for:
# "Failed to forward to Portal26"
# "Invalid Pub/Sub message structure"
# "Timeout" or "ConnectionError"
```

**Fix:**
```bash
# Check Portal26 endpoint
curl -v https://otel.portal26.in:4318/v1/logs

# Check Lambda configuration
aws lambda get-function-configuration --function-name webhook-customer1
```

#### Issue 3: High Latency

**Symptom:** Requests taking >2 seconds

**Possible Causes:**
1. Cold start
2. Portal26 slow to respond
3. Lambda memory too low

**Debug:**
```bash
# Check Lambda duration metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=webhook-customer1 \
  --start-time 2025-01-15T00:00:00Z \
  --end-time 2025-01-15T23:59:59Z \
  --period 300 \
  --statistics Average
```

**Fix:**
```bash
# Increase Lambda memory (faster CPU)
aws lambda update-function-configuration \
  --function-name webhook-customer1 \
  --memory-size 1024

# Or use provisioned concurrency (eliminate cold starts)
aws lambda put-provisioned-concurrency-config \
  --function-name webhook-customer1 \
  --qualifier '$LATEST' \
  --provisioned-concurrent-executions 1
# Cost: +$6/month per customer
```

#### Issue 4: Throttling

**Symptom:** "Rate exceeded" or 429 error

**Possible Causes:**
1. Customer exceeding rate limit
2. Lambda concurrency limit reached
3. API Gateway throttling

**Debug:**
```bash
# Check throttle metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value=webhook-customer1 \
  --start-time 2025-01-15T00:00:00Z \
  --end-time 2025-01-15T23:59:59Z \
  --period 300 \
  --statistics Sum
```

**Fix:**
```bash
# Increase reserved concurrency
aws lambda put-function-concurrency \
  --function-name webhook-customer1 \
  --reserved-concurrent-executions 100

# Or increase API Gateway rate limit
# (Update Usage Plan in Terraform)
```

---

## Cost Optimization Strategies

### Strategy 1: Reduce CloudWatch Costs

CloudWatch is 60-65% of total cost. Options:

**Option A: Single Aggregate Dashboard**
```
Instead of 30 dashboards ($90/month)
Use 1 dashboard with all customers ($3/month)
Savings: $87/month
```

**Option B: Reduce Log Retention**
```
Instead of 30 days retention
Use 7 days retention
Savings: ~$10/month
```

**Option C: Sample Logs**
```
Log only 10% of successful requests
Log 100% of errors
Savings: ~$12/month
```

### Strategy 2: Right-Size Lambda Memory

```
Small customers: 256MB instead of 512MB
Savings: ~$1/customer/month

Monitor performance and adjust:
- If latency <500ms: Consider reducing memory
- If latency >1000ms: Consider increasing memory
```

### Strategy 3: Use Shared Portal26 Endpoint

```
Instead of dedicated Portal26 per customer
Use shared Portal26 with customer.id attribute
Savings: ~$100/customer/month (Portal26 hosting cost)
```

### Strategy 4: Batch Processing

```
Instead of synchronous Lambda per request
Use SQS + batch processing Lambda
Process 10 messages at once
Savings: ~40% Lambda cost
```

---

## When to Use One Lambda Per Customer

### ✅ Use This Architecture If:

1. **Need Complete Customer Isolation**
   - Compliance requirements (HIPAA, PCI-DSS, FedRAMP)
   - Customer contract demands dedicated resources
   - One customer's bug must not affect others

2. **Customers Have Very Different Requirements**
   - Customer A needs 10GB memory, Customer B needs 128MB
   - Different timeout requirements per customer
   - Different Portal26 endpoints per customer

3. **Want Per-Customer Configuration**
   - Custom environment variables per customer
   - Different IAM roles/permissions per customer
   - Customer-specific secrets

4. **Need Per-Customer Monitoring**
   - Dedicated dashboards per customer
   - Customer-specific alarms
   - Can provide customer access to their logs

5. **Plan to Charge Per Customer**
   - Can track exact AWS costs per customer
   - Billing transparency (each Lambda's cost visible)
   - Can implement different pricing tiers

6. **Have <200 Customers**
   - Operational overhead manageable
   - Under AWS Lambda function limits
   - Monitoring cost acceptable

### ❌ Do NOT Use If:

1. **Cost is Critical**
   - 10× more expensive than shared Lambda
   - CloudWatch monitoring dominates cost
   - Shared Lambda is sufficient

2. **Want Simple Operations**
   - 30 functions = 30× deployment complexity
   - Shared Lambda much simpler
   - Small team with limited DevOps

3. **Plan to Scale to 500+ Customers**
   - Hits AWS Lambda function limits (~1000 per region)
   - Operational overhead becomes unmanageable
   - CloudWatch cost explodes ($300+/month)

4. **All Customers Have Similar Needs**
   - Same memory, timeout, configuration
   - No special isolation requirements
   - Shared Lambda works fine

---

## Summary & Recommendation

### Architecture Summary

**One Lambda Per Customer:**
- Cost: $1.75-$4.75 per customer/month
- Complexity: High (30 functions to manage)
- Isolation: Maximum (complete separation)
- Best for: Enterprise SaaS with <200 customers

### Comparison with Alternatives

| Metric | Shared Lambda | One Lambda/Customer | ECS Containers |
|--------|--------------|---------------------|----------------|
| **Cost (30 customers)** | $5 | $53-$143 | $200 |
| **Cost per customer** | $0.17 | $1.75-$4.75 | $6.67 |
| **Deployment time** | 2 min | 30 min | 1 hour |
| **Operational overhead** | Very Low | High | Very High |
| **Customer isolation** | Logical | Physical | Physical |
| **Scalability** | 1000+ | 200-500 | 100-200 |

### Final Recommendation

**Use Shared Lambda** for most use cases, unless you have specific requirements:

- ✅ Start with shared Lambda ($5/month)
- ✅ Add per-customer Lambdas ONLY for enterprise customers who pay for it
- ✅ Hybrid approach: 25 customers on shared Lambda + 5 enterprise customers on dedicated Lambdas

**Hybrid Cost Example:**
```
Shared Lambda (25 customers): $5/month
+ 5 Dedicated Lambdas: 5 × $4.75 = $23.75/month
Total: $28.75/month for 30 customers
vs $143/month if all dedicated
Savings: $114.25/month (80% savings)
```

This gives you best of both worlds: low cost for standard customers + premium isolation for enterprise customers who need and pay for it.
