#!/usr/bin/env python3
"""
Deploy portal26GCPLocal Agent
Exports telemetry via ngrok to local OTEL collector
"""

import subprocess
import sys
import json

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
REGION = "us-central1"
AGENT_NAME = "portal26GCPLocal"
PACKAGE_DIR = "adk_agent_ngrok"
OTEL_ENDPOINT = "https://tabetha-unelemental-bibulously.ngrok-free.dev"

print("=" * 80)
print(f"Deploying: {AGENT_NAME}")
print("=" * 80)
print()
print(f"Project:          {PROJECT_ID}")
print(f"Region:           {REGION}")
print(f"Package:          {PACKAGE_DIR}")
print(f"OTEL Endpoint:    {OTEL_ENDPOINT}")
print(f"Export Path:      Agent → ngrok → Local Collector → Portal26 + Files")
print()
print("=" * 80)
print()

# Deploy command
cmd = [
    "python", "-m", "google.adk.cli", "deploy", "agent_engine",
    f"--project={PROJECT_ID}",
    f"--region={REGION}",
    f"--display_name={AGENT_NAME}",
    "--otel_to_cloud",
    PACKAGE_DIR
]

print("Running deployment command:")
print(f"  {' '.join(cmd)}")
print()
print("=" * 80)
print()

try:
    # Run deployment
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300  # 5 minutes
    )

    # Print output
    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print("STDERR:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)

    print()
    print("=" * 80)

    if result.returncode == 0:
        print("✅ DEPLOYMENT SUCCESSFUL")
        print("=" * 80)
        print()
        print(f"Agent Name:       {AGENT_NAME}")
        print(f"Service Name:     portal26GCPLocal")
        print(f"Package:          {PACKAGE_DIR}")
        print()
        print("Telemetry Flow:")
        print("  1. Agent generates telemetry")
        print("  2. Sends to ngrok tunnel")
        print("  3. Forwards to local OTEL collector")
        print("  4. Collector exports to:")
        print("     - Portal26 cloud")
        print("     - Local files (otel-data/)")
        print("     - Console (debug)")
        print()
        print("View agent:")
        print(f"  https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={PROJECT_ID}")
        print()
        print("Monitor telemetry:")
        print("  - ngrok UI:       http://localhost:4040")
        print("  - Local files:    otel-data/*.json")
        print("  - Portal26:       https://portal26.in")
        print("    Filter by:      service.name=portal26GCPLocal")
        print()
        print("Test the agent:")
        print('  curl -X POST "https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{REGION}/reasoningEngines/{RESOURCE_ID}:query" \\')
        print('    -H "Authorization: Bearer $(gcloud auth print-access-token)" \\')
        print('    -d \'{"input": {"message": "What is the weather in Tokyo?"}}\'')
        print()
        sys.exit(0)
    else:
        print("❌ DEPLOYMENT FAILED")
        print("=" * 80)
        print()
        print(f"Exit code: {result.returncode}")
        print()
        print("Check the error messages above for details.")
        print()
        print("Common issues:")
        print("  - Check that .env file exists in adk_agent_ngrok/")
        print("  - Verify GCP project ID and permissions")
        print("  - Ensure Vertex AI API is enabled")
        print("  - Check that ngrok is running: ngrok http 4318")
        print()
        sys.exit(1)

except subprocess.TimeoutExpired:
    print()
    print("=" * 80)
    print("❌ DEPLOYMENT TIMEOUT")
    print("=" * 80)
    print()
    print("Deployment exceeded 5 minutes and was terminated.")
    print("This may indicate a problem with the deployment process.")
    print()
    sys.exit(1)

except KeyboardInterrupt:
    print()
    print()
    print("=" * 80)
    print("⚠️  DEPLOYMENT CANCELLED")
    print("=" * 80)
    print()
    print("Deployment was interrupted by user.")
    print()
    sys.exit(130)

except Exception as e:
    print()
    print("=" * 80)
    print("❌ DEPLOYMENT ERROR")
    print("=" * 80)
    print()
    print(f"Error: {str(e)}")
    print()
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)
