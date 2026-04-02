"""
Generate a full trace with nested spans to test Cloud Trace
"""
import os
import sys
import time

# Load environment
env_file = "gcp_traces_agent/.env"
with open(env_file, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

# Change to agent directory
os.chdir("gcp_traces_agent")
sys.path.insert(0, os.getcwd())

print("=" * 70)
print("Testing Full Trace Generation")
print("=" * 70)
print()

print("Importing agent...")
from agent import root_agent
print("[OK] Agent with Cloud Trace exporter loaded")
print()

print("Generating full trace with nested spans...")
print("-" * 70)

from opentelemetry import trace
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("agent_query") as query_span:
    query_span.set_attribute("query.text", "What is the weather in Tokyo?")
    query_span.set_attribute("query.timestamp", time.time())

    print("[SPAN] Created: agent_query")

    # Simulate LLM call
    with tracer.start_as_current_span("llm_call") as llm_span:
        llm_span.set_attribute("llm.model", "gemini-2.5-flash")
        llm_span.set_attribute("llm.prompt", "What is the weather in Tokyo?")
        time.sleep(0.5)
        llm_span.set_attribute("llm.response", "I'll check the weather for Tokyo")
        print("[SPAN] Created: llm_call (child of agent_query)")

    # Simulate tool call
    with tracer.start_as_current_span("tool_execution") as tool_span:
        tool_span.set_attribute("tool.name", "get_weather")
        tool_span.set_attribute("tool.input.city", "tokyo")
        time.sleep(0.3)
        tool_span.set_attribute("tool.output", "Sunny, 28C. Clear skies.")
        print("[SPAN] Created: tool_execution (child of agent_query)")

    # Simulate final LLM response
    with tracer.start_as_current_span("llm_response") as response_span:
        response_span.set_attribute("llm.model", "gemini-2.5-flash")
        response_span.set_attribute("llm.final_response", "The weather in Tokyo is sunny, 28C with clear skies.")
        time.sleep(0.4)
        print("[SPAN] Created: llm_response (child of agent_query)")

    query_span.set_attribute("query.status", "completed")
    query_span.set_attribute("query.duration_ms", 1200)

print()
print("[OK] Full trace with nested spans created")
print()

print("Flushing to Cloud Trace...")
provider = trace.get_tracer_provider()
if hasattr(provider, 'force_flush'):
    provider.force_flush()
time.sleep(5)
print("[OK] Flushed")
print()

print("=" * 70)
print("Check Cloud Trace Now")
print("=" * 70)
print()
print("URL: https://console.cloud.google.com/traces?project=agentic-ai-integration-490716")
print()
print("Filter:")
print("  - Service: gcp_traces_agent")
print("  - Time: Last 5 minutes")
print()
print("You should see:")
print("  - Root span: agent_query")
print("  - Child spans: llm_call, tool_execution, llm_response")
print("  - Attributes on each span")
print("  - Timing/duration for each operation")
print()
