"""
Test script using the exact code from Google Cloud Console
This verifies the model and authentication work correctly
"""

from google import genai
from google.genai import types
import os

def test_console_code():
    """Test using console code format"""

    # Try to initialize client
    api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")

    if api_key:
        print("[Test] Using Gemini API with API key")
        # Use Gemini API directly (accepts API keys)
        client = genai.Client(api_key=api_key)
    else:
        print("[Test] Using Vertex AI with Application Default Credentials")
        print("[Test] Run 'gcloud auth application-default login' if this fails")
        # Use Vertex AI (requires OAuth2/ADC)
        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "agentic-ai-integration-490716"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        )

    # Use correct model name format for Gemini API
    model = "models/gemini-2.5-flash" if api_key else "gemini-1.5-flash"

    print(f"[Test] Testing model: {model}")
    print("[Test] Sending test prompt...")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""What is 2+2? Answer briefly.""")
            ]
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=1000,
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )

        print(f"\n[Test] SUCCESS!")
        print(f"[Test] Response: {response.text}")
        print(f"\n[Test] Model '{model}' is working correctly!")
        return True

    except Exception as e:
        print(f"\n[Test] FAILED: {e}")
        print(f"\n[Test] Troubleshooting:")
        print(f"  1. Make sure you're authenticated:")
        print(f"     gcloud auth application-default login")
        print(f"  2. Or set API key in .env:")
        print(f"     GOOGLE_CLOUD_API_KEY=your-key")
        print(f"  3. Get API key from:")
        print(f"     https://console.cloud.google.com/apis/credentials?project=agentic-ai-integration-490716")
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("="*60)
    print("Testing Google GenAI Connection")
    print("="*60)
    print()

    success = test_console_code()

    print()
    print("="*60)
    if success:
        print("Ready to run the agent!")
        print("  Start server: python -m uvicorn app:app --reload")
        print("  Test API: python test_api.py")
    else:
        print("Please fix authentication first")
    print("="*60)
