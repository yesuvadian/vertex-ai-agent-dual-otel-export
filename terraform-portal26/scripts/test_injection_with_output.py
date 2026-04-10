#!/usr/bin/env python3
"""
Test OTEL injection and save the modified files to an output directory.
This version PERSISTS the modified agent so you can inspect it.
"""
import argparse
import shutil
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


def test_injection_with_output(source_dir: str, output_dir: str, portal26_endpoint: str, service_name: str):
    """Test injection and save modified files to output directory."""

    print(f"\n{'='*60}")
    print(f"Testing OTEL Injection (With Persistent Output)")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Portal 26: {portal26_endpoint}")
    print(f"Service: {service_name}")

    # Verify source agent exists
    source_agent_file = os.path.join(source_dir, "agent.py")
    if not os.path.exists(source_agent_file):
        print(f"\n[ERROR] No agent.py found in {source_dir}")
        return False

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n[SETUP] Created output directory: {output_dir}")

    # Copy agent source
    for item in os.listdir(source_dir):
        src = os.path.join(source_dir, item)
        dst = os.path.join(output_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    print(f"[COPY] [OK] Copied agent source to output directory")

    # Copy OTEL module
    otel_module = Path(__file__).parent.parent / "otel_portal26.py"
    shutil.copy2(otel_module, os.path.join(output_dir, "otel_portal26.py"))
    print(f"[COPY] [OK] Copied otel_portal26.py")

    # Save original agent for comparison
    original_agent = os.path.join(output_dir, "agent_original.py")
    shutil.copy2(os.path.join(output_dir, "agent.py"), original_agent)
    print(f"[BACKUP] [OK] Saved original as agent_original.py")

    # Inject import into agent.py
    agent_file = os.path.join(output_dir, "agent.py")
    inject_otel_import(agent_file)

    # Create environment variables file
    env_file = os.path.join(output_dir, "env_variables.txt")
    with open(env_file, 'w') as f:
        f.write("# Environment Variables for Vertex AI Deployment\n")
        f.write("# These would be set automatically during terraform apply\n\n")
        f.write(f"OTEL_EXPORTER_OTLP_ENDPOINT={portal26_endpoint}\n")
        f.write(f"OTEL_SERVICE_NAME={service_name}\n")
        f.write("OTEL_TRACES_EXPORTER=otlp\n")
        f.write("OTEL_METRICS_EXPORTER=otlp\n")
        f.write("OTEL_LOGS_EXPORTER=otlp\n")
        f.write("OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf\n")
        f.write("GOOGLE_GENAI_USE_VERTEXAI=true\n")
    print(f"[CREATE] [OK] Created env_variables.txt")

    # Create README
    readme_file = os.path.join(output_dir, "README.txt")
    with open(readme_file, 'w') as f:
        f.write("OTEL Injection Test Output\n")
        f.write("="*60 + "\n\n")
        f.write("This directory contains the result of OTEL injection.\n\n")
        f.write("Files:\n")
        f.write("------\n")
        f.write("- agent_original.py    : Original agent (unmodified)\n")
        f.write("- agent.py             : Modified agent (with OTEL import)\n")
        f.write("- otel_portal26.py     : OTEL module (injected)\n")
        f.write("- env_variables.txt    : Environment variables for deployment\n")
        f.write("- requirements.txt     : Python dependencies\n")
        f.write("- README.txt           : This file\n\n")
        f.write("What Changed:\n")
        f.write("-------------\n")
        f.write("Compare agent_original.py with agent.py to see the difference.\n")
        f.write("Only ONE line was added: import otel_portal26\n\n")
        f.write("Next Steps:\n")
        f.write("-----------\n")
        f.write("1. Review agent.py to verify the injection\n")
        f.write("2. Check env_variables.txt for Portal 26 configuration\n")
        f.write("3. If satisfied, use these files for Terraform deployment\n")
    print(f"[CREATE] [OK] Created README.txt")

    # Show comparison
    print(f"\n{'='*60}")
    print(f"COMPARISON")
    print(f"{'='*60}")

    with open(original_agent, 'r') as f:
        original_lines = f.readlines()

    with open(agent_file, 'r') as f:
        modified_lines = f.readlines()

    print("\nFirst 15 lines comparison:\n")
    print("ORIGINAL (agent_original.py):")
    print("-" * 40)
    for i, line in enumerate(original_lines[:15], 1):
        print(f"{i:3d} | {line.rstrip()}")

    print("\n\nMODIFIED (agent.py):")
    print("-" * 40)
    for i, line in enumerate(modified_lines[:15], 1):
        marker = " <-- ADDED" if "import otel_portal26" in line else ""
        print(f"{i:3d} | {line.rstrip()}{marker}")

    # List files
    print(f"\n{'='*60}")
    print(f"OUTPUT DIRECTORY CONTENTS")
    print(f"{'='*60}")
    print(f"Location: {os.path.abspath(output_dir)}\n")

    for item in sorted(os.listdir(output_dir)):
        item_path = os.path.join(output_dir, item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            print(f"  [FILE] {item:<25} ({size:,} bytes)")
        else:
            print(f"  [DIR]  {item}/")

    print(f"\n{'='*60}")
    print(f"[SUCCESS] INJECTION TEST COMPLETE")
    print(f"{'='*60}")
    print(f"\nOutput saved to: {os.path.abspath(output_dir)}")
    print(f"\nTo review:")
    print(f"  - Original:  {os.path.join(output_dir, 'agent_original.py')}")
    print(f"  - Modified:  {os.path.join(output_dir, 'agent.py')}")
    print(f"  - OTEL:      {os.path.join(output_dir, 'otel_portal26.py')}")
    print(f"  - Config:    {os.path.join(output_dir, 'env_variables.txt')}")
    print(f"\nThe original source in '{source_dir}' was NOT modified.")
    print(f"{'='*60}\n")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test OTEL injection and save output to directory"
    )
    parser.add_argument("--source-dir", required=True, help="Path to agent source code")
    parser.add_argument("--output-dir", required=True, help="Path to save modified files")
    parser.add_argument("--portal26-endpoint", required=True, help="Portal 26 OTEL endpoint")
    parser.add_argument("--service-name", default="test-agent", help="OTEL service name")

    args = parser.parse_args()

    success = test_injection_with_output(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        portal26_endpoint=args.portal26_endpoint,
        service_name=args.service_name
    )

    sys.exit(0 if success else 1)
