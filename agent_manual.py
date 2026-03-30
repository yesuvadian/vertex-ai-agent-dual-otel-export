import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telemetry import tracer

# Load environment variables
load_dotenv()

# Initialize Google GenAI client (matching console code)
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
api_key = os.getenv("GOOGLE_CLOUD_API_KEY")

# Initialize client (API key for Gemini API, or Vertex AI with ADC)
try:
    if api_key:
        # Use Gemini API directly (accepts API keys)
        client = genai.Client(api_key=api_key)
        # Gemini API requires "models/" prefix
        MODEL_NAME = "models/gemini-2.5-flash"
        print(f"[agent_manual] Initialized Gemini API with API key - Model: {MODEL_NAME}")
    else:
        # Use Vertex AI (requires OAuth2/ADC)
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        MODEL_NAME = "gemini-1.5-flash"
        print(f"[agent_manual] Initialized Vertex AI - Project: {project_id}, Location: {location} - Model: {MODEL_NAME}")
except Exception as e:
    print(f"[agent_manual] ERROR initializing client: {e}")
    client = None
    MODEL_NAME = "gemini-1.5-flash"

def get_weather(city: str):
    return {"result": f"Weather in {city}: 28°C, sunny"}

def get_order_status(order_id: str):
    return {"result": f"Order {order_id} is shipped"}

TOOLS = {
    "get_weather": get_weather,
    "get_order_status": get_order_status,
}

def run_agent(user_input: str):
    if not client:
        return {"error": "Google GenAI client not initialized. Check GOOGLE_CLOUD_PROJECT in .env"}

    with tracer.start_as_current_span("agent_run") as span:
        span.set_attribute("user.input", user_input)

        prompt = f"""
You are an AI agent.

Available tools:
- get_weather(city)
- get_order_status(order_id)

Return JSON:
{{"action": "...", "input": "..."}}

User: {user_input}
"""

        with tracer.start_as_current_span("llm_call"):
            # Generate content config matching console code
            generate_config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=8192,
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=generate_config
            )

        try:
            response_text = response.text
            # Strip markdown code blocks if present
            if response_text.strip().startswith("```"):
                # Extract JSON from markdown code block
                lines = response_text.strip().split("\n")
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            decision = json.loads(response_text)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": response_text}
        except Exception as e:
            return {"error": f"LLM error: {str(e)}"}

        if decision.get("action") in TOOLS:
            tool_name = decision["action"]
            tool_input = decision["input"]

            with tracer.start_as_current_span(f"tool:{tool_name}"):
                result = TOOLS[tool_name](tool_input)

            final_prompt = f"""
User: {user_input}
Tool result: {result}
Give final answer.
"""

            with tracer.start_as_current_span("llm_final"):
                final = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=final_prompt,
                    config=generate_config
                )

            return {"final_answer": final.text}

        return decision
