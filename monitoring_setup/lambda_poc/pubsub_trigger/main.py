"""
Cloud Function to trigger Reasoning Engine from Pub/Sub
Architecture: Pub/Sub -> Cloud Function -> Reasoning Engine -> AWS Lambda
"""
import base64
import json
import functions_framework
from google.cloud import aiplatform
import os

PROJECT_ID = os.environ.get("PROJECT_ID", "agentic-ai-integration-490716")
LOCATION = os.environ.get("LOCATION", "us-central1")
REASONING_ENGINE_ID = os.environ.get("REASONING_ENGINE_ID", "3783824681212051456")

# Initialize AI Platform
aiplatform.init(project=PROJECT_ID, location=LOCATION)


@functions_framework.cloud_event
def pubsub_to_reasoning_engine(cloud_event):
    """
    Triggered by Pub/Sub message
    Forwards to Reasoning Engine for processing

    Args:
        cloud_event: CloudEvent with Pub/Sub message
    """
    print(f"[CLOUD FUNCTION] Received Pub/Sub message")

    try:
        # Decode Pub/Sub message
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        message_id = cloud_event.data["message"].get("messageId", "unknown")
        publish_time = cloud_event.data["message"].get("publishTime", "unknown")

        print(f"[CLOUD FUNCTION] Message ID: {message_id}")
        print(f"[CLOUD FUNCTION] Message: {pubsub_message}")

        # Reconstruct message in format Reasoning Engine expects
        reasoning_engine_input = {
            "message": {
                "data": cloud_event.data["message"]["data"],  # Keep base64 encoded
                "messageId": message_id,
                "publishTime": publish_time
            }
        }

        # Load Reasoning Engine
        print(f"[CLOUD FUNCTION] Invoking Reasoning Engine: {REASONING_ENGINE_ID}")
        reasoning_engine = aiplatform.ReasoningEngine(
            f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"
        )

        # Query Reasoning Engine
        result = reasoning_engine.query(**reasoning_engine_input)

        print(f"[CLOUD FUNCTION] Reasoning Engine result: {json.dumps(result, indent=2)}")
        print(f"[CLOUD FUNCTION] Processing complete")

        return {"status": "success", "result": result}

    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        print(f"[CLOUD FUNCTION ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": error_msg}
