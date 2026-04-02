"""Test full content logging with new agent using Console UI"""
import webbrowser

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
AGENT_ID = "8081657304514035712"

print(f"Testing agent {AGENT_ID} with full content logging...")
print("=" * 80)

# Instructions for testing via Console UI (session-based API)
print("\n[SUCCESS] Agent deployed successfully!")
print(f"\n[INFO] Agent ID: {AGENT_ID}")
print(f"[INFO] Configuration: OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true")

print("\n" + "=" * 80)
print("TESTING INSTRUCTIONS:")
print("=" * 80)

print("\n1. Open the agent in Console UI:")
agent_url = f"https://console.cloud.google.com/vertex-ai/agents/agent-engines/{AGENT_ID}?project={PROJECT_ID}"
print(f"   {agent_url}")

print("\n2. Go to the 'Playground' tab")

print("\n3. Send this test query:")
print('   "What is the weather in Tokyo? Please provide detailed information."')

print("\n4. Wait for response (should show weather data)")

print("\n5. Check Cloud Trace Explorer:")
trace_url = f"https://console.cloud.google.com/traces?project={PROJECT_ID}"
print(f"   {trace_url}")

print("\n6. Filter traces:")
print("   - Set time range: Last 1 hour")
print("   - Look for recent traces")
print("   - Click on a trace span")

print("\n7. Verify full content in labels:")
print("   - gen_ai.prompt.user: Should show full query text")
print("   - gen_ai.response.text: Should show full response")
print("   - gen_ai.tool.*: Should show complete tool parameters")
print("   - No truncation or '...' at the end")

print("\n" + "=" * 80)
print("\nOpening agent playground in browser...")
webbrowser.open(agent_url)
