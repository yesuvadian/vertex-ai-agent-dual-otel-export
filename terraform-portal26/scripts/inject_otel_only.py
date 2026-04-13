#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inject OTEL module into agent WITHOUT deploying.
Creates a new directory with _injected suffix containing the modified agent.
"""
import argparse
import shutil
import os
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def inject_otel_import(agent_file: str):
    """Add otel_portal26 import to agent.py if not present."""

    with open(agent_file, 'r', encoding='utf-8') as f:
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
    lines.insert(insert_pos, "import otel_portal26  # Portal 26 telemetry - injected by Terraform")

    with open(agent_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"[INJECT] [OK] Added OTEL import to {agent_file}")
    return True


def inject_agent(
    agent_name: str,
    source_dir: str,
    portal26_endpoint: str,
    service_name: str
):
    """Inject OTEL into agent without deploying."""

    print(f"\n{'='*60}")
    print(f"Injecting OTEL into {agent_name}")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Portal 26: {portal26_endpoint}")
    print(f"Service: {service_name}")

    # Create output directory
    output_dir = f"{source_dir}_injected"

    # Remove existing if present
    if os.path.exists(output_dir):
        print(f"\n[CLEAN] Removing existing {output_dir}")
        shutil.rmtree(output_dir)

    print(f"\n[INJECT] Creating {output_dir}")

    # Copy agent source
    shutil.copytree(source_dir, output_dir)
    print(f"[INJECT] ✓ Copied agent source")

    # Copy OTEL module
    otel_module = Path(__file__).parent.parent / "otel_portal26.py"
    shutil.copy2(otel_module, os.path.join(output_dir, "otel_portal26.py"))
    print(f"[INJECT] ✓ Copied otel_portal26.py")

    # Inject import into agent.py
    agent_file = os.path.join(output_dir, "agent.py")
    if os.path.exists(agent_file):
        inject_otel_import(agent_file)
    else:
        print(f"[ERROR] No agent.py found in {output_dir}")
        return False

    # Create or update .env file
    env_file = os.path.join(output_dir, ".env")
    env_content = f"""# Portal26 OTEL Configuration (Injected by Terraform)
OTEL_EXPORTER_OTLP_ENDPOINT={portal26_endpoint}
OTEL_SERVICE_NAME={service_name}
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Multi-tenant attributes
PORTAL26_TENANT_ID=tenant1
PORTAL26_USER_ID=relusys_terraform
AGENT_TYPE={agent_name}
"""

    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    print(f"[INJECT] ✓ Created .env configuration")

    # Create injection report
    report_file = os.path.join(output_dir, "INJECTION_REPORT.txt")
    report = f"""Portal26 OTEL Injection Report
{'='*60}

Agent: {agent_name}
Source: {source_dir}
Output: {output_dir}
Date: {Path(__file__).stat().st_mtime}

Configuration:
  Portal26 Endpoint: {portal26_endpoint}
  Service Name: {service_name}
  Tenant ID: tenant1
  User ID: relusys_terraform

Files Modified:
  ✓ agent.py - Added 'import otel_portal26'
  ✓ otel_portal26.py - Copied OTEL module
  ✓ .env - Created Portal26 config

Status: ✅ INJECTION COMPLETE (NOT DEPLOYED)

Next Steps:
  1. Test locally:
     cd {output_dir}
     export $(cat .env | xargs)
     python3 -c "import agent; print('OTEL loaded!')"

  2. Deploy manually when ready:
     - Via Vertex AI SDK
     - Via gcloud CLI
     - Via Console UI

  3. Verify telemetry:
     cd ../../portal26_otel_agent
     python3 pull_agent_logs.py
     grep "{service_name}" portal26_otel_agent_logs_*.jsonl
"""

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[INJECT] ✓ Created injection report")

    print(f"\n{'='*60}")
    print(f"✅ Injection complete!")
    print(f"{'='*60}")
    print(f"Output directory: {output_dir}")
    print(f"Report: {report_file}")
    print(f"\nAgent ready to deploy manually when needed.")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inject OTEL into agent without deploying"
    )
    parser.add_argument("--agent-name", required=True, help="Agent identifier")
    parser.add_argument("--source-dir", required=True, help="Agent source directory")
    parser.add_argument("--portal26-endpoint", required=True, help="Portal 26 endpoint")
    parser.add_argument("--service-name", required=True, help="Service name for telemetry")

    args = parser.parse_args()

    success = inject_agent(
        agent_name=args.agent_name,
        source_dir=args.source_dir,
        portal26_endpoint=args.portal26_endpoint,
        service_name=args.service_name
    )

    exit(0 if success else 1)
