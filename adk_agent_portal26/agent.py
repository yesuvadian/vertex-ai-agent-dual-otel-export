import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp


def get_weather(city: str) -> dict:
    """Returns mock weather for a given city."""
    mock_data = {
        "bengaluru": "Partly cloudy, 28C. Humidity 70%.",
        "new york":  "Sunny, 22C. Light winds.",
        "london":    "Overcast, 15C. Rain expected.",
        "tokyo":     "Sunny, 28C. Clear skies.",
    }
    normalized = city.lower().strip()
    if normalized in mock_data:
        return {"status": "success", "report": mock_data[normalized]}
    return {
        "status": "error",
        "error_message": f"No weather data available for '{city}'.",
    }


def get_current_time(city: str) -> dict:
    """Returns current time for a given city."""
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


root_agent = Agent(
    name="portal26GCPTel",
    model="gemini-2.0-flash-exp",
    description="City info agent - exports telemetry directly to Portal26 cloud",
    instruction=(
        "You are a helpful city assistant. Use the available tools to answer "
        "questions about the current weather or time in any city the user asks about. "
        "Always use a tool - never guess or make up data."
    ),
    tools=[get_weather, get_current_time],
)

# Simple AdkApp without customization
# OTEL setup happens in __init__.py before this module loads
app = AdkApp(agent=root_agent)
