#!/usr/bin/env python3
"""
Deploy two agents with different OTEL export destinations:
1. portal26GCPLocal - exports to ngrok (local collector)
2. portal26GCPTel - exports directly to Portal26 cloud
"""

import subprocess
import sys
import time

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
REGION = "us-central1"

agents_config = [
    {
        "name": "portal26GCPLocal",
        "package": "adk_agent_ngrok",
        "description": "Agent with ngrok export (local collector)",
        "endpoint": "https://tabetha-unelemental-bibulously.ngrok-free.dev",
    },
    {
        "name": "portal26GCPTel",
        "package": "adk_agent_portal26",
        "description": "Agent with direct Portal26 export",
        "endpoint": "https://otel-tenant1.portal26.in:4318",
    },
]

print("=" * 80)
print("Deploying 2 Agents with Different OTEL Endpoints")
print("=" * 80)
print()
print(f"Project: {PROJECT_ID}")
print(f"Region: {REGION}")
print()

deployed_agents = []

for idx, config in enumerate(agents_config, 1):
    print(f"[{idx}/2] Deploying: {config['name']}")
    print("-" * 80)
    print(f"  Package: {config['package']}")
    print(f"  OTEL Endpoint: {config['endpoint']}")
    print()

    try:
        # Deploy command
        cmd = [
            "python", "-m", "google.adk.cli", "deploy", "agent_engine",
            f"--project={PROJECT_ID}",
            f"--region={REGION}",
            f"--display_name={config['name']}",
            "--otel_to_cloud",
            config["package"]
        ]

        print(f"  Running: {' '.join(cmd)}")
        print()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(f"  [OK] Successfully deployed {config['name']}")
            print()

            # Parse output for resource ID (basic parsing)
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'Resource name' in line or 'resource_name' in line:
                    print(f"  {line}")

            deployed_agents.append({
                "name": config['name'],
                "package": config['package'],
                "endpoint": config['endpoint'],
                "status": "success"
            })
        else:
            print(f"  [FAILED] Deployment failed for {config['name']}")
            print(f"  Error: {result.stderr}")
            deployed_agents.append({
                "name": config['name'],
                "status": "failed",
                "error": result.stderr
            })

        print()

        # Wait between deployments
        if idx < len(agents_config):
            print("  Waiting 15 seconds before next deployment...")
            time.sleep(15)
            print()

    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] Deployment timed out after 5 minutes")
        deployed_agents.append({
            "name": config['name'],
            "status": "timeout"
        })
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        deployed_agents.append({
            "name": config['name'],
            "status": "error",
            "error": str(e)
        })

print()
print("=" * 80)
print("DEPLOYMENT SUMMARY")
print("=" * 80)
print()

success_count = sum(1 for a in deployed_agents if a.get("status") == "success")
print(f"Successfully deployed: {success_count}/{len(agents_config)} agents")
print()

for agent in deployed_agents:
    status_icon = "✅" if agent.get("status") == "success" else "❌"
    print(f"{status_icon} {agent['name']}")
    if agent.get("status") == "success":
        print(f"   Package: {agent.get('package')}")
        print(f"   OTEL Endpoint: {agent.get('endpoint')}")
    else:
        print(f"   Status: {agent.get('status')}")
        if agent.get('error'):
            print(f"   Error: {agent.get('error')[:100]}")
    print()

if success_count > 0:
    print("=" * 80)
    print("TELEMETRY ARCHITECTURE")
    print("=" * 80)
    print()
    print("portal26GCPLocal:")
    print("  Agent → ngrok → Local Collector → Portal26 + Local Files")
    print()
    print("portal26GCPTel:")
    print("  Agent → Portal26 Cloud (direct)")
    print()
    print("View agents:")
    print(f"  https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={PROJECT_ID}")
    print()

print("=" * 80)
