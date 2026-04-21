"""
Test Vertex AI Reasoning Engine
Verify logs flow to AWS Lambda
"""
import vertexai
from vertexai.preview import reasoning_engines
import base64

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
REASONING_ENGINE_ID = "3783824681212051456"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

print("=" * 60)
print("Testing Vertex AI Reasoning Engine")
print("=" * 60)
print(f"Project: {PROJECT_ID}")
print(f"Engine ID: {REASONING_ENGINE_ID}")
print()

# Initialize Vertex AI
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

# Load Reasoning Engine
print("[1/3] Loading Reasoning Engine...")
engine = reasoning_engines.ReasoningEngine(
    f"projects/961756870884/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"
)
print("[OK] Engine loaded")
print()

# Test message with ERROR keyword (should trigger high severity)
test_message = "Test message with ERROR in monitoring data"
encoded_message = base64.b64encode(test_message.encode()).decode()

print("[2/3] Querying Reasoning Engine...")
print(f"Test message: {test_message}")
print()

try:
    result = engine.query(
        message={
            "data": encoded_message,
            "messageId": "test-123-error",
            "publishTime": "2026-04-21T10:30:00Z"
        }
    )

    print("[3/3] Result received:")
    print("-" * 60)
    import json
    print(json.dumps(result, indent=2))
    print("-" * 60)
    print()

    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    print("Logs will flow:")
    print("  1. Reasoning Engine → Cloud Logging (automatic)")
    print("  2. Cloud Logging → Pub/Sub (via log sink)")
    print("  3. Pub/Sub → AWS Lambda (via push subscription)")
    print()
    print("Wait 1-2 minutes, then check AWS Lambda logs:")
    print("  MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test --since 5m --region us-east-1")
    print()

except Exception as e:
    print(f"[ERROR] Query failed: {str(e)}")
    import traceback
    traceback.print_exc()
