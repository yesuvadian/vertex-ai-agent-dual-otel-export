#!/bin/bash
# ============================================================================
# Cleanup Script - Remove Old POC Files
# ============================================================================
# Purpose: Archive old POC/test files, keep only production Terraform setup
# Usage: bash cleanup_old_files.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}Monitoring Setup - Cleanup Script${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create archive directory
ARCHIVE_DIR="_archive_$(date +%Y%m%d_%H%M%S)"
echo -e "${YELLOW}Creating archive directory: $ARCHIVE_DIR${NC}"
mkdir -p "$ARCHIVE_DIR"

# ============================================================================
# Archive Function
# ============================================================================
archive_file() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "  → Archiving: $file"
        mv "$file" "$ARCHIVE_DIR/"
    fi
}

# ============================================================================
# Phase 1: Archive Old ZIP Files
# ============================================================================
echo ""
echo -e "${GREEN}Phase 1: Archiving old ZIP files...${NC}"
cd lambda_poc

archive_file "function.zip"
archive_file "lambda_api_key.zip"
archive_file "lambda_oidc.zip"              # Keep .py version, archive compiled .zip
archive_file "lambda_oidc_simple.zip"       # Keep .py version, archive compiled .zip
archive_file "lambda_shared_secret.zip"

# ============================================================================
# Phase 2: Archive Old Lambda Files (Except OIDC Reference)
# ============================================================================
echo ""
echo -e "${GREEN}Phase 2: Archiving old Lambda files (preserving OIDC reference)...${NC}"

archive_file "lambda_function.py"
archive_file "lambda_with_api_key.py"
# KEEP: lambda_with_oidc.py (OIDC reference implementation)
# KEEP: lambda_with_oidc_simple.py (OIDC simple example)
archive_file "lambda_with_shared_secret.py"
archive_file "lambda_credentials.txt"

echo -e "${YELLOW}  ℹ  Preserving OIDC reference files:${NC}"
echo "     - lambda_with_oidc.py"
echo "     - lambda_with_oidc_simple.py"

# ============================================================================
# Phase 3: Archive Old Deployment Scripts (Except OIDC Setup)
# ============================================================================
echo ""
echo -e "${GREEN}Phase 3: Archiving old deployment scripts (preserving OIDC setup)...${NC}"

archive_file "deploy.sh"
archive_file "deploy_simple.sh"
archive_file "deploy_with_url.sh"
archive_file "deploy_oidc_lambda.sh"        # Archive - replaced by Terraform
archive_file "deploy_secured_lambdas.sh"
archive_file "deploy_complete_integration.sh"
archive_file "deploy_agent_with_logging.sh"
archive_file "deploy_reasoning_engine.sh"
archive_file "setup_gcp_pubsub_with_auth.sh"
# KEEP: setup_gcp_oidc.sh (OIDC manual setup reference)
archive_file "setup_log_sink_programmatic.py"
archive_file "setup_reasoning_logs_to_aws.sh"

echo -e "${YELLOW}  ℹ  Preserving OIDC setup script:${NC}"
echo "     - setup_gcp_oidc.sh"

# ============================================================================
# Phase 4: Archive Test/POC Scripts
# ============================================================================
echo ""
echo -e "${GREEN}Phase 4: Archiving test and POC scripts...${NC}"

archive_file "add_auth_headers.py"
archive_file "check_console_test.sh"
archive_file "create_adk_style_agent.py"
archive_file "create_agent_api.py"
archive_file "create_reasoning_engine_with_logs.py"
archive_file "create_simple_adk_agent.py"
archive_file "deploy_vertex_reasoning_engine.py"
archive_file "test_adk_style_agent.py"
archive_file "test_from_console.py"
archive_file "test_local.py"
archive_file "test_reasoning_engine.py"
archive_file "test_reasoning_engine_new.py"
archive_file "test_simple_adk_agent.py"

# ============================================================================
# Phase 5: Archive Old Requirements Files (Except OIDC)
# ============================================================================
echo ""
echo -e "${GREEN}Phase 5: Archiving old requirements files (preserving OIDC)...${NC}"

archive_file "requirements.txt"
# KEEP: requirements_oidc.txt (OIDC dependencies reference)
archive_file "requirements_log_sink.txt"

echo -e "${YELLOW}  ℹ  Preserving OIDC requirements:${NC}"
echo "     - requirements_oidc.txt"

