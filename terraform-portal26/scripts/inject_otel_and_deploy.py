#!/usr/bin/env python3
"""
Inject OTEL module into agent and deploy to Vertex AI Agent Engine.
Enables Portal 26 telemetry for agents without modifying their core code.
"""
import argparse
import shutil
import tempfile
import os
import sys
import vertexai
from vertexai import agent_engines
from pathlib import Path


def inject_otel_import(agent_file: str):
    """Add otel_portal26 import to agent.py if not present."""

    with open(agent_file, 'r') as f:
        content = f.read()

    # Check if already has import
    if "import otel_portal26" in content:
        print(f"[INJECT] OTEL import already present in {agent_file}")
        return False

    lines = content.split('\n')

    # Find insertion point (after module docstring, before other imports)
    insert_pos = 0
    in_docstring = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Handle docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if in_docstring:
                in_docstring = False
                insert_pos = i + 1
            else:
                in_docstring = True

        # First non-comment, non-docstring line
        if not in_docstring and stripped and not stripped.startswith('#'):
            if not (stripped.startswith('"""') or stripped.startswith("'''")):
                insert_pos = i
                break

    # Insert import
    lines.insert(insert_pos, "import otel_portal26  # Portal 26 telemetry")

    with open(agent_file, 'w') as f:
        f.write('\n'.join(lines))

    print(f"[INJECT] ✓ Added OTEL import to {agent_file}")
    return True


def deploy_agent_with_portal26(
    agent_name: str,
    source_dir: str,
    display_name: str,
    portal26_endpoint: str,
    service_name: str,
    project_id: str,
    location: str
):
    """Deploy agent with Portal 26 OTEL integration."""

    print(f"\n{'='*60}")
    print(f"Deploying {agent_name} with Portal 26")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Portal 26: {portal26_endpoint}")
    print(f"Service: {service_name}")

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n[DEPLOY] Preparing agent in {temp_dir}")

        # Copy agent source
        for item in os.listdir(source_dir):
            src = os.path.join(source_dir, item)
            dst = os.path.join(temp_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        # Copy OTEL module
        otel_module = Path(__file__).parent.parent / "otel_portal26.py"
        shutil.copy2(otel_module, os.path.join(temp_dir, "otel_portal26.py"))
        print(f"[DEPLOY] ✓ Copied otel_portal26.py")

        # Inject import into agent.py
        agent_file = os.path.join(temp_dir, "agent.py")
        if os.path.exists(agent_file):
            inject_otel_import(agent_file)
        else:
            print(f"[DEPLOY] ⚠️  No agent.py found in {source_dir}")
            return False

        # Import agent
        sys.path.insert(0, temp_dir)
        try:
            from agent import root_agent
        except ImportError as e:
            print(f"[DEPLOY] ❌ Failed to import agent: {e}")
            return False

        # Initialize Vertex AI
        print(f"\n[DEPLOY] Connecting to Vertex AI...")
        vertexai.init(project=project_id, location=location)

        # Deploy to Agent Engine
        print(f"[DEPLOY] Deploying to Vertex AI Agent Engine...")

        try:
            deployed = agent_engines.create(
                agent_engine=root_agent,
                extra_packages=[temp_dir],
                requirements=[
                    "google-adk>=1.17.0",
                    "opentelemetry-instrumentation-google-genai>=0.4b0",
                    "opentelemetry-exporter-gcp-logging",
                    "opentelemetry-exporter-gcp-monitoring",
                    "opentelemetry-exporter-otlp-proto-http",
                    "opentelemetry-exporter-otlp-proto-grpc",
                    "opentelemetry-instrumentation-vertexai>=2.0b0",
                ],
                display_name=display_name,
                description=f"{display_name} with Portal 26 telemetry",
                env_vars={
                    "OTEL_EXPORTER_OTLP_ENDPOINT": portal26_endpoint,
                    "OTEL_SERVICE_NAME": service_name,
                    "OTEL_TRACES_EXPORTER": "otlp",
                    "OTEL_METRICS_EXPORTER": "otlp",
                    "OTEL_LOGS_EXPORTER": "otlp",
                    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
                    "GOOGLE_GENAI_USE_VERTEXAI": "true",
                }
            )

            agent_id = deployed.resource_name.split('/')[-1]

            print(f"\n{'='*60}")
            print(f"✅ DEPLOYMENT SUCCESSFUL")
            print(f"{'='*60}")
            print(f"Agent ID: {agent_id}")
            print(f"Resource: {deployed.resource_name}")
            print(f"Display Name: {deployed.display_name}")
            print(f"\n📊 Portal 26 Telemetry:")
            print(f"  Endpoint: {portal26_endpoint}")
            print(f"  Service: {service_name}")
            print(f"  Traces: {portal26_endpoint}/v1/traces")
            print(f"  Logs: {portal26_endpoint}/v1/logs")
            print(f"  Metrics: {portal26_endpoint}/v1/metrics")
            print(f"\n🧪 Test with:")
            print(f"  python3 query_agent.py {agent_id} \"test query\"")
            print(f"{'='*60}\n")

            return True

        except Exception as e:
            print(f"\n[DEPLOY] ❌ Deployment failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deploy Vertex AI agent with Portal 26 integration"
    )
    parser.add_argument("--agent-name", required=True, help="Agent identifier")
    parser.add_argument("--source-dir", required=True, help="Path to agent source code")
    parser.add_argument("--display-name", required=True, help="Agent display name")
    parser.add_argument("--portal26-endpoint", required=True, help="Portal 26 OTEL endpoint")
    parser.add_argument("--service-name", required=True, help="OTEL service name")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--location", default="us-central1", help="GCP location")

    args = parser.parse_args()

    success = deploy_agent_with_portal26(
        agent_name=args.agent_name,
        source_dir=args.source_dir,
        display_name=args.display_name,
        portal26_endpoint=args.portal26_endpoint,
        service_name=args.service_name,
        project_id=args.project_id,
        location=args.location
    )

    sys.exit(0 if success else 1)
