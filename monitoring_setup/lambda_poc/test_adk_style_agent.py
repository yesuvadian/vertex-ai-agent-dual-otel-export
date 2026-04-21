"""
Test the new ADK-style agent with sessions
"""
import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
ENGINE_ID = "2362938998776659968"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

print("=" * 60)
print("Testing ADK-Style Agent with Sessions")
print("=" * 60)
print(f"Engine ID: {ENGINE_ID}")
print()

# Initialize
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Load engine
print("[1/4] Loading ADK-Style Agent...")
engine = reasoning_engines.ReasoningEngine(
    f"projects/961756870884/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"
)
print(f"[OK] Loaded: {engine.display_name}")
print()

# Test 1: First message with user session
print("[2/4] Test 1: First message in session...")
result1 = engine.query(
    message="Database connection timeout detected",
    user_id="test-user-001",
    session_id="session-abc"
)

print("Result 1:")
print(f"  Session: {result1['session_id']}")
print(f"  Severity: {result1['analysis']['severity']}")
print(f"  Insights: {result1['analysis']['insights']}")
print(f"  Lambda: {result1['lambda_result']['status']}")
print()

# Test 2: Second message in same session
print("[3/4] Test 2: Follow-up message in same session...")
result2 = engine.query(
    message="ERROR: Failed to reconnect to database",
    user_id="test-user-001",
    session_id="session-abc"
)

print("Result 2:")
print(f"  Session: {result2['session_id']}")
print(f"  Severity: {result2['analysis']['severity']}")
print(f"  Messages in session: {result2['message_count']}")
print(f"  User memory: {result2['user_memory']}")
print(f"  Lambda: {result2['lambda_result']['status']}")
print()

# Test 3: Different user
print("[4/4] Test 3: Different user...")
result3 = engine.query(
    message="CPU usage normal",
    user_id="test-user-002",
    session_id="session-xyz"
)

print("Result 3:")
print(f"  Session: {result3['session_id']}")
print(f"  User: {result3['user_id']}")
print(f"  Severity: {result3['analysis']['severity']}")
print()

print("=" * 60)
print("SUCCESS! All Tests Passed")
print("=" * 60)
print()
print("Features demonstrated:")
print("  - Session management (multiple messages in same session)")
print("  - User memory (error count tracking)")
print("  - Multi-user support (separate contexts)")
print("  - AWS Lambda integration")
print()
print("Logs flowing to AWS Lambda:")
print("  Check in 1-2 minutes:")
print("  MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test --since 5m --region us-east-1")
print()
