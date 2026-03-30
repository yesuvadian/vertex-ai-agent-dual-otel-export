import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

# Configuration from .env
AGENT_MODE = os.getenv("AGENT_MODE", "manual").lower()  # Options: "manual", "adk", "both"
ENABLE_MANUAL_AGENT = os.getenv("ENABLE_MANUAL_AGENT", "true").lower() == "true"
ENABLE_ADK_AGENT = os.getenv("ENABLE_ADK_AGENT", "false").lower() == "true"


def run_agent(user_input: str) -> Dict[str, Any]:
    """
    Routes the user input to the appropriate agent(s) based on .env configuration.

    Configuration options in .env:
    - AGENT_MODE=manual (default) - Use only manual agent
    - AGENT_MODE=adk - Use only ADK agent
    - AGENT_MODE=both - Run both agents and return both responses

    Or use individual flags:
    - ENABLE_MANUAL_AGENT=true/false
    - ENABLE_ADK_AGENT=true/false

    Args:
        user_input: User's message/question

    Returns:
        Dictionary with agent response(s)
    """
    results = {}

    # Determine which agents to run
    use_manual = AGENT_MODE in ["manual", "both"] or ENABLE_MANUAL_AGENT
    use_adk = AGENT_MODE in ["adk", "both"] or ENABLE_ADK_AGENT

    # Run manual agent
    if use_manual:
        try:
            from agent_manual import run_agent as run_manual_agent
            manual_result = run_manual_agent(user_input)
            results["manual_agent"] = manual_result
            print(f"[router] Manual agent executed successfully")
        except Exception as e:
            results["manual_agent"] = {"error": str(e)}
            print(f"[router] Manual agent failed: {e}")

    # Run ADK agent
    if use_adk:
        try:
            # Try to import and run ADK agent
            from agent import root_agent
            adk_result = root_agent.execute(user_input)
            results["adk_agent"] = {"response": adk_result}
            print(f"[router] ADK agent executed successfully")
        except ImportError as e:
            results["adk_agent"] = {
                "error": "ADK not available",
                "detail": str(e),
                "note": "Install google-genai-adk or use AGENT_MODE=manual"
            }
            print(f"[router] ADK agent not available: {e}")
        except Exception as e:
            results["adk_agent"] = {"error": str(e)}
            print(f"[router] ADK agent failed: {e}")

    # If no agents enabled, return error
    if not results:
        return {
            "error": "No agents enabled",
            "note": "Set AGENT_MODE=manual or AGENT_MODE=adk in .env"
        }

    # If only one agent, return its result directly
    if len(results) == 1:
        return list(results.values())[0]

    # If both agents, return combined results
    return {
        "mode": "both",
        "results": results
    }


def get_agent_status() -> Dict[str, Any]:
    """Returns the current agent configuration status."""
    return {
        "agent_mode": AGENT_MODE,
        "manual_agent_enabled": AGENT_MODE in ["manual", "both"] or ENABLE_MANUAL_AGENT,
        "adk_agent_enabled": AGENT_MODE in ["adk", "both"] or ENABLE_ADK_AGENT,
    }
