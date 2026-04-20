"""
Test Agent Invocations
Triggers multiple Reasoning Engine invocations to generate log data for analysis

Usage:
  python test_agent_invocations.py --count 10 --delay 5
"""
import argparse
import time
from datetime import datetime
from vertexai.preview import reasoning_engines
import vertexai

# Test queries of different complexity
TEST_QUERIES = {
    'simple': [
        "Hello, how are you?",
        "What is 2+2?",
        "Tell me a joke.",
        "What's the weather?",
        "Hi there!"
    ],
    'medium': [
        "Explain what a Reasoning Engine is.",
        "How does machine learning work?",
        "What are the benefits of cloud computing?",
        "Describe the process of natural language processing.",
        "What is the difference between AI and ML?"
    ],
    'complex': [
        "Analyze the pros and cons of using serverless architecture for a high-traffic application with variable load patterns.",
        "Explain the complete lifecycle of a request in a microservices architecture, including service discovery, load balancing, and circuit breakers.",
        "Design a comprehensive monitoring strategy for 1000 distributed agents running across multiple cloud providers.",
        "Compare and contrast different database scaling strategies including sharding, replication, and partitioning.",
        "Describe a fault-tolerant system design for handling 10,000 concurrent users with 99.99% uptime."
    ]
}

def test_invocations(reasoning_engine_name, count=10, delay=5, complexity='mixed'):
    """
    Trigger multiple invocations of Reasoning Engine

    Args:
        reasoning_engine_name: Name or ID of reasoning engine
        count: Number of invocations
        delay: Seconds between invocations
        complexity: 'simple', 'medium', 'complex', or 'mixed'
    """
    print("="*80)
    print("REASONING ENGINE TEST INVOCATIONS")
    print("="*80)
    print(f"Engine: {reasoning_engine_name}")
    print(f"Invocations: {count}")
    print(f"Delay: {delay}s")
    print(f"Complexity: {complexity}")
    print("")

    # Initialize Vertex AI
    project_id = "agentic-ai-integration-490716"
    location = "us-central1"

    vertexai.init(project=project_id, location=location)

    # Get reasoning engine
    print("Loading Reasoning Engine...")
    try:
        reasoning_engine = reasoning_engines.ReasoningEngine(reasoning_engine_name)
        print(f"✓ Loaded: {reasoning_engine_name}")
    except Exception as e:
        print(f"✗ Failed to load engine: {e}")
        return

    print("")
    print("Starting invocations...")
    print("-"*80)

    results = []
    errors = 0

    for i in range(count):
        # Select query based on complexity
        if complexity == 'mixed':
            # Rotate through all complexities
            if i % 3 == 0:
                query_type = 'simple'
            elif i % 3 == 1:
                query_type = 'medium'
            else:
                query_type = 'complex'
        else:
            query_type = complexity

        query = TEST_QUERIES[query_type][i % len(TEST_QUERIES[query_type])]

        print(f"\n[{i+1}/{count}] {datetime.now().strftime('%H:%M:%S')}")
        print(f"  Type: {query_type}")
        print(f"  Query: {query[:60]}{'...' if len(query) > 60 else ''}")

        start_time = time.time()

        try:
            # Invoke reasoning engine
            response = reasoning_engine.query(input=query)

            elapsed = time.time() - start_time

            # Extract response
            if hasattr(response, 'output'):
                response_text = response.output
            elif isinstance(response, dict):
                response_text = response.get('output', str(response))
            else:
                response_text = str(response)

            print(f"  ✓ Success ({elapsed:.2f}s)")
            print(f"  Response: {response_text[:80]}{'...' if len(response_text) > 80 else ''}")

            results.append({
                'invocation': i + 1,
                'query_type': query_type,
                'query': query,
                'success': True,
                'duration': elapsed,
                'response_length': len(response_text)
            })

        except Exception as e:
            elapsed = time.time() - start_time
            errors += 1

            print(f"  ✗ Error ({elapsed:.2f}s)")
            print(f"  Error: {str(e)[:80]}...")

            results.append({
                'invocation': i + 1,
                'query_type': query_type,
                'query': query,
                'success': False,
                'duration': elapsed,
                'error': str(e)
            })

        # Wait before next invocation
        if i < count - 1:
            print(f"  Waiting {delay}s...")
            time.sleep(delay)

    # Summary
    print("")
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Invocations: {count}")
    print(f"Successful: {count - errors}")
    print(f"Errors: {errors}")

    if results:
        successful_results = [r for r in results if r['success']]

        if successful_results:
            avg_duration = sum(r['duration'] for r in successful_results) / len(successful_results)
            print(f"Average Duration: {avg_duration:.2f}s")

            # Breakdown by complexity
            for query_type in ['simple', 'medium', 'complex']:
                type_results = [r for r in successful_results if r['query_type'] == query_type]
                if type_results:
                    avg = sum(r['duration'] for r in type_results) / len(type_results)
                    print(f"  {query_type.capitalize()}: {avg:.2f}s (n={len(type_results)})")

    print("")
    print("Analysis Notes:")
    print("  - Check log_pattern_analyzer.py output for detailed patterns")
    print("  - Logs will appear in Pub/Sub within 1-2 minutes")
    print("  - Each invocation generates ~15-40 logs depending on complexity")
    print("="*80)

def main():
    parser = argparse.ArgumentParser(description='Test Reasoning Engine invocations for log analysis')

    parser.add_argument(
        '--engine',
        type=str,
        required=True,
        help='Reasoning Engine name or ID (e.g., projects/PROJECT/locations/LOCATION/reasoningEngines/ID)'
    )

    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of invocations (default: 10)'
    )

    parser.add_argument(
        '--delay',
        type=int,
        default=5,
        help='Seconds between invocations (default: 5)'
    )

    parser.add_argument(
        '--complexity',
        type=str,
        choices=['simple', 'medium', 'complex', 'mixed'],
        default='mixed',
        help='Query complexity (default: mixed)'
    )

    args = parser.parse_args()

    test_invocations(
        reasoning_engine_name=args.engine,
        count=args.count,
        delay=args.delay,
        complexity=args.complexity
    )

if __name__ == "__main__":
    main()
