"""
Deploy ADK Agent with Tools to Vertex AI
This agent will have Playground UI access
"""
import vertexai
from vertexai.preview import agents

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

print("=" * 60)
print("Deploying ADK Agent with Tools")
print("=" * 60)
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print()

# Initialize Vertex AI
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

print("[1/3] Creating ADK Agent...")

# Define agent with tools
agent = agents.Agent(
    model="gemini-2.0-flash-001",
    config=agents.AgentConfig(
        name="monitoring-agent-with-tools",
        description="GCP monitoring agent with tools for message analysis, Lambda forwarding, and log querying",
        instructions="""
You are a GCP monitoring agent that processes log messages and forwards them to AWS Lambda.

Your capabilities:
1. Analyze messages for severity (HIGH, MEDIUM, LOW, INFO)
2. Detect anomalies (errors, warnings, performance issues)
3. Forward messages to AWS Lambda with AI enrichment
4. Query GCP Cloud Logging for historical data
5. Calculate severity statistics

When a user provides a message:
1. Decode it if it's base64 encoded
2. Analyze it for severity and anomalies
3. Forward it to Lambda with your analysis
4. Report the results clearly

Always provide insights about what you found and what action you recommend.
""",
        tools=[
            # Tool 1: Analyze message
            agents.Tool(
                function_declarations=[
                    agents.FunctionDeclaration(
                        name="analyze_message",
                        description="Analyze a monitoring message for severity, category, and anomalies. Returns severity level (HIGH/MEDIUM/LOW/INFO), category (error/warning/metric/etc), anomaly detection status, insights, and recommended action.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "message_text": {
                                    "type": "string",
                                    "description": "The decoded text content to analyze"
                                }
                            },
                            "required": ["message_text"]
                        }
                    )
                ]
            ),
            # Tool 2: Forward to Lambda
            agents.Tool(
                function_declarations=[
                    agents.FunctionDeclaration(
                        name="forward_to_lambda",
                        description="Forward message to AWS Lambda with AI enrichment. Returns Lambda response status and any errors.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "message_data": {
                                    "type": "string",
                                    "description": "Base64 encoded message data"
                                },
                                "message_id": {
                                    "type": "string",
                                    "description": "Unique message identifier"
                                },
                                "publish_time": {
                                    "type": "string",
                                    "description": "ISO timestamp when message was published"
                                },
                                "analysis": {
                                    "type": "object",
                                    "description": "AI analysis results from analyze_message tool"
                                }
                            },
                            "required": ["message_data", "message_id", "publish_time", "analysis"]
                        }
                    )
                ]
            ),
            # Tool 3: Decode base64
            agents.Tool(
                function_declarations=[
                    agents.FunctionDeclaration(
                        name="decode_base64_message",
                        description="Decode base64 encoded message data to readable text.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "encoded_data": {
                                    "type": "string",
                                    "description": "Base64 encoded string to decode"
                                }
                            },
                            "required": ["encoded_data"]
                        }
                    )
                ]
            )
        ]
    )
)

print("[OK] Agent configuration created")
print()

print("[2/3] Deploying agent to Vertex AI...")
print("This may take 2-3 minutes...")
print()

try:
    # Deploy the agent
    deployed_agent = agent.create()

    print()
    print("[OK] Agent deployed successfully!")
    print()

    print("=" * 60)
    print("Deployment Complete!")
    print("=" * 60)
    print()
    print(f"Agent Name: {deployed_agent.display_name}")
    print(f"Agent ID: {deployed_agent.name}")
    print()
    print("Access Playground:")
    print(f"https://console.cloud.google.com/vertex-ai/agents/agent-engines/{deployed_agent.name.split('/')[-1]}/playground?project={PROJECT_ID}")
    print()
    print("Available Tools:")
    print("  1. analyze_message - Analyze severity and anomalies")
    print("  2. forward_to_lambda - Forward to AWS Lambda")
    print("  3. decode_base64_message - Decode base64 data")
    print()
    print("[3/3] Test in Playground:")
    print("  Message: 'Analyze this: ERROR in database connection'")
    print()
    print("Logs will automatically flow to:")
    print("  Cloud Logging -> Pub/Sub -> AWS Lambda -> Portal26")
    print()

except Exception as e:
    print(f"[ERROR] Deployment failed: {str(e)}")
    import traceback
    traceback.print_exc()
