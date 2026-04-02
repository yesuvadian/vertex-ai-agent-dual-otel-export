"""
Query gcp_traces_agent to generate traces in GCP Cloud Trace
"""
import requests
from google.auth import default
from google.auth.transport.requests import Request

PROJECT_ID = "agentic-ai-integration-490716"
REGION = "us-central1"

# We need the agent ID - check Console for gcp_traces_agent ID
# For now, we'll list agents first

def get_access_token():
    """Get Google Cloud access token"""
    credentials, project = default()
    credentials.refresh(Request())
    return credentials.token

def list_agents():
    """List all deployed agents to find gcp_traces_agent"""
    token = get_access_token()

    endpoint = f"https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/reasoningEngines"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("Fetching list of deployed agents...")
    response = requests.get(endpoint, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        agents = data.get('reasoningEngines', [])

        print(f"\nFound {len(agents)} agent(s):")
        print("-" * 70)

        for agent in agents:
            name = agent.get('name', '')
            agent_id = name.split('/')[-1]
            display_name = agent.get('displayName', 'N/A')
            create_time = agent.get('createTime', 'N/A')

            print(f"Display Name: {display_name}")
            print(f"Agent ID: {agent_id}")
            print(f"Created: {create_time}")
            print(f"Full Name: {name}")
            print("-" * 70)

            # Check if this is gcp_traces_agent
            if 'gcp_traces_agent' in display_name.lower() or 'gcp_traces' in name.lower():
                print(f"[OK] Found gcp_traces_agent!")
                return agent_id

        return None
    else:
        print(f"[ERROR] Failed to list agents: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def query_agent(agent_id, query):
    """Query the agent to generate traces"""
    token = get_access_token()

    # Try the query endpoint
    endpoint = f"https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/reasoningEngines/{agent_id}:query"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": query
    }

    print(f"\nSending query to agent {agent_id}...")
    print(f"Query: {query}")

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=120)

        if response.status_code == 200:
            result = response.json()
            print("\n[OK] Agent responded!")
            print(f"Response: {result}")
            return True
        else:
            print(f"\n[ERROR] Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        return False

def main():
    print("=" * 70)
    print("Query gcp_traces_agent to Generate GCP Cloud Traces")
    print("=" * 70)
    print()

    # Find gcp_traces_agent
    agent_id = list_agents()

    if not agent_id:
        print("\n[WARNING] gcp_traces_agent not found in list")
        print("\nManual verification:")
        print("1. Go to: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716")
        print("2. Find gcp_traces_agent")
        print("3. Click on it and note the Agent ID from URL")
        print("4. Query it via Console UI")
        return

    # Query the agent
    test_query = "What is the weather in Tokyo?"
    success = query_agent(agent_id, test_query)

    if success:
        print("\n" + "=" * 70)
        print("Traces Generated!")
        print("=" * 70)
        print("\nView traces in GCP Cloud Trace:")
        print(f"1. Go to: https://console.cloud.google.com/traces?project={PROJECT_ID}")
        print("2. Filter by:")
        print("   - Service: gcp_traces_agent")
        print("   - Time: Last 15 minutes")
        print("3. Look for your query: 'What is the weather in Tokyo?'")
        print()

if __name__ == "__main__":
    main()
