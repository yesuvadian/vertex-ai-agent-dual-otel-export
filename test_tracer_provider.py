import vertexai
from vertexai.preview import reasoning_engines
import requests
import google.auth
import google.auth.transport.requests
import time

vertexai.init(project="agentic-ai-integration-490716", location="us-central1")

# Get auth token
creds, project = google.auth.default()
auth_req = google.auth.transport.requests.Request()
creds.refresh(auth_req)
token = creds.token

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

agents = [
    ("2658127084508938240", "portal26_ngrok_agent", "test_tracer_ngrok"),
    ("7483734085236424704", "portal26_otel_agent", "test_tracer_otel"),
]

print("Testing agents with trace.set_tracer_provider() approach...")
print("="*80)

for agent_id, name, user_id in agents:
    print(f"\n🧪 Testing {name} (ID: {agent_id})")
    print("-"*80)

    try:
        agent = reasoning_engines.ReasoningEngine(agent_id)
        session = agent.create_session(user_id=user_id)
        session_id = session.get("id", "")
        print(f"✓ Session created: {session_id}")

        url = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/{agent_id}:streamQuery"

        data = {
            "input": {
                "user_id": user_id,
                "session_id": session_id,
                "message": "What's the time in New York?"
            }
        }

        print(f"✓ Calling agent...")
        response = requests.post(url, json=data, headers=headers, stream=True, timeout=30)

        if response.status_code == 200:
            text_found = False
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if '"text"' in decoded and not text_found:
                        import json
                        try:
                            event = json.loads(decoded)
                            if 'content' in event and 'parts' in event['content']:
                                for part in event['content']['parts']:
                                    if 'text' in part:
                                        print(f"✓ Response: {part['text']}")
                                        text_found = True
                                        break
                        except:
                            pass
            print(f"✅ Agent executed successfully")
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

    time.sleep(2)

print(f"\n{'='*80}")
print("Tests complete. Checking for telemetry...")
print(f"{'='*80}")
