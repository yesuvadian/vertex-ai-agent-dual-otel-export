"""Simple test without Unicode issues"""
from vertexai.preview import reasoning_engines
import vertexai
import time

# Initialize
vertexai.init(
    project="agentic-ai-integration-490716",
    location="us-central1"
)

# Your actual engine
print("Loading Reasoning Engine...")
reasoning_engine = reasoning_engines.ReasoningEngine(
    "projects/961756870884/locations/us-central1/reasoningEngines/6010661182900273152"
)
print("Loaded successfully!")

# Simple test queries
queries = [
    "Hello, how are you?",
    "What is the weather today?",
    "Explain what a Reasoning Engine is."
]

print(f"\nStarting {len(queries)} test invocations...")
print("="*60)

for i, query in enumerate(queries, 1):
    print(f"\n[{i}/{len(queries)}] Query: {query}")
    try:
        start = time.time()
        response = reasoning_engine.query(input=query)
        elapsed = time.time() - start

        response_text = str(response)[:100] if response else "No response"
        print(f"Success ({elapsed:.2f}s): {response_text}...")
    except Exception as e:
        print(f"Error: {e}")

    if i < len(queries):
        print("Waiting 15 seconds...")
        time.sleep(15)

print("\n" + "="*60)
print("Test complete! Check the analyzer for captured logs.")
