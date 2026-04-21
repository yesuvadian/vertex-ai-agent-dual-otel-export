"""
Vertex AI Reasoning Engine Agent
Analyzes GCP Pub/Sub messages before forwarding to AWS Lambda
"""
import os
import json
import base64
import requests
from datetime import datetime
from flask import Flask, request as flask_request

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "agentic-ai-integration-490716")
AWS_LAMBDA_URL = os.getenv("AWS_LAMBDA_URL", "https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/")

app = Flask(__name__)

class MonitoringAgent:
    """AI Agent for monitoring data analysis"""

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name

    def analyze_log_message(self, message_data: str) -> dict:
        """
        Analyze log message for anomalies and insights

        Args:
            message_data: Decoded Pub/Sub message content

        Returns:
            Analysis results with severity, category, insights
        """
        print(f"[AGENT] Analyzing message: {message_data[:100]}")

        # AI analysis (rule-based for now, can add Gemini later)
        analysis = {
            "severity": "INFO",
            "category": "info",
            "anomaly_detected": False,
            "insights": "Normal monitoring data",
            "recommended_action": "forward_to_portal26",
            "ai_processed": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Check for error keywords
        message_lower = message_data.lower()
        if any(keyword in message_lower for keyword in ['error', 'exception', 'failed', 'critical']):
            analysis["severity"] = "HIGH"
            analysis["category"] = "error"
            analysis["anomaly_detected"] = True
            analysis["insights"] = "Error detected in monitoring data"
            analysis["recommended_action"] = "alert_and_forward"
            print("[AGENT] ANOMALY DETECTED: Error keyword found")

        elif any(keyword in message_lower for keyword in ['warning', 'warn']):
            analysis["severity"] = "MEDIUM"
            analysis["category"] = "warning"
            analysis["insights"] = "Warning detected in monitoring data"

        elif any(keyword in message_lower for keyword in ['metric', 'cpu', 'memory', 'disk']):
            analysis["category"] = "metric"
            analysis["insights"] = "System metric data"

        return analysis

    def enrich_message(self, original_message: dict, analysis: dict) -> dict:
        """
        Enrich original message with AI analysis

        Args:
            original_message: Original Pub/Sub message
            analysis: AI analysis results

        Returns:
            Enriched message with AI metadata
        """
        enriched = {
            "message": original_message,  # Keep original format for Lambda
            "ai_enrichment": {
                "analysis": analysis,
                "processing_time": datetime.utcnow().isoformat(),
                "agent_version": "1.0.0",
                "agent_service": "vertex-ai-reasoning-engine"
            }
        }
        return enriched

    def forward_to_lambda(self, enriched_message: dict) -> dict:
        """
        Forward enriched message to AWS Lambda

        Args:
            enriched_message: Message with AI analysis

        Returns:
            Lambda response
        """
        print(f"[AGENT] Forwarding to Lambda: {AWS_LAMBDA_URL}")

        try:
            response = requests.post(
                AWS_LAMBDA_URL,
                json=enriched_message,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            print(f"[AGENT] Lambda response: {response.status_code}")

            return {
                "status": "success",
                "lambda_status_code": response.status_code,
                "lambda_response": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            print(f"[AGENT] Error forwarding to Lambda: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def process_pubsub_message(self, pubsub_message: dict) -> dict:
        """
        Main processing function for Pub/Sub messages

        Args:
            pubsub_message: Raw Pub/Sub push message

        Returns:
            Processing result
        """
        timestamp = datetime.utcnow().isoformat()
        print(f"[{timestamp}] === Reasoning Engine Processing ===")

        # Extract and decode message data
        message = pubsub_message.get('message', {})
        encoded_data = message.get('data', '')
        message_id = message.get('messageId', 'unknown')
        publish_time = message.get('publishTime', 'unknown')

        print(f"[AGENT] Message ID: {message_id}")
        print(f"[AGENT] Publish Time: {publish_time}")

        try:
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
            print(f"[AGENT] Decoded data: {decoded_data}")
        except Exception as e:
            decoded_data = f"[Decode error: {str(e)}]"
            print(f"[AGENT] Error decoding: {str(e)}")

        # AI Analysis
        analysis = self.analyze_log_message(decoded_data)
        print(f"[AGENT] Analysis: {json.dumps(analysis, indent=2)}")

        # Enrich message (keep original message format for Lambda compatibility)
        enriched_message = self.enrich_message(
            original_message={
                "data": encoded_data,
                "messageId": message_id,
                "publishTime": publish_time
            },
            analysis=analysis
        )

        # Decide whether to forward based on analysis
        should_forward = True

        # Optional: Filter low-severity messages
        # if analysis["severity"] == "INFO":
        #     should_forward = False
        #     print("[AGENT] Skipping forward - low severity")

        lambda_result = {"status": "skipped", "reason": "filtered"}

        if should_forward:
            # Forward to AWS Lambda
            lambda_result = self.forward_to_lambda(enriched_message)
            print(f"[AGENT] Lambda result: {json.dumps(lambda_result, indent=2)}")

        return {
            "status": "success",
            "agent_processed": True,
            "message_id": message_id,
            "analysis": analysis,
            "lambda_forwarded": lambda_result.get("status") == "success",
            "timestamp": timestamp
        }


@app.route('/', methods=['POST'])
def pubsub_handler():
    """
    Cloud Run handler for Pub/Sub push messages
    Compatible with Pub/Sub push subscription format
    """
    try:
        # Parse request
        request_json = flask_request.get_json()

        print(f"[HANDLER] Received request")
        print(f"[HANDLER] Headers: {dict(flask_request.headers)}")

        # Initialize agent
        agent = MonitoringAgent()

        # Process message
        result = agent.process_pubsub_message(request_json)

        print(f"[HANDLER] Processing complete: {result['status']}")

        # Return 200 to acknowledge message
        return json.dumps(result), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        print(f"[HANDLER] Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()

        # Return 500 for retry
        return json.dumps({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500, {'Content-Type': 'application/json'}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return json.dumps({
        "status": "healthy",
        "service": "vertex-ai-reasoning-agent",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }), 200, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    # For local testing
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
