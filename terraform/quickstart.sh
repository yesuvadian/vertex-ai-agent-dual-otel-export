#!/bin/bash

# Terraform Quick Start Script for Vertex AI Agent Engine
# Usage: ./quickstart.sh [init|plan|apply|update-ngrok|update-otel|destroy]

set -e

PROJECT_ID="agentic-ai-integration-490716"
REGION="us-central1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Terraform
    if command -v terraform &> /dev/null; then
        TERRAFORM_VERSION=$(terraform version | head -n1)
        print_success "Terraform installed: $TERRAFORM_VERSION"
    else
        print_error "Terraform not installed"
        exit 1
    fi

    # Check gcloud
    if command -v gcloud &> /dev/null; then
        print_success "gcloud installed"
    else
        print_error "gcloud not installed"
        exit 1
    fi

    # Check authentication
    if gcloud auth application-default print-access-token &> /dev/null; then
        print_success "GCP authenticated"
    else
        print_warning "GCP not authenticated. Run: gcloud auth application-default login"
        exit 1
    fi

    # Check Python and ADK
    if python -m google.adk.cli --version &> /dev/null; then
        print_success "google-adk installed"
    else
        print_error "google-adk not installed. Run: pip install google-adk"
        exit 1
    fi
}

terraform_init() {
    print_header "Initializing Terraform"

    if [ ! -f "terraform.tfvars" ]; then
        print_warning "terraform.tfvars not found. Creating from example..."
        cp terraform.tfvars.example terraform.tfvars
        print_success "Created terraform.tfvars - please review and customize"
        print_warning "Edit terraform.tfvars with your values before proceeding"
        exit 0
    fi

    terraform init
    print_success "Terraform initialized"
}

terraform_plan() {
    print_header "Planning Terraform Changes"
    terraform plan
}

terraform_apply() {
    print_header "Applying Terraform Configuration"
    terraform apply

    print_success "Configuration applied"
    echo ""
    echo "Next steps:"
    echo "  1. Review the updated .env files"
    echo "  2. If you want to redeploy agents, set trigger_redeploy=true in terraform.tfvars"
    echo "  3. Run: ./quickstart.sh apply"
}

update_ngrok_endpoint() {
    print_header "Updating ngrok Endpoint"

    echo "Current endpoint:"
    grep OTEL_EXPORTER_OTLP_ENDPOINT ../portal26_ngrok_agent/.env || echo "Not set"
    echo ""

    read -p "Enter new ngrok endpoint URL: " NEW_ENDPOINT

    # Update terraform.tfvars
    if [ -f "terraform.tfvars" ]; then
        # This is a simple approach - for production, use proper tfvars editing
        print_warning "Please manually update terraform.tfvars with:"
        echo "  otel_endpoint = \"$NEW_ENDPOINT\""
        echo ""
        echo "Then run: ./quickstart.sh apply"
    else
        print_error "terraform.tfvars not found"
        exit 1
    fi
}

update_otel_endpoint() {
    print_header "Updating Portal26 OTEL Endpoint"

    echo "Current endpoint:"
    grep OTEL_EXPORTER_OTLP_ENDPOINT ../portal26_otel_agent/.env || echo "Not set"
    echo ""

    read -p "Enter new Portal26 endpoint URL: " NEW_ENDPOINT

    print_warning "Please manually update terraform.tfvars with:"
    echo "  otel_endpoint = \"$NEW_ENDPOINT\""
    echo ""
    echo "Then run: ./quickstart.sh apply"
}

show_status() {
    print_header "Current Agent Status"

    echo "portal26_ngrok_agent:"
    echo "  ID: $(terraform output -raw portal26_ngrok_agent_id 2>/dev/null || echo 'Not set')"
    echo "  .env file: $(terraform output -raw portal26_ngrok_agent_env_file 2>/dev/null || echo 'Not set')"
    echo ""

    echo "portal26_otel_agent:"
    echo "  ID: $(terraform output -raw portal26_otel_agent_id 2>/dev/null || echo 'Not set')"
    echo "  .env file: $(terraform output -raw portal26_otel_agent_env_file 2>/dev/null || echo 'Not set')"
    echo ""

    echo "Current environment variables:"
    echo ""
    echo "=== portal26_ngrok_agent ==="
    cat ../portal26_ngrok_agent/.env 2>/dev/null || echo "File not found"
    echo ""
    echo "=== portal26_otel_agent ==="
    cat ../portal26_otel_agent/.env 2>/dev/null || echo "File not found"
}

terraform_destroy() {
    print_header "Destroying Terraform Resources"
    print_warning "This will remove Terraform state but NOT delete the agents"
    print_warning "To delete agents, use the GCP Console or gcloud commands"

    read -p "Continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" == "yes" ]; then
        terraform destroy
        print_success "Terraform resources destroyed"
    else
        print_warning "Cancelled"
    fi
}

show_help() {
    echo "Terraform Quick Start for Vertex AI Agent Engine"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  init           - Initialize Terraform and create terraform.tfvars"
    echo "  plan           - Preview changes"
    echo "  apply          - Apply configuration changes"
    echo "  status         - Show current agent status and env vars"
    echo "  update-ngrok   - Update ngrok endpoint"
    echo "  update-otel    - Update Portal26 OTEL endpoint"
    echo "  destroy        - Remove Terraform state (doesn't delete agents)"
    echo "  check          - Check prerequisites"
    echo ""
    echo "Examples:"
    echo "  $0 init                    # First time setup"
    echo "  $0 plan                    # Preview changes"
    echo "  $0 apply                   # Apply changes"
    echo "  $0 status                  # Check current status"
}

# Main script
case "${1:-help}" in
    init)
        check_prerequisites
        terraform_init
        ;;
    plan)
        check_prerequisites
        terraform_plan
        ;;
    apply)
        check_prerequisites
        terraform_apply
        ;;
    status)
        show_status
        ;;
    update-ngrok)
        update_ngrok_endpoint
        ;;
    update-otel)
        update_otel_endpoint
        ;;
    destroy)
        terraform_destroy
        ;;
    check)
        check_prerequisites
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
