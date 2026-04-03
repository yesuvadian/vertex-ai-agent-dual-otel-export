"""
Cloud Run worker that processes Vertex AI telemetry logs
Triggered by Pub/Sub push subscription
"""
import base64
import json
import logging
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from trace_processor import TraceProcessor

# Load environment variables from .env file (for local testing)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize processor (stateless)
try:
    processor = TraceProcessor()
    logger.info("TraceProcessor initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize TraceProcessor: {e}", exc_info=True)
    processor = None


@app.route('/process', methods=['POST'])
def process_telemetry():
    """
    Process incoming Pub/Sub message
    Dynamic tenant handling - extracts tenant_id from each message
    """
    if not processor:
        return jsonify({'error': 'Processor not initialized'}), 500

    try:
        # Parse Pub/Sub message
        envelope = request.get_json()
        if not envelope:
            logger.warning("Received request with no JSON body")
            return jsonify({'error': 'No Pub/Sub message'}), 400

        # Decode message data
        pubsub_message = envelope.get('message', {})
        if not pubsub_message:
            logger.warning("Received envelope with no message field")
            return jsonify({'error': 'No message field'}), 400

        # Get message ID for tracking
        message_id = pubsub_message.get('messageId', 'unknown')

        # Decode base64 data
        data_encoded = pubsub_message.get('data', '')
        if not data_encoded:
            logger.warning(f"Message {message_id} has no data")
            return jsonify({'error': 'No data in message'}), 400

        try:
            data = base64.b64decode(data_encoded).decode('utf-8')
            log_entry = json.loads(data)
        except Exception as e:
            logger.error(f"Failed to decode message {message_id}: {e}")
            return jsonify({'error': 'Failed to decode message'}), 400

        # Extract message attributes (tenant_id might be here)
        attributes = pubsub_message.get('attributes', {})

        logger.info(f"Processing message {message_id}, insertId: {log_entry.get('insertId')}")

        # Process (extracts tenant_id dynamically)
        result = processor.process_log_entry(log_entry, attributes)

        if result['success']:
            logger.info(
                f"Successfully processed trace {result.get('trace_id')} "
                f"for tenant {result['tenant_id']}"
            )
            return jsonify({
                'status': 'success',
                'tenant_id': result['tenant_id'],
                'trace_id': result.get('trace_id')
            }), 200
        else:
            logger.warning(
                f"Processing failed for message {message_id}: {result['error']}"
            )
            # Return 200 to ack message (don't retry on application errors)
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 200

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        # Return 500 to trigger retry
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Cloud Run"""
    if not processor:
        return jsonify({
            'status': 'unhealthy',
            'error': 'Processor not initialized'
        }), 503

    return jsonify({
        'status': 'healthy',
        'service': 'telemetry-worker',
        'version': '1.0.0'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'Vertex AI Telemetry Worker',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'process': '/process (POST)'
        }
    }), 200


if __name__ == '__main__':
    # Local development server
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
