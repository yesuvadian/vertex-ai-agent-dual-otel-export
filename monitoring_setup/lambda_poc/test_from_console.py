"""
Test Reasoning Engine via Python (simulates console test)
"""
import vertexai
from vertexai.preview import reasoning_engines
import base64
import json
from datetime import datetime

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
REASONING_ENGINE_ID = "3783824681212051456"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

print("=" * 60)
print("Testing Reasoning Engine - Console Simulation")
print("=" * 60)
print(f"Engine: {REASONING_ENGINE_ID}")
print()

# Initialize
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

# Load engine
print("[1/3] Loading Reasoning Engine...")
engine = reasoning_engines.ReasoningEngine(
    f"projects/961756870884/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"
)
print("[OK] Loaded")
print()

# Test message
test_message = "Test from GCP Console with ERROR"
encoded = base64.b64encode(test_message.encode()).decode()

print("[2/3] Sending test query...")
print(f"Message: {test_message}")
print(f"Message ID: console-test-001")
print()

# Query
result = engine.query(
    message={
        "data": encoded,
        "messageId": "console-test-001",
        "publishTime": datetime.utcnow().isoformat() + "Z"
    }
)

print("[3/3] Result:")
print("-" * 60)
print(json.dumps(result, indent=2))
print("-" * 60)
print()

# Check results
if result.get("status") == "success":
    analysis = result.get("analysis", {})
    lambda_result = result.get("lambda_result", {})

    print("=" * 60)
    print("SUCCESS - Full Flow Working!")
    print("=" * 60)
    print()
    print(f"AI Analysis:")
    print(f"  Severity: {analysis.get('severity')}")
    print(f"  Category: {analysis.get('category')}")
    print(f"  Anomaly: {analysis.get('anomaly_detected')}")
    print(f"  Insights: {analysis.get('insights')}")
    print()
    print(f"Lambda Forward:")
    print(f"  Status: {lambda_result.get('status')}")
    print(f"  HTTP Code: {lambda_result.get('lambda_status_code')}")
    print()
    print("Next: Check AWS Lambda logs")
    print("  chmod +x check_console_test.sh && ./check_console_test.sh")
    print()
else:
    print("[ERROR] Query failed")
    print(json.dumps(result, indent=2))
