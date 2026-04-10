#!/usr/bin/env python3
"""
Test OTEL injection without deploying to Vertex AI.
Shows before/after of agent.py to verify injection works.
"""
import argparse
import shutil
import tempfile
import os
import sys
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

    print(f"[INJECT] [OK] Added OTEL import to {agent_file}")
    return True


def test_injection(source_dir: str, portal26_endpoint: str, service_name: str):
    """Test injection without deploying."""

    print(f"\n{'='*60}")
    print(f"Testing OTEL Injection (Dry Run)")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Portal 26: {portal26_endpoint}")
    print(f"Service: {service_name}")

    # Verify source agent exists
    source_agent_file = os.path.join(source_dir, "agent.py")
    if not os.path.exists(source_agent_file):
        print(f"\n[ERROR] No agent.py found in {source_dir}")
        return False

    # Show original agent
    print(f"\n{'='*60}")
    print(f"ORIGINAL AGENT (before injection)")
    print(f"{'='*60}")
    with open(source_agent_file, 'r') as f:
        original_content = f.read()
        print(original_content)

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n{'='*60}")
        print(f"Processing in temporary directory: {temp_dir}")
        print(f"{'='*60}")

        # Copy agent source
        for item in os.listdir(source_dir):
            src = os.path.join(source_dir, item)
            dst = os.path.join(temp_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        print(f"[TEST] [OK] Copied agent source")

        # Copy OTEL module
        otel_module = Path(__file__).parent.parent / "otel_portal26.py"
        shutil.copy2(otel_module, os.path.join(temp_dir, "otel_portal26.py"))
        print(f"[TEST] [OK] Copied otel_portal26.py")

        # Inject import into agent.py
        agent_file = os.path.join(temp_dir, "agent.py")
        inject_otel_import(agent_file)

        # Show modified agent
        print(f"\n{'='*60}")
        print(f"MODIFIED AGENT (after injection)")
        print(f"{'='*60}")
        with open(agent_file, 'r') as f:
            modified_content = f.read()
            print(modified_content)

        # Show diff
        print(f"\n{'='*60}")
        print(f"WHAT CHANGED")
        print(f"{'='*60}")
        original_lines = original_content.split('\n')
        modified_lines = modified_content.split('\n')

        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines), 1):
            if orig != mod:
                print(f"Line {i}:")
                print(f"  - (removed):  {orig if orig else '(empty)'}")
                print(f"  + (added):    {mod if mod else '(empty)'}")

        # Show environment variables that would be set
        print(f"\n{'='*60}")
        print(f"ENVIRONMENT VARIABLES (would be set in Vertex AI)")
        print(f"{'='*60}")
        env_vars = {
            "OTEL_EXPORTER_OTLP_ENDPOINT": portal26_endpoint,
            "OTEL_SERVICE_NAME": service_name,
            "OTEL_TRACES_EXPORTER": "otlp",
            "OTEL_METRICS_EXPORTER": "otlp",
            "OTEL_LOGS_EXPORTER": "otlp",
            "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
        }
        for key, value in env_vars.items():
            print(f"  {key}={value}")

        # List files in temp directory
        print(f"\n{'='*60}")
        print(f"FILES IN DEPLOYMENT PACKAGE")
        print(f"{'='*60}")
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                print(f"  [FILE] {item} ({size} bytes)")
            else:
                print(f"  [DIR]  {item}/")

        # Show otel_portal26.py snippet
        print(f"\n{'='*60}")
        print(f"OTEL MODULE (otel_portal26.py) - First 30 lines")
        print(f"{'='*60}")
        otel_file = os.path.join(temp_dir, "otel_portal26.py")
        with open(otel_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:30], 1):
                print(f"{i:3d}  {line.rstrip()}")
            if len(lines) > 30:
                print(f"... ({len(lines) - 30} more lines)")

        print(f"\n{'='*60}")
        print(f"[SUCCESS] INJECTION TEST SUCCESSFUL")
        print(f"{'='*60}")
        print(f"Summary:")
        print(f"  [OK] Agent source copied")
        print(f"  [OK] OTEL module injected")
        print(f"  [OK] Import statement added")
        print(f"  [OK] Environment variables defined")
        print(f"\nNote: No deployment to Vertex AI - this was a dry run only.")
        print(f"Temporary files cleaned up automatically.")
        print(f"{'='*60}\n")

        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test OTEL injection without deploying"
    )
    parser.add_argument("--source-dir", required=True, help="Path to agent source code")
    parser.add_argument("--portal26-endpoint", required=True, help="Portal 26 OTEL endpoint")
    parser.add_argument("--service-name", default="test-agent", help="OTEL service name")

    args = parser.parse_args()

    success = test_injection(
        source_dir=args.source_dir,
        portal26_endpoint=args.portal26_endpoint,
        service_name=args.service_name
    )

    sys.exit(0 if success else 1)
