"""
ADK Agent with Tools for GCP Monitoring
Includes tools for message analysis, Lambda forwarding, and log querying
"""
import base64
import json
import requests
from datetime import datetime
from typing import Dict, Any, List

# Tool configurations
AWS_LAMBDA_URL = "https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/"
PROJECT_ID = "agentic-ai-integration-490716"


def analyze_message(message_text: str) -> Dict[str, Any]:
    """
    Analyze a monitoring message for severity and anomalies.

    Args:
        message_text: The text content to analyze

    Returns:
        Analysis results including severity, category, and insights
    """
    print(f"[TOOL: analyze_message] Analyzing: {message_text[:100]}")

    analysis = {
        "severity": "INFO",
        "category": "info",
        "anomaly_detected": False,
        "insights": "Normal monitoring data",
        "recommended_action": "forward",
        "timestamp": datetime.utcnow().isoformat()
    }

    message_lower = message_text.lower()

    # Error detection
    if any(keyword in message_lower for keyword in ['error', 'exception', 'failed', 'critical', 'fatal']):
        analysis["severity"] = "HIGH"
        analysis["category"] = "error"
        analysis["anomaly_detected"] = True
        analysis["insights"] = "Error detected - immediate attention required"
        analysis["recommended_action"] = "alert_and_forward"

    # Warning detection
    elif any(keyword in message_lower for keyword in ['warning', 'warn', 'deprecated']):
        analysis["severity"] = "MEDIUM"
        analysis["category"] = "warning"
        analysis["insights"] = "Warning detected - monitor closely"
        analysis["recommended_action"] = "forward_and_monitor"

    # Performance issues
    elif any(keyword in message_lower for keyword in ['slow', 'timeout', 'latency', 'delay']):
        analysis["severity"] = "MEDIUM"
        analysis["category"] = "performance"
        analysis["insights"] = "Performance issue detected"
        analysis["recommended_action"] = "investigate"

    # Metrics
    elif any(keyword in message_lower for keyword in ['metric', 'cpu', 'memory', 'disk', 'usage']):
        analysis["category"] = "metric"
        analysis["insights"] = "System metric data"

    print(f"[TOOL: analyze_message] Result: {analysis['severity']} - {analysis['insights']}")
    return analysis


