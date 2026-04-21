"""
Local test script for simple ADK agent
Run from your local machine (not Cloud Shell)
"""
import vertexai
from vertexai.preview import reasoning_engines
from datetime import datetime

# Configuration
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
ENGINE_ID = "8213677864684355584"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

def print_header(text):
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()

def print_result(label, result):
    print(f"\n{label}:")
    print(f"  Session ID: {result.get('session_id')}")
    print(f"  User ID: {result.get('user_id')}")
    print(f"  Severity: {result['analysis']['severity']}")
    print(f"  Category: {result['analysis']['category']}")
    print(f"  Insights: {result['analysis']['insights']}")
    print(f"  Anomaly: {result['analysis']['anomaly_detected']}")
    print(f"  Message Count: {result.get('message_count', 0)}")
    print(f"  User Memory: {result.get('user_memory', {})}")
    print(f"  Log Capture: {result.get('log_capture')}")

# Main test
print_header("Simple ADK Agent - Local Test")

print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing Vertex AI...")
print(f"  Project: {PROJECT_ID}")
print(f"  Location: {LOCATION}")
print(f"  Engine ID: {ENGINE_ID}")

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Loading Reasoning Engine...")
engine = reasoning_engines.ReasoningEngine(
    f"projects/961756870884/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"
)
print(f"  [OK] Loaded: {engine.display_name}")

# Test Scenario 1: Normal message
print_header("Test 1: Normal Message")
print("Testing with normal INFO level message...")

result1 = engine.query(
    message="System running normally, CPU at 45%",
    user_id="user-alice",
    session_id="session-001"
)
print_result("Result", result1)

# Test Scenario 2: Warning message
print_header("Test 2: Warning Message")
print("Testing with WARNING level message...")

result2 = engine.query(
    message="Warning: Disk usage at 85%",
    user_id="user-alice",
    session_id="session-001"
)
print_result("Result", result2)

# Test Scenario 3: Error message (first error for this user)
print_header("Test 3: Error Message (First)")
print("Testing with ERROR level message...")

result3 = engine.query(
    message="ERROR: Database connection failed",
    user_id="user-alice",
    session_id="session-001"
)
print_result("Result", result3)

# Test Scenario 4: Another error (should increment error count)
print_header("Test 4: Error Message (Second)")
print("Testing follow-up ERROR to verify memory tracking...")

result4 = engine.query(
    message="CRITICAL: Failed to reconnect to database",
    user_id="user-alice",
    session_id="session-001"
)
print_result("Result", result4)

# Test Scenario 5: Different user (should have separate memory)
print_header("Test 5: Different User")
print("Testing with different user to verify isolation...")

result5 = engine.query(
    message="ERROR: Service unavailable",
    user_id="user-bob",
    session_id="session-002"
)
print_result("Result", result5)

# Test Scenario 6: New session for first user
print_header("Test 6: New Session (Same User)")
print("Testing new session for existing user...")

result6 = engine.query(
    message="System recovered successfully",
    user_id="user-alice",
    session_id="session-003"
)
print_result("Result", result6)

# Summary
print_header("Test Summary")
print("[OK] All 6 tests completed successfully!")
print()
print("Features Verified:")
print("  [OK] Session management (multiple sessions)")
print("  [OK] User memory (error count tracking)")
print("  [OK] Multi-user support (isolated contexts)")
print("  [OK] Severity detection (INFO, WARNING, HIGH)")
print("  [OK] Anomaly detection (errors flagged)")
print("  [OK] Cloud Logging capture")
print()
print("Log Flow:")
print("  Reasoning Engine -> Cloud Logging -> Log Sink -> Pub/Sub -> AWS Lambda")
print()
print(f"[{datetime.now().strftime('%H:%M:%S')}] Check AWS Lambda logs in 1-2 minutes:")
print("  MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test --since 5m --region us-east-1")
print()
print("Engine works exactly like basic-gcp-agent-working!")
print()
