"""
Empty Agent with Portal26 OTEL Integration
A minimal agent for testing telemetry ingestion
"""
import otel_portal26  # Portal 26 telemetry - auto-initializes on import
from vertexai.preview import reasoning_engines

def simple_query(query: str) -> str:
    """
    Simple query handler that echoes the input.

    Args:
        query: User's question

    Returns:
        Simple response with telemetry tracking
    """
    response = f"Echo: {query}"
    print(f"[EmptyAgent] Processed query: {query}")
    return response


def get_status() -> dict:
    """
    Returns agent status for health checks.

    Returns:
        Status dictionary
    """
    return {
        "status": "active",
        "agent_type": "empty_agent_portal26",
        "capabilities": ["echo", "status"],
        "telemetry": "portal26_enabled"
    }


# Define the agent
root_agent = reasoning_engines.LangchainAgent(
    model="gemini-2.5-flash",
    tools=[simple_query, get_status],
    model_kwargs={
        "temperature": 0.1,
    },
)
