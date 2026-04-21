"""
Deploy Vertex AI Reasoning Engine for Pub/Sub -> Lambda integration
Captures logs automatically to Cloud Logging
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

# Initialize Vertex AI with staging bucket
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)


class PubSubToLambdaAgent:
    """
    Reasoning Engine Agent for processing Pub/Sub messages
    Analyzes messages and forwards to AWS Lambda
    """

    def __init__(self):
        self.aws_lambda_url = AWS_LAMBDA_URL
        self.project_id = PROJECT_ID

    def analyze_message(self, message_data: str) -> Dict[str, Any]:
        """
        Analyze message content for severity and anomalies

        Args:
            message_data: Decoded message content

        Returns:
            Analysis results
        """
        print(f"[REASONING ENGINE] Analyzing message: {message_data[:100]}")

        analysis = {
            "severity": "INFO",
            "category": "info",
            "anomaly_detected": False,
            "insights": "Normal monitoring data",
            "recommended_action": "forward",
            "timestamp": datetime.utcnow().isoformat()
        }

        message_lower = message_data.lower()

        # Error detection
        if any(keyword in message_lower for keyword in ['error', 'exception', 'failed', 'critical']):
            analysis["severity"] = "HIGH"
            analysis["category"] = "error"
            analysis["anomaly_detected"] = True
            analysis["insights"] = "Error detected - requires attention"
            analysis["recommended_action"] = "alert_and_forward"
            print("[REASONING ENGINE] ANOMALY: Error detected")

        # Warning detection
        elif any(keyword in message_lower for keyword in ['warning', 'warn']):
            analysis["severity"] = "MEDIUM"
            analysis["category"] = "warning"
            analysis["insights"] = "Warning detected"

        # Metric detection
        elif any(keyword in message_lower for keyword in ['metric', 'cpu', 'memory', 'disk', 'latency']):
            analysis["category"] = "metric"
            analysis["insights"] = "System metric data"

        return analysis

    def forward_to_lambda(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forward enriched message to AWS Lambda

        Args:
            message: Enriched message with analysis

        Returns:
            Forward result
        """
        print(f"[REASONING ENGINE] Forwarding to Lambda: {self.aws_lambda_url}")

        try:
            response = requests.post(
                self.aws_lambda_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            print(f"[REASONING ENGINE] Lambda response: {response.status_code}")

            result = {
                "status": "success",
                "lambda_status_code": response.status_code,
                "lambda_response": response.json() if response.status_code == 200 else response.text[:200]
            }

            return result

        except Exception as e:
            error_msg = f"Error forwarding to Lambda: {str(e)}"
            print(f"[REASONING ENGINE] {error_msg}")
            return {
                "status": "error",
                "error": error_msg
            }

    def process_pubsub_message(self, pubsub_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing function - called by Pub/Sub

        Args:
            pubsub_data: Pub/Sub message data

        Returns:
            Processing result
        """
        timestamp = datetime.utcnow().isoformat()
        print(f"[{timestamp}] === Reasoning Engine Processing Pub/Sub Message ===")

        # Extract message
        message = pubsub_data.get('message', {})
        encoded_data = message.get('data', '')
        message_id = message.get('messageId', 'unknown')
        publish_time = message.get('publishTime', 'unknown')

        print(f"[REASONING ENGINE] Message ID: {message_id}")
        print(f"[REASONING ENGINE] Publish Time: {publish_time}")

        # Decode message data
        try:
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
            print(f"[REASONING ENGINE] Decoded data: {decoded_data}")
        except Exception as e:
            decoded_data = f"[Decode error: {str(e)}]"
            print(f"[REASONING ENGINE] Decode error: {str(e)}")

        # AI Analysis
        analysis = self.analyze_message(decoded_data)
        print(f"[REASONING ENGINE] Analysis: {json.dumps(analysis, indent=2)}")

        # Create enriched message (keep Lambda-compatible format)
        enriched_message = {
            "message": {
                "data": encoded_data,
                "messageId": message_id,
                "publishTime": publish_time
            },
            "vertex_ai_enrichment": {
                "analysis": analysis,
                "reasoning_engine": "pubsub-to-lambda-agent",
                "processing_time": timestamp,
                "project_id": self.project_id
            }
        }

        # Forward to Lambda
        lambda_result = self.forward_to_lambda(enriched_message)

        result = {
            "status": "success",
            "message_id": message_id,
            "analysis": analysis,
            "lambda_result": lambda_result,
            "timestamp": timestamp
        }

        print(f"[REASONING ENGINE] Processing complete: {json.dumps(result, indent=2)}")

        return result

    def query(self, **kwargs) -> Dict[str, Any]:
        """
        Query method required by Reasoning Engine
        This is called when the engine receives a message
        """
        return self.process_pubsub_message(kwargs)


def deploy_reasoning_engine():
    """
    Deploy the Reasoning Engine to Vertex AI
    """
    print("=" * 60)
    print("Deploying Vertex AI Reasoning Engine")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Lambda URL: {AWS_LAMBDA_URL}")
    print()

    # Create the agent instance
    agent = PubSubToLambdaAgent()

    print("[1/2] Creating Reasoning Engine...")

    # Deploy as Reasoning Engine
    engine = reasoning_engines.ReasoningEngine.create(
        agent,
        requirements=[
            "google-cloud-aiplatform>=1.38.0",
            "requests>=2.31.0",
        ],
        display_name="pubsub-lambda-reasoning-engine",
        description="Processes GCP Pub/Sub messages, analyzes with AI, forwards to AWS Lambda",
        extra_packages=[],
    )

    print()
    print("[OK] Reasoning Engine deployed successfully!")
    print()
    print("=" * 60)
    print("Deployment Complete")
    print("=" * 60)
    print()
    print(f"Reasoning Engine ID: {engine.resource_name}")
    print(f"Display Name: pubsub-lambda-reasoning-engine")
    print()
    print("Logs will automatically flow to:")
    print("  Cloud Logging -> Pub/Sub -> Portal26")
    print()
    print("Next Steps:")
    print("  1. Configure Pub/Sub to invoke this Reasoning Engine")
    print("  2. Test with: gcloud pubsub topics publish test-topic --message 'Test'")
    print("  3. Check logs in Cloud Logging")
    print()

    return engine


if __name__ == "__main__":
    try:
        engine = deploy_reasoning_engine()
        print(f"[OK] Success! Engine deployed: {engine.resource_name}")
    except Exception as e:
        print(f"[ERROR] Error deploying: {str(e)}")
        import traceback
        traceback.print_exc()
