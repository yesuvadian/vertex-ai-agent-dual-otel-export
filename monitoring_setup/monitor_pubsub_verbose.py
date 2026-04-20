"""
Verbose Pub/Sub Monitor - Prints all logs to console
Perfect for manual testing and debugging
"""
import json
import os
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "agentic-ai-integration-490716")
TOPIC_ID = "vertex-telemetry-topic"
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "vertex-telemetry-subscription")
PULL_TIMEOUT = 60  # Run for 60 seconds

print("=" * 80)
print("VERBOSE PUB/SUB MONITOR - Manual Testing Mode")
print("=" * 80)
print(f"Project: {PROJECT_ID}")
print(f"Subscription: {SUBSCRIPTION_ID}")
print(f"Timeout: {PULL_TIMEOUT} seconds")
print("=" * 80)
print()

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

# Stats
total = 0
matched = 0

def callback(message):
    global total, matched
    total += 1

    try:
        # Parse log entry
        log_entry = json.loads(message.data.decode('utf-8'))

        # Extract key fields
        timestamp = log_entry.get('timestamp', 'unknown')
        severity = log_entry.get('severity', 'INFO')
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')
        resource_labels = resource.get('labels', {})
        reasoning_engine_id = resource_labels.get('reasoning_engine_id', 'unknown')

        text_payload = log_entry.get('textPayload', '')
        json_payload = log_entry.get('jsonPayload', {})

        trace = log_entry.get('trace', '')
        span_id = log_entry.get('spanId', '')

        print("\n" + "=" * 80)
        print(f"MESSAGE #{total}")
        print("=" * 80)
        print(f"Timestamp:      {timestamp}")
        print(f"Severity:       {severity}")
        print(f"Resource Type:  {resource_type}")
        print(f"Engine ID:      {reasoning_engine_id}")

        if trace:
            print(f"Trace ID:       {trace.split('/')[-1]}")
        if span_id:
            print(f"Span ID:        {span_id}")

        # Check if it's a Reasoning Engine log
        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            matched += 1
            print(f">>> MATCHED: Reasoning Engine Log #{matched} <<<")

            # Print payload
            if text_payload:
                print("\nText Payload:")
                print("-" * 40)
                print(text_payload[:500])  # First 500 chars
                if len(text_payload) > 500:
                    print(f"... (truncated, full length: {len(text_payload)} chars)")

            if json_payload:
                print("\nJSON Payload:")
                print("-" * 40)
                print(json.dumps(json_payload, indent=2)[:1000])  # First 1000 chars
                payload_str = json.dumps(json_payload)
                if len(payload_str) > 1000:
                    print(f"... (truncated, full length: {len(payload_str)} chars)")
        else:
            print(f">>> SKIPPED: Not a Reasoning Engine log <<<")

        message.ack()

    except Exception as e:
        print(f"\n[ERROR] Failed to process message: {e}")
        import traceback
        traceback.print_exc()
        message.ack()

print(f"Listening for {PULL_TIMEOUT} seconds...")
print("Press Ctrl+C to stop early")
print()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    streaming_pull_future.result(timeout=PULL_TIMEOUT)
except TimeoutError:
    print(f"\n[TIMEOUT] {PULL_TIMEOUT} seconds elapsed")
except KeyboardInterrupt:
    print("\n[STOPPED] User interrupted")
except Exception as e:
    print(f"\n[ERROR] {e}")
finally:
    streaming_pull_future.cancel()
    streaming_pull_future.result()

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total messages received:        {total}")
print(f"Reasoning Engine logs matched:  {matched}")
print()

if matched > 0:
    print("[SUCCESS] Found Reasoning Engine logs!")
    print()
    print("Next step: Run forwarder to send to Portal26")
    print("  python monitor_pubsub_to_portal26.py")
else:
    print("[INFO] No Reasoning Engine logs found")
    print()
    print("Try:")
    print("  1. Trigger a prompt in Google Console UI")
    print("  2. Wait 1-2 minutes for logs to flow")
    print("  3. Run this script again")
print()
