"""
Verify OTEL telemetry is being received and saved locally
"""
import os
import time
import json
from datetime import datetime

def check_local_receiver():
    """Check if local OTEL receiver is running"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 4318))
    sock.close()
    return result == 0

def check_otel_data_folder():
    """Check otel-data folder and recent files"""
    if not os.path.exists('otel-data'):
        return False, "otel-data folder not found"

    files = [f for f in os.listdir('otel-data') if f.startswith('traces_')]
    if not files:
        return False, "No trace files found"

    # Get most recent file
    files.sort(reverse=True)
    latest = files[0]

    # Check file age
    file_path = os.path.join('otel-data', latest)
    file_time = os.path.getmtime(file_path)
    age_minutes = (time.time() - file_time) / 60

    # Check file content
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            span_count = 0
            if 'resourceSpans' in data:
                for rs in data['resourceSpans']:
                    for ss in rs.get('scopeSpans', []):
                        span_count += len(ss.get('spans', []))

        return True, f"Latest: {latest} ({age_minutes:.1f} min ago, {span_count} spans)"
    except Exception as e:
        return False, f"Error reading file: {e}"

def main():
    print("=" * 70)
    print("OTEL Telemetry Verification")
    print("=" * 70)
    print()

    # Check local receiver
    print("1. Checking local OTEL receiver...")
    if check_local_receiver():
        print("   ✓ Local receiver is running on port 4318")
    else:
        print("   ✗ Local receiver is NOT running")
        print("   → Start it with: python local_otel_receiver.py")
    print()

    # Check otel-data folder
    print("2. Checking otel-data folder...")
    exists, message = check_otel_data_folder()
    if exists:
        print(f"   ✓ {message}")
    else:
        print(f"   ✗ {message}")
    print()

    # Instructions
    print("=" * 70)
    print("To test telemetry collection:")
    print("=" * 70)
    print()
    print("Option 1 - Google Console:")
    print("  1. Go to: https://console.cloud.google.com/vertex-ai/agents/agent-engines")
    print("  2. Click on portal26_ngrok_agent")
    print("  3. Go to Query tab")
    print("  4. Enter: 'What is 2+2?'")
    print("  5. Submit and wait for response")
    print("  6. Run this script again to see new traces")
    print()
    print("Option 2 - Test Script:")
    print("  python test_tracer_provider.py")
    print()
    print("Option 3 - Watch for new traces:")
    print("  dir otel-data (Windows)")
    print("  ls -lt otel-data (Linux/Mac)")
    print()

if __name__ == "__main__":
    main()
