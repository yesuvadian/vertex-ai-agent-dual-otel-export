# ============================================================================
# AWS Lambda Configuration - Multi-Customer Support
# ============================================================================
# Purpose: Single Lambda function to handle logs from multiple customers
# Features:
#   - OIDC JWT authentication
#   - Customer identification from GCP project/agent metadata
#   - Dynamic routing to customer-specific Portal26 endpoints
#   - Size-based routing (OTEL/S3/Kinesis)
# ============================================================================

# ============================================================================
# Variables
# ============================================================================
variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
  default     = "gcp-pubsub-multi-customer-processor"
}

variable "portal26_endpoints" {
  description = "Portal26 endpoints per customer"
  type = map(object({
    otel_endpoint    = string
    s3_bucket        = string
    kinesis_stream   = string
    customer_id      = string
  }))
  default = {
    "customer1" = {
      otel_endpoint  = "https://customer1.portal26.com/otel"
      s3_bucket      = "portal26-customer1-traces"
      kinesis_stream = "portal26-customer1-stream"
      customer_id    = "cust-001"
    }
    "customer2" = {
      otel_endpoint  = "https://customer2.portal26.com/otel"
      s3_bucket      = "portal26-customer2-traces"
      kinesis_stream = "portal26-customer2-stream"
      customer_id    = "cust-002"
    }
  }
}

# ============================================================================
# 1. Lambda IAM Role
# ============================================================================
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.lambda_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.lambda_function_name}-role"
    Purpose     = "multi-customer-log-processing"
    Environment = "production"
  }
}

# Lambda Basic Execution Policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for S3, Kinesis, and CloudWatch
resource "aws_iam_role_policy" "lambda_custom_policy" {
  name = "${var.lambda_function_name}-custom-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = [
          for customer, config in var.portal26_endpoints :
          "arn:aws:s3:::${config.s3_bucket}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kinesis:PutRecord",
          "kinesis:PutRecords"
        ]
        Resource = [
          for customer, config in var.portal26_endpoints :
          "arn:aws:kinesis:${var.aws_region}:*:stream/${config.kinesis_stream}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      }
    ]
  })
}

# ============================================================================
# 2. Lambda Function
# ============================================================================
resource "aws_lambda_function" "multi_customer_processor" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "lambda_multi_customer.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512

  filename         = "${path.module}/lambda_package.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_package.zip")

  environment {
    variables = {
      PORTAL26_ENDPOINTS = jsonencode(var.portal26_endpoints)
      EXPECTED_ISSUER    = "https://accounts.google.com"
      GCP_PROJECT_ID     = var.gcp_project_id
    }
  }

  tags = {
    Name        = var.lambda_function_name
    Purpose     = "multi-customer-log-processing"
    Environment = "production"
  }
}

# ============================================================================
# 3. Lambda Function URL (Public endpoint with OIDC auth)
# ============================================================================
resource "aws_lambda_function_url" "multi_customer_url" {
  function_name      = aws_lambda_function.multi_customer_processor.function_name
  authorization_type = "NONE" # Auth handled in Lambda code via OIDC

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["*"]
    max_age           = 86400
  }
}

# ============================================================================
# 4. CloudWatch Log Group
# ============================================================================
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.lambda_function_name}-logs"
    Environment = "production"
  }
}

# ============================================================================
# 5. S3 Buckets for Customer Traces
# ============================================================================
resource "aws_s3_bucket" "customer_traces" {
  for_each = var.portal26_endpoints

  bucket = each.value.s3_bucket

  tags = {
    Name        = each.value.s3_bucket
    Customer    = each.value.customer_id
    Purpose     = "trace-storage"
    Environment = "production"
  }
}

resource "aws_s3_bucket_versioning" "customer_traces_versioning" {
  for_each = aws_s3_bucket.customer_traces

  bucket = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "customer_traces_lifecycle" {
  for_each = aws_s3_bucket.customer_traces

  bucket = each.value.id

  rule {
    id     = "delete-old-traces"
    status = "Enabled"

    expiration {
      days = 90 # Keep traces for 90 days
    }
  }
}

# ============================================================================
# 6. Kinesis Streams for Customer Data
# ============================================================================
resource "aws_kinesis_stream" "customer_streams" {
  for_each = var.portal26_endpoints

  name             = each.value.kinesis_stream
  shard_count      = 1
  retention_period = 24 # hours

  tags = {
    Name        = each.value.kinesis_stream
    Customer    = each.value.customer_id
    Purpose     = "real-time-streaming"
    Environment = "production"
  }
}

# ============================================================================
# Outputs
# ============================================================================
output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.multi_customer_processor.arn
}

output "lambda_function_url" {
  description = "Lambda Function URL (use this in GCP Pub/Sub subscription)"
  value       = aws_lambda_function_url.multi_customer_url.function_url
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.multi_customer_processor.function_name
}

output "s3_buckets" {
  description = "S3 buckets for customer traces"
  value = {
    for customer, bucket in aws_s3_bucket.customer_traces :
    customer => bucket.bucket
  }
}

output "kinesis_streams" {
  description = "Kinesis streams for customer data"
  value = {
    for customer, stream in aws_kinesis_stream.customer_streams :
    customer => stream.name
  }
}