def forward_to_lambda(message_data: str, message_id: str, publish_time: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Forward message to AWS Lambda with AI enrichment.

    Args:
        message_data: Base64 encoded message data
        message_id: Unique message identifier
        publish_time: Time message was published
        analysis: AI analysis results

    Returns:
        Forward result with Lambda response
    """
    print(f"[TOOL: forward_to_lambda] Forwarding message {message_id} to Lambda")

    payload = {
        "message": {
            "data": message_data,
            "messageId": message_id,
            "publishTime": publish_time
        },
        "ai_analysis": analysis,
        "agent_type": "adk_agent_with_tools",
        "processing_time": datetime.utcnow().isoformat()
    }

    try:
        response = requests.post(
            AWS_LAMBDA_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        result = {
            "status": "success",
            "lambda_status_code": response.status_code,
            "lambda_response": response.json() if response.status_code == 200 else response.text[:200]
        }

        print(f"[TOOL: forward_to_lambda] Lambda returned {response.status_code}")
        return result

    except Exception as e:
        error_msg = f"Error forwarding to Lambda: {str(e)}"
        print(f"[TOOL: forward_to_lambda] {error_msg}")
        return {
            "status": "error",
            "error": error_msg
        }


def query_gcp_logs(filter_query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query GCP Cloud Logging for recent logs.

    Args:
        filter_query: Cloud Logging filter query
        limit: Maximum number of log entries to return

    Returns:
        List of log entries
    """
    print(f"[TOOL: query_gcp_logs] Querying logs with filter: {filter_query}")

    try:
        from google.cloud import logging
        client = logging.Client(project=PROJECT_ID)

        entries = list(client.list_entries(filter_=filter_query, max_results=limit))

        results = []
        for entry in entries:
            results.append({
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "severity": entry.severity,
                "log_name": entry.log_name,
                "payload": str(entry.payload)[:200]  # Truncate for display
            })

        print(f"[TOOL: query_gcp_logs] Found {len(results)} log entries")
        return results

    except Exception as e:
        print(f"[TOOL: query_gcp_logs] Error: {str(e)}")
        return [{"error": str(e)}]


def decode_base64_message(encoded_data: str) -> str:
    """
    Decode base64 encoded message data.

    Args:
        encoded_data: Base64 encoded string

    Returns:
        Decoded text
    """
    print(f"[TOOL: decode_base64_message] Decoding message")

    try:
        decoded = base64.b64decode(encoded_data).decode('utf-8')
        print(f"[TOOL: decode_base64_message] Decoded: {decoded[:100]}")
        return decoded
    except Exception as e:
        error_msg = f"Error decoding: {str(e)}"
        print(f"[TOOL: decode_base64_message] {error_msg}")
        return error_msg


def get_severity_stats(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate severity statistics from a list of analyzed messages.

    Args:
        messages: List of messages with analysis results

    Returns:
        Count of messages by severity level
    """
    print(f"[TOOL: get_severity_stats] Calculating stats for {len(messages)} messages")

    stats = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "INFO": 0,
        "total": len(messages)
    }

    for msg in messages:
        severity = msg.get("analysis", {}).get("severity", "INFO")
        stats[severity] = stats.get(severity, 0) + 1

    print(f"[TOOL: get_severity_stats] Stats: {stats}")
    return stats


# Agent orchestration function
def process_monitoring_message(message_data: str, message_id: str, publish_time: str = None) -> Dict[str, Any]:
    """
    Main agent function to process monitoring messages.
    Orchestrates multiple tools to analyze and forward messages.

    Args:
        message_data: Base64 encoded message data
        message_id: Message identifier
        publish_time: Optional publish timestamp

    Returns:
        Complete processing result
    """
    if publish_time is None:
        publish_time = datetime.utcnow().isoformat() + "Z"

    print(f"[AGENT] Processing message {message_id}")

    # Step 1: Decode message
    decoded_text = decode_base64_message(message_data)

    # Step 2: Analyze message
    analysis = analyze_message(decoded_text)

    # Step 3: Forward to Lambda
    lambda_result = forward_to_lambda(message_data, message_id, publish_time, analysis)

    # Step 4: Return complete result
    result = {
        "status": "success",
        "message_id": message_id,
        "decoded_message": decoded_text[:200],  # Truncate for display
        "analysis": analysis,
        "lambda_result": lambda_result,
        "timestamp": datetime.utcnow().isoformat()
    }

    print(f"[AGENT] Processing complete for {message_id}")
    return result


# Define tools metadata for ADK
TOOLS = [
    {
        "name": "analyze_message",
        "description": "Analyze a monitoring message for severity, category, and anomalies",
        "parameters": {
            "message_text": "The text content to analyze"
        }
    },
    {
        "name": "forward_to_lambda",
        "description": "Forward message to AWS Lambda with AI enrichment",
        "parameters": {
            "message_data": "Base64 encoded message data",
            "message_id": "Message identifier",
            "publish_time": "Publish timestamp",
            "analysis": "AI analysis results"
        }
    },
    {
        "name": "query_gcp_logs",
        "description": "Query GCP Cloud Logging for recent logs",
        "parameters": {
            "filter_query": "Cloud Logging filter query",
            "limit": "Maximum number of entries (default 10)"
        }
    },
    {
        "name": "decode_base64_message",
        "description": "Decode base64 encoded message data",
        "parameters": {
            "encoded_data": "Base64 encoded string"
        }
    },
    {
        "name": "get_severity_stats",
        "description": "Calculate severity statistics from analyzed messages",
        "parameters": {
            "messages": "List of messages with analysis results"
        }
    }
]
