"""
Vertex AI Reasoning Engine Agent
This version uses the production Vertex AI SDK instead of ADK
"""

import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any
import os

# Tools for the agent
def get_weather(city: str) -> dict:
    """Returns a mock weather report for a given city.

    Args:
        city: Name of the city to get weather for.

    Returns:
        dict with status and report or error message.
    """
    mock_data = {
        "bengaluru": "Partly cloudy, 28°C. Humidity 70%.",
        "new york":  "Sunny, 22°C. Light winds.",
        "london":    "Overcast, 15°C. Rain expected.",
        "tokyo":     "Sunny, 28°C. Clear skies.",
    }
    normalized = city.lower().strip()
    if normalized in mock_data:
        return {"status": "success", "report": mock_data[normalized]}
    return {
        "status": "error",
        "error_message": f"No weather data available for '{city}'.",
    }


def get_current_time(city: str) -> dict:
    """Returns the current local time for a given city.

    Args:
        city: Name of the city.

    Returns:
        dict with status and current time string or error.
    """
    timezone_map = {
        "bengaluru": "Asia/Kolkata",
        "new york":  "America/New_York",
        "london":    "Europe/London",
        "tokyo":     "Asia/Tokyo",
    }
    tz_name = timezone_map.get(city.lower().strip())
    if not tz_name:
        return {
            "status": "error",
            "error_message": f"Timezone not found for '{city}'.",
        }
    now = datetime.datetime.now(ZoneInfo(tz_name))
    return {
        "status": "success",
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


# Agent implementation for Vertex AI Reasoning Engine
class CityInfoAgent:
    """
    City Information Agent for Vertex AI Reasoning Engine
    Provides weather and time information for cities worldwide.
    """

    def __init__(self):
        self.name = "city_info_agent"
        self.description = "Provides weather and time information for cities worldwide."
        self.tools = {
            "get_weather": get_weather,
            "get_current_time": get_current_time,
        }

    def query(self, user_input: str) -> Dict[str, Any]:
        """
        Process user query using Gemini with function calling

        Args:
            user_input: User's question

        Returns:
            Dict with response and metadata
        """
        from google import genai
        from google.genai import types

        # Initialize Gemini client
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        api_key = os.getenv("GOOGLE_CLOUD_API_KEY")

        if api_key:
            client = genai.Client(api_key=api_key)
            model_name = "models/gemini-2.0-flash-exp"
        else:
            client = genai.Client(vertexai=True, project=project_id, location=location)
            model_name = "gemini-1.5-flash"

        # Define tools for function calling
        tool_declarations = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="get_weather",
                        description="Get current weather for a city",
                        parameters={
                            "type": "object",
                            "properties": {
                                "city": {
                                    "type": "string",
                                    "description": "Name of the city"
                                }
                            },
                            "required": ["city"]
                        }
                    ),
                    types.FunctionDeclaration(
                        name="get_current_time",
                        description="Get current local time for a city",
                        parameters={
                            "type": "object",
                            "properties": {
                                "city": {
                                    "type": "string",
                                    "description": "Name of the city"
                                }
                            },
                            "required": ["city"]
                        }
                    )
                ]
            )
        ]

        # System instruction
        system_instruction = (
            "You are a helpful city assistant. Use the available tools to answer "
            "questions about the current weather or time in any city the user asks about. "
            "Always use a tool — never guess or make up data."
        )

        # First request with tools
        response = client.models.generate_content(
            model=model_name,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tool_declarations,
                temperature=0.1,
            )
        )

        # Check if model wants to call a function
        if response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]

            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                function_name = function_call.name
                function_args = dict(function_call.args)

                print(f"[agent] Function call: {function_name}({function_args})")

                # Execute the function
                if function_name in self.tools:
                    function_result = self.tools[function_name](**function_args)
                    print(f"[agent] Function result: {function_result}")

                    # Send result back to model
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Content(role="user", parts=[types.Part(text=user_input)]),
                            response.candidates[0].content,
                            types.Content(
                                role="user",
                                parts=[types.Part(
                                    function_response=types.FunctionResponse(
                                        name=function_name,
                                        response=function_result
                                    )
                                )]
                            )
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            tools=tool_declarations,
                            temperature=0.1,
                        )
                    )

        # Extract final response
        final_response = response.text if response.text else "No response generated"

        return {
            "response": final_response,
            "model": model_name,
            "agent": self.name
        }


# For Vertex AI Reasoning Engine deployment
def get_agent():
    """Factory function to create agent instance"""
    return CityInfoAgent()


# Standalone query function for Reasoning Engine
def query(user_input: str) -> Dict[str, Any]:
    """
    Main entry point for Vertex AI Reasoning Engine

    Args:
        user_input: User's question

    Returns:
        Agent response
    """
    agent = get_agent()
    return agent.query(user_input)


if __name__ == "__main__":
    # Test locally
    import sys

    # Set up environment
    os.environ["GOOGLE_CLOUD_PROJECT"] = "agentic-ai-integration-490716"
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

    # Test query
    test_query = sys.argv[1] if len(sys.argv) > 1 else "What is the weather in Tokyo?"
    print(f"Query: {test_query}")
    print()

    result = query(test_query)
    print(f"Response: {result['response']}")
