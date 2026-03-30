# Terraform variables file
# NEVER commit this file to Git!

# GCP Configuration
project_id = "agentic-ai-integration-490716"
region     = "us-central1"

# Service Configuration
service_name    = "ai-agent"
container_image = "gcr.io/agentic-ai-integration-490716/ai-agent:latest"
environment     = "production"
service_version = "1.0"

# Secrets
gemini_api_key  = "AIzaSyCaCCU5hUyDYC6xneT6ReQEHKr5coTkWx8"
otel_auth_header = "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="

# OpenTelemetry Configuration
otel_service_name    = "ai-agent"
otel_endpoint        = "https://otel-tenant1.portal26.in:4318"
portal26_user_id     = "relusys"
portal26_tenant_id   = "tenant1"

# Agent Configuration
agent_mode = "manual"

# Resource Configuration
cpu             = "1"
memory          = "512Mi"
timeout_seconds = 300
concurrency     = 80

# Scaling Configuration
min_instances = 0
max_instances = 10

# Access Control
allow_unauthenticated = false
