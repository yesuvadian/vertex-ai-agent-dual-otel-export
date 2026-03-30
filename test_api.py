#!/usr/bin/env python3
"""
Test script for the AI Agent API
Demonstrates both agent modes
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, method, url, data=None):
    """Test a single API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)

        print(f"Status: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        return True
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server not running. Start with: uvicorn app:app --reload")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def main():
    print("AI Agent API Test Suite")
    print(f"Testing server at: {BASE_URL}\n")

    # Test 1: Root endpoint
    if not test_endpoint(
        "Root Endpoint",
        "GET",
        f"{BASE_URL}/"
    ):
        sys.exit(1)

    # Test 2: Status endpoint
    if not test_endpoint(
        "Status Endpoint",
        "GET",
        f"{BASE_URL}/status"
    ):
        sys.exit(1)

    # Test 3: Chat with weather query
    test_endpoint(
        "Chat - Weather Query",
        "POST",
        f"{BASE_URL}/chat",
        {"message": "What's the weather in New York?"}
    )

    # Test 4: Chat with order status query
    test_endpoint(
        "Chat - Order Status Query",
        "POST",
        f"{BASE_URL}/chat",
        {"message": "What's the status of order ABC123?"}
    )

    print(f"\n{'='*60}")
    print("All tests completed!")
    print(f"{'='*60}\n")

    print("Tips:")
    print("  - Change AGENT_MODE in .env to switch between agent types")
    print("  - AGENT_MODE=manual  -> Use manual agent (default)")
    print("  - AGENT_MODE=adk     -> Use ADK agent (requires google-genai-adk)")
    print("  - AGENT_MODE=both    -> Run both agents in parallel")

if __name__ == "__main__":
    main()
