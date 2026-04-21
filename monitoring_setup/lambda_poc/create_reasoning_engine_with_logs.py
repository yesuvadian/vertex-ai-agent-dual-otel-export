"""
Create fresh Reasoning Engine with AWS Lambda integration
Logs will be captured automatically to Cloud Logging -> AWS Lambda
"""
import vertexai
from vertexai.preview import reasoning_engines
import requests
import base64
import json
from datetime import datetime
from typing import Dict, Any

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
AWS_LAMBDA_URL = "https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

print("=" * 60)
print("Creating Reasoning Engine with Log Capture")
print("=" * 60)
print(f"Project: {PROJECT_ID}")
print(f"Lambda URL: {AWS_LAMBDA_URL}")
print()

# Initialize Vertex AI
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)


class MonitoringAgentWithLogs:
    """
    Monitoring agent that analyzes messages and forwards to AWS Lambda
    All logs automatically captured to Cloud Logging
    """

    def __init__(self):
        self.aws_lambda_url = AWS_LAMBDA_URL
        self.project_id = PROJECT_ID

    def analyze_message(self, message_data: str) -> Dict[str, Any]:
        """Analyze message for severity and anomalies"""
        print(f"[AGENT] Analyzing message: {message_data[:100]}")

        analysis = {
            "severity": "INFO",
            "category": "info",
            "anomaly_detected": False,
            "insights": "Normal monitoring data",
            "recommended_action": "forward",
            "timestamp": datetime.utcnow().isoformat()
        }

        message_lower = message_data.lower()

        if any(kw in message_lower for kw in ['error', 'exception', 'failed', 'critical', 'fatal']):
            analysis.update({
                "severity": "HIGH",
                "category": "error",
                "anomaly_detected": True,
                "insights": "Error detected - immediate attention required",
                "recommended_action": "alert_and_forward"
            })
            print(f"[AGENT] ALERT: High severity error detected!")

        elif any(kw in message_lower for kw in ['warning', 'warn']):
            analysis.update({
                "severity": "MEDIUM",
                "category": "warning",
                "insights": "Warning detected",
                "recommended_action": "monitor"
            })

        elif any(kw in message_lower for kw in ['slow', 'timeout', 'latency']):
            analysis.update({
                "severity": "MEDIUM",
                "category": "performance",
                "insights": "Performance issue detected",
                "recommended_action": "investigate"
            })

        print(f"[AGENT] Analysis complete: {analysis['severity']} - {analysis['insights']}")
        return analysis

    def forward_to_lambda(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Forward enriched message to AWS Lambda"""
        print(f"[AGENT] Forwarding to Lambda: {self.aws_lambda_url}")

        try:
            response = requests.post(
                self.aws_lambda_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            result = {
                "status": "success",
                "lambda_status_code": response.status_code,
                "lambda_response": response.json() if response.status_code == 200 else response.text[:200]
            }

            print(f"[AGENT] Lambda responded: {response.status_code}")
            return result

        except Exception as e:
            error_msg = f"Lambda error: {str(e)}"
            print(f"[AGENT] {error_msg}")
            return {"status": "error", "error": error_msg}

    def process_pubsub_message(self, pubsub_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing function
        This is called when querying the Reasoning Engine
        """
        timestamp = datetime.utcnow().isoformat()
        print(f"[{timestamp}] === Processing Message ===")

        # Extract message
        message = pubsub_data.get('message', {})
        encoded_data = message.get('data', '')
        message_id = message.get('messageId', 'unknown')
        publish_time = message.get('publishTime', 'unknown')

        print(f"[AGENT] Message ID: {message_id}")

        # Decode message data
        try:
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
            print(f"[AGENT] Decoded: {decoded_data}")
        except Exception as e:
            decoded_data = f"[Decode error: {str(e)}]"
            print(f"[AGENT] {decoded_data}")

        # Analyze
        analysis = self.analyze_message(decoded_data)

        # Create enriched message
        enriched_message = {
            "message": {
                "data": encoded_data,
                "messageId": message_id,
                "publishTime": publish_time
            },
            "ai_analysis": {
                "analysis": analysis,
                "reasoning_engine": "monitoring-agent-with-logs",
                "processing_time": timestamp,
                "project_id": self.project_id
            }
        }

        # Forward to Lambda
        lambda_result = self.forward_to_lambda(enriched_message)

        result = {
            "status": "success",
            "message_id": message_id,
            "decoded_message": decoded_data[:200],
            "analysis": analysis,
            "lambda_result": lambda_result,
            "timestamp": timestamp
        }

        print(f"[AGENT] Processing complete")
        return result

    def query(self, **kwargs) -> Dict[str, Any]:
        """Entry point for Reasoning Engine queries"""
        return self.process_pubsub_message(kwargs)


# Create and deploy
print("[1/2] Creating Reasoning Engine...")

agent = MonitoringAgentWithLogs()

engine = reasoning_engines.ReasoningEngine.create(
    agent,
    requirements=[
        "google-cloud-aiplatform>=1.38.0",
        "requests>=2.31.0",
    ],
    display_name="monitoring-agent-with-logs",
    description="Monitoring agent with AWS Lambda integration and automatic log capture",
    extra_packages=[],
)

print()
print("[2/2] Reasoning Engine deployed!")
print()
print("=" * 60)
print("Deployment Complete")
print("=" * 60)
print()
print(f"Engine ID: {engine.resource_name}")
print(f"Display Name: monitoring-agent-with-logs")
print()
print("Logs automatically flow:")
print("  1. Reasoning Engine -> Cloud Logging (automatic)")
print("  2. Cloud Logging -> Pub/Sub (via log sink)")
print("  3. Pub/Sub -> AWS Lambda (push subscription)")
print("  4. Lambda -> Portal26")
print()
print("Test it:")
print('  python test_reasoning_engine_new.py')
print()
print("Or query directly:")
print(f'  engine.query(message={{"data": "VGVzdA==", "messageId": "test-001"}})')
print()