# ============================================================================
# Phase 6: Archive Old Config Files (Except OIDC Config)
# ============================================================================
echo ""
echo -e "${GREEN}Phase 6: Archiving old config files (preserving OIDC config)...${NC}"

# KEEP: oidc_lambda_config.txt (OIDC configuration reference)
archive_file "reasoning_agent.py"

echo -e "${YELLOW}  ℹ  Preserving OIDC config:${NC}"
echo "     - oidc_lambda_config.txt"

# ============================================================================
# Phase 7: Archive Deprecated Documentation
# ============================================================================
echo ""
echo -e "${GREEN}Phase 7: Archiving deprecated documentation...${NC}"

archive_file "ARCHITECTURE_WRITEUP.md"
archive_file "COMPLETE_ARCHITECTURE_DIAGRAM.md"
archive_file "COMPLETE_SETUP_SUMMARY.md"
archive_file "DEPLOYMENT_STATUS.md"
archive_file "EMAIL_WRITEUP.md"
archive_file "FINAL_ARCHITECTURE.md"
archive_file "FINAL_DEPLOYMENT_SUMMARY.md"
archive_file "FINAL_INTEGRATED_ARCHITECTURE.md"
archive_file "GCP_AGENT_SECURITY.md"
archive_file "HEADER_LIMITATION.md"
archive_file "INTEGRATION_WITH_PORTAL26_PREPROCESSOR.md"
archive_file "MANUAL_HEADER_SETUP.md"

# ============================================================================
# Phase 8: Archive Root Level Deprecated Files
# ============================================================================
echo ""
echo -e "${GREEN}Phase 8: Archiving root level deprecated files...${NC}"
cd ..

archive_file "AGENT_ENGINE_LOGGING.md"
archive_file "AGENT_ENGINE_SOLUTION.md"
archive_file "ARCHITECTURE.md"
archive_file "ARCHITECTURE_ONE_LAMBDA_PER_CUSTOMER.md"
archive_file "AWS_DEPLOYMENT.md"
archive_file "CONTINUOUS_OPERATION_GUIDE.md"
archive_file "DEPLOYMENT_SUMMARY.md"
archive_file "continuous_forwarder.py"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

# Count archived files
ARCHIVED_COUNT=$(ls -1 "$ARCHIVE_DIR" 2>/dev/null | wc -l)
echo -e "${YELLOW}Archived files: $ARCHIVED_COUNT${NC}"
echo -e "${YELLOW}Archive location: $SCRIPT_DIR/$ARCHIVE_DIR${NC}"
echo ""

# Calculate archive size
if [ -d "$ARCHIVE_DIR" ]; then
    ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" | cut -f1)
    echo -e "${YELLOW}Archive size: $ARCHIVE_SIZE${NC}"
fi

echo ""
echo -e "${GREEN}✅ What was kept:${NC}"
echo ""
echo "  ${YELLOW}Production Infrastructure:${NC}"
echo "    - lambda_poc/terraform/          (All Terraform configs)"
echo ""
echo "  ${YELLOW}OIDC Reference Files (Working Solution):${NC}"
echo "    - lambda_with_oidc.py           (OIDC Lambda implementation)"
echo "    - lambda_with_oidc_simple.py    (Simple OIDC example)"
echo "    - setup_gcp_oidc.sh             (OIDC setup script)"
echo "    - requirements_oidc.txt         (OIDC dependencies)"
echo "    - oidc_lambda_config.txt        (OIDC configuration notes)"
echo ""
echo "  ${YELLOW}Documentation:${NC}"
echo "    - LOG_SINK_DEEP_DIVE.md"
echo "    - PUBSUB_DEEP_DIVE.md"
echo "    - CONCEPTUAL_EXPLANATION.md"
echo "    - SECURITY_SETUP.md"
echo ""

echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo "  1. Test Terraform deployment still works"
echo "  2. Verify documentation is complete"
echo "  3. After 1-2 weeks of testing, you can delete archive:"
echo "     rm -rf $SCRIPT_DIR/$ARCHIVE_DIR"
echo ""

echo -e "${GREEN}To restore archived files:${NC}"
echo "  mv $SCRIPT_DIR/$ARCHIVE_DIR/* $SCRIPT_DIR/lambda_poc/"
echo ""

echo -e "${GREEN}============================================================================${NC}"
