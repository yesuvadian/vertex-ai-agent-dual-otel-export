"""
Test deployed agents properly using sessions
"""
import requests
import json
import subprocess
import time
import os

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"

AGENTS = {
    "portal26_ngrok_agent": {
        "id": "2658127084508938240",
        "query": "What is the weather in Bengaluru?"
    },
    "portal26_otel_agent": {
        "id": "7483734085236424704",
        "query": "What is the current time in Tokyo?"
    }
}

def get_access_token():
    """Get GCP access token"""
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", "gcloud auth print-access-token"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"[ERROR] Failed to get access token: {e}")
        return None

def call_agent_method(agent_id, method_name, input_data=None):
    """Call an agent method"""
    token = get_access_token()
    if not token:
        return None

    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{agent_id}:query"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # For ADK agents with sessions, use input directly
    payload = {"input": input_data or {}}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None

def test_agent(agent_name, agent_config):
    """Test a single agent"""
    print(f"\n{'='*70}")
    print(f"Testing {agent_name}")
    print(f"Agent ID: {agent_config['id']}")
    print('='*70)

    # For ADK agents, query directly with the input
    print(f"\nQuerying agent with: {agent_config['query']}")
    start_time = time.time()

    result = call_agent_method(
        agent_config['id'],
        "query",
        {"query": agent_config['query']}
    )

    elapsed = time.time() - start_time

    if result:
        print(f"\nResponse received in {elapsed:.2f}s:")
        print(json.dumps(result, indent=2))
        print(f"\n[OK] {agent_name} responded successfully")
        return True
    else:
        print(f"\n[FAIL] {agent_name} did not respond")
        return False

def check_local_receiver():
    """Check if local receiver is running and has recent data"""
    print("\n" + "="*70)
    print("Checking Local OTEL Receiver")
    print("="*70)

    # Check if receiver is running
    try:
        response = requests.get("http://localhost:4318", timeout=2)
        print("[OK] Local OTEL receiver is running on port 4318")
    except:
        print("[WARNING] Local OTEL receiver not responding on port 4318")
        print("         Start it with: python local_otel_receiver.py")
        return

    # Check otel-data folder
    otel_dir = "otel-data"
    if not os.path.exists(otel_dir):
        print(f"[WARNING] {otel_dir}/ directory not found")
        return

    files = sorted([f for f in os.listdir(otel_dir) if f.startswith('traces_')], reverse=True)

    if files:
        print(f"\n[OK] Found {len(files)} trace file(s) in {otel_dir}/")
        latest = files[0]
        file_path = os.path.join(otel_dir, latest)
        size = os.path.getsize(file_path)
        mtime = os.path.getmtime(file_path)
        age = (time.time() - mtime) / 60
        print(f"     Latest: {latest}")
        print(f"     Size: {size} bytes")
        print(f"     Age: {age:.1f} minutes")

        if age < 5:
            print(f"     [OK] File is recent (less than 5 minutes old)")
        else:
            print(f"     [INFO] File is {age:.1f} minutes old")
    else:
        print(f"[INFO] No trace files found yet in {otel_dir}/")

def main():
    print("="*70)
    print("Testing Deployed Vertex AI Agents with OTEL Export")
    print("="*70)
    print("\nThis will:")
    print("  1. Query both deployed agents")
    print("  2. Generate OTEL telemetry")
    print("  3. portal26_ngrok_agent -> sends to local receiver -> forwards to Portal26")
    print("  4. portal26_otel_agent -> sends directly to Portal26")
    print()

    results = {}

    # Test portal26_ngrok_agent
    results["ngrok"] = test_agent("portal26_ngrok_agent", AGENTS["portal26_ngrok_agent"])

    print("\nWaiting 5 seconds for telemetry to be collected...")
    time.sleep(5)

    # Test portal26_otel_agent
    results["otel"] = test_agent("portal26_otel_agent", AGENTS["portal26_otel_agent"])

    print("\nWaiting 5 seconds for telemetry to be processed...")
    time.sleep(5)

    # Check local receiver
    check_local_receiver()

    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"  portal26_ngrok_agent: {'PASS' if results.get('ngrok') else 'FAIL'}")
    print(f"  portal26_otel_agent:  {'PASS' if results.get('otel') else 'FAIL'}")
    print()

    if all(results.values()):
        print("[SUCCESS] All agents responded!")
        print("\nExpected OTEL Flow:")
        print("  portal26_ngrok_agent:")
        print("    Agent -> Ngrok -> Local Receiver -> otel-data/*.json")
        print("                                      -> Portal26 (https://otel-tenant1.portal26.in:4318)")
        print()
        print("  portal26_otel_agent:")
        print("    Agent -> Portal26 (https://otel-tenant1.portal26.in:4318) [direct]")
        print()
        print("Next steps:")
        print("  1. Check otel-data/ folder for new JSON files")
        print("  2. Check local receiver logs (if running in terminal)")
        print("  3. Check Portal26 dashboard for received traces")
    else:
        print("[WARNING] Some agents failed - check errors above")

    print("="*70)

if __name__ == "__main__":
    main()
