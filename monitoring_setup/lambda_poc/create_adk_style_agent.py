"""
Create an ADK-style agent similar to basic-gcp-agent-working
With sessions, memory, and AWS Lambda integration
"""
import vertexai
from vertexai.preview import reasoning_engines
import requests
import base64
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
AWS_LAMBDA_URL = "https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

print("=" * 60)
print("Creating ADK-Style Agent with Sessions")
print("=" * 60)
print(f"Project: {PROJECT_ID}")
print()

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)


class ADKStyleMonitoringAgent:
    """
    ADK-style agent with sessions, memory, and streaming capabilities
    Similar to basic-gcp-agent-working
    """

    def __init__(self):
        self.aws_lambda_url = AWS_LAMBDA_URL
        self.project_id = PROJECT_ID
        self.sessions = {}  # In-memory session storage
        self.memories = {}  # In-memory user memories

    def create_session(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session for a user"""
        if session_id is None:
            session_id = f"session-{datetime.utcnow().timestamp()}"

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],
            "state": {}
        }

        if user_id not in self.sessions:
            self.sessions[user_id] = {}

        self.sessions[user_id][session_id] = session
        print(f"[AGENT] Created session: {session_id} for user: {user_id}")

        return session

    def get_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get an existing session"""
        return self.sessions.get(user_id, {}).get(session_id)

    def add_to_memory(self, user_id: str, key: str, value: Any):
        """Add information to user memory"""
        if user_id not in self.memories:
            self.memories[user_id] = {}

        self.memories[user_id][key] = value
        print(f"[AGENT] Added to memory for {user_id}: {key}")

    def get_memory(self, user_id: str) -> Dict[str, Any]:
        """Get user memory"""
        return self.memories.get(user_id, {})

    def analyze_message(self, message_data: str, user_id: str) -> Dict[str, Any]:
        """Analyze message with context from user memory"""
        print(f"[AGENT] Analyzing for user: {user_id}")

        # Get user context from memory
        user_memory = self.get_memory(user_id)

        analysis = {
            "severity": "INFO",
            "category": "info",
            "anomaly_detected": False,
            "insights": "Normal monitoring data",
            "recommended_action": "forward",
            "timestamp": datetime.utcnow().isoformat(),
            "user_context": user_memory
        }

        message_lower = message_data.lower()

        if any(kw in message_lower for kw in ['error', 'exception', 'failed', 'critical']):
            analysis.update({
                "severity": "HIGH",
                "category": "error",
                "anomaly_detected": True,
                "insights": "Error detected - immediate attention required",
                "recommended_action": "alert_and_forward"
            })

            # Update memory with error count
            error_count = user_memory.get("error_count", 0) + 1
            self.add_to_memory(user_id, "error_count", error_count)
            self.add_to_memory(user_id, "last_error", message_data[:100])

        elif any(kw in message_lower for kw in ['warning', 'warn']):
            analysis.update({
                "severity": "MEDIUM",
                "category": "warning",
                "insights": "Warning detected"
            })

        print(f"[AGENT] Analysis: {analysis['severity']} - {analysis['insights']}")
        return analysis

    def forward_to_lambda(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Forward to AWS Lambda"""
        print(f"[AGENT] Forwarding to Lambda")

        try:
            response = requests.post(
                self.aws_lambda_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            return {
                "status": "success",
                "lambda_status_code": response.status_code,
                "lambda_response": response.json() if response.status_code == 200 else response.text[:200]
            }

        except Exception as e:
            print(f"[AGENT] Lambda error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def stream_query(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process query with streaming-style response (simulated)
        Similar to basic-gcp-agent-working's stream_query
        """
        print(f"[{datetime.utcnow().isoformat()}] === Stream Query ===")
        print(f"[AGENT] User: {user_id}, Session: {session_id}")

        # Get or create session
        if session_id:
            session = self.get_session(user_id, session_id)
            if not session:
                session = self.create_session(user_id, session_id)
        else:
            session = self.create_session(user_id)
            session_id = session["session_id"]

        # Add message to session
        session["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Analyze message
        analysis = self.analyze_message(message, user_id)

        # Create enriched message
        encoded = base64.b64encode(message.encode()).decode()
        enriched_message = {
            "message": {
                "data": encoded,
                "messageId": f"{session_id}-msg-{len(session['messages'])}",
                "publishTime": datetime.utcnow().isoformat() + "Z"
            },
            "ai_analysis": {
                "analysis": analysis,
                "session_id": session_id,
                "user_id": user_id,
                "agent_type": "adk-style-agent",
                "project_id": self.project_id
            }
        }

        # Forward to Lambda
        lambda_result = self.forward_to_lambda(enriched_message)

        # Stream events (simulated streaming)
        events = [
            {"type": "session_start", "session_id": session_id},
            {"type": "analysis", "data": analysis},
            {"type": "lambda_forward", "data": lambda_result},
            {
                "type": "response",
                "data": {
                    "status": "success",
                    "session_id": session_id,
                    "user_id": user_id,
                    "analysis": analysis,
                    "lambda_result": lambda_result,
                    "message_count": len(session["messages"]),
                    "user_memory": self.get_memory(user_id)
                }
            }
        ]

        # Add response to session
        session["messages"].append({
            "role": "assistant",
            "content": json.dumps(analysis),
            "timestamp": datetime.utcnow().isoformat()
        })

        print(f"[AGENT] Stream complete: {len(events)} events")
        return events

    def query(self, **kwargs) -> Dict[str, Any]:
        """
        Entry point for direct queries (non-streaming)
        """
        message = kwargs.get('message', '')
        user_id = kwargs.get('user_id', 'default-user')
        session_id = kwargs.get('session_id')

        # If message is dict (Pub/Sub format)
        if isinstance(message, dict):
            encoded_data = message.get('data', '')
            try:
                decoded = base64.b64decode(encoded_data).decode('utf-8')
            except:
                decoded = str(message)
            message = decoded

        # Process with streaming
        events = self.stream_query(message, user_id, session_id)

        # Return final response
        return events[-1]["data"]


# Create and deploy
print("[1/2] Creating ADK-Style Agent...")

agent = ADKStyleMonitoringAgent()

engine = reasoning_engines.ReasoningEngine.create(
    agent,
    requirements=[
        "google-cloud-aiplatform>=1.38.0",
        "requests>=2.31.0",
    ],
    display_name="adk-style-monitoring-agent",
    description="ADK-style agent with sessions, memory, streaming, and AWS Lambda integration",
    extra_packages=[],
)

print()
print("[2/2] ADK-Style Agent deployed!")
print()
print("=" * 60)
print("Deployment Complete")
print("=" * 60)
print()
print(f"Engine ID: {engine.resource_name}")
print(f"Display Name: adk-style-monitoring-agent")
print()
print("Features:")
print("  - Session management (multi-turn conversations)")
print("  - User memory (context retention)")
print("  - Stream-style queries")
print("  - AWS Lambda integration")
print("  - Automatic log capture to Cloud Logging")
print()
print("Test with sessions:")
print('  result = engine.query(')
print('      message="Test ERROR",')
print('      user_id="user-001",')
print('      session_id="session-abc"')
print('  )')
print()
print("Logs automatically flow:")
print("  Reasoning Engine -> Cloud Logging -> Pub/Sub -> AWS Lambda -> Portal26")
print()
