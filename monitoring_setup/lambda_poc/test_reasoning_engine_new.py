"""
Test the new Reasoning Engine with log capture
"""
import vertexai
from vertexai.preview import reasoning_engines
import base64

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
ENGINE_ID = "8019460130754002944"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

print("=" * 60)
print("Testing Reasoning Engine with Log Capture")
print("=" * 60)
print(f"Engine ID: {ENGINE_ID}")
print()

# Initialize
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Load engine
print("[1/3] Loading Reasoning Engine...")
engine = reasoning_engines.ReasoningEngine(
    f"projects/961756870884/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"
)
print(f"[OK] Loaded: {engine.display_name}")
print()

# Test with ERROR message
test_message = "Test message with ERROR in database connection"
encoded = base64.b64encode(test_message.encode()).decode()

print("[2/3] Sending test query...")
print(f"Message: {test_message}")
print()

result = engine.query(
    message={
        "data": encoded,
        "messageId": "new-engine-test-001",
        "publishTime": "2026-04-21T12:00:00Z"
    }
)

print("[3/3] Result:")
print("-" * 60)
import json
print(json.dumps(result, indent=2))
print("-" * 60)
print()

if result.get("status") == "success":
    print("=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print()
    print(f"Analysis: {result['analysis']['severity']} - {result['analysis']['insights']}")
    print(f"Lambda: {result['lambda_result']['status']}")
    print()
    print("Logs flowing to:")
    print("  1. Cloud Logging (check now)")
    print("  2. Pub/Sub topic: reasoning-engine-logs-topic")
    print("  3. AWS Lambda (check in 1-2 minutes)")
    print()
    print("Check Lambda logs:")
    print("  MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test --since 5m --region us-east-1")
    print()
else:
    print("[ERROR] Test failed")
