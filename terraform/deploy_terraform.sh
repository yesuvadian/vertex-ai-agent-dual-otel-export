#!/bin/bash
# Terraform deployment script for Google Cloud Shell
# Run this in Cloud Shell where Terraform is pre-installed

set -e

echo "🚀 Starting Terraform deployment..."
echo ""

# Check if we're in the terraform directory
if [ ! -f "main.tf" ]; then
    echo "❌ Error: main.tf not found. Please run this from the terraform directory."
    exit 1
fi

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ Error: terraform.tfvars not found."
    echo "Please create terraform.tfvars with your configuration."
    exit 1
fi

# Step 1: Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

echo ""
echo "✅ Initialization complete!"
echo ""

# Step 2: Validate configuration
echo "🔍 Validating configuration..."
terraform validate

echo ""
echo "✅ Configuration is valid!"
echo ""

# Step 3: Preview changes
echo "📋 Previewing changes..."
terraform plan

echo ""
echo "================================================"
echo "Ready to deploy!"
echo "================================================"
echo ""
read -p "Do you want to apply these changes? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo ""
    echo "🚀 Deploying infrastructure..."
    terraform apply -auto-approve

    echo ""
    echo "================================================"
    echo "✅ Deployment complete!"
    echo "================================================"
    echo ""

    # Show outputs
    echo "📊 Service URL:"
    terraform output service_url

    echo ""
    echo "🧪 Test commands:"
    terraform output test_command

    echo ""
    echo "🌍 Console links:"
    terraform output console_links
else
    echo "❌ Deployment cancelled."
fi
