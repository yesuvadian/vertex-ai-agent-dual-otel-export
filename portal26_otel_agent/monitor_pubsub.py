"""
Monitor GCP Pub/Sub topic: vertex-telemetry-topic
Pull messages from Vertex AI Reasoning Engine log sink
"""
import json
import os
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ID = "agentic-ai-integration-490716"
TOPIC_ID = "vertex-telemetry-topic"
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "vertex-telemetry-subscription")

print("=" * 80)
print("MONITORING GCP PUB/SUB TOPIC: vertex-telemetry-topic")
print("=" * 80)
print(f"Project: {PROJECT_ID}")
print(f"Topic: {TOPIC_ID}")
print(f"Subscription: {SUBSCRIPTION_ID}")
print()

# Initialize Pub/Sub subscriber
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

print("[1/3] Checking subscription...")
try:
    subscription = subscriber.get_subscription(request={"subscription": subscription_path})
    print(f"[OK] Subscription exists: {subscription.name}")
    print(f"     Topic: {subscription.topic}")
    print(f"     Ack deadline: {subscription.ack_deadline_seconds}s")
except Exception as e:
    print(f"[WARN] Subscription not found: {e}")
    print()
    print("Creating subscription...")
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

        subscription = subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
                "ack_deadline_seconds": 60
            }
        )
        print(f"[OK] Created subscription: {subscription.name}")
    except Exception as create_error:
        print(f"[ERROR] Failed to create subscription: {create_error}")
        print()
        print("Create manually with:")
        print(f"  gcloud pubsub subscriptions create {SUBSCRIPTION_ID} \\")
        print(f"    --topic={TOPIC_ID} \\")
        print(f"    --project={PROJECT_ID}")
        exit(1)

print()
print("[2/3] Pulling messages from Pub/Sub...")
print("-" * 80)

total = 0
matched = 0
output_file = f"pubsub_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"

def callback(message):
    global total, matched
    total += 1

    try:
        # Parse the log entry
        log_entry = json.loads(message.data.decode('utf-8'))

        # Extract key fields
        timestamp = log_entry.get('timestamp', 'unknown')
        severity = log_entry.get('severity', 'INFO')
        resource = log_entry.get('resource', {})
        labels = log_entry.get('labels', {})
        text_payload = log_entry.get('textPayload', '')
        json_payload = log_entry.get('jsonPayload', {})

        # Get resource information
        resource_type = resource.get('type', 'unknown')
        resource_labels = resource.get('labels', {})
        reasoning_engine_id = resource_labels.get('reasoning_engine_id', 'unknown')

        # Get trace information
        trace = log_entry.get('trace', '')
        span_id = log_entry.get('spanId', '')

        # Print all messages (first 10 for sampling)
        if total <= 10:
            print(f"\n[SAMPLE {total}]")
            print(f"  Timestamp: {timestamp}")
            print(f"  Severity: {severity}")
            print(f"  Resource: {resource_type}")
            print(f"  Reasoning Engine: {reasoning_engine_id}")
            if trace:
                print(f"  Trace: {trace}")
            if span_id:
                print(f"  Span ID: {span_id}")
            if text_payload:
                print(f"  Text: {text_payload[:200]}")
            if json_payload:
                print(f"  JSON keys: {list(json_payload.keys())}")

        # Save all reasoning engine logs
        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            with open(output_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            matched += 1
            print(f"\n[MATCH {matched}]")
            print(f"  Timestamp: {timestamp}")
            print(f"  Severity: {severity}")
            print(f"  Engine ID: {reasoning_engine_id}")
            if trace:
                print(f"  Trace: {trace}")

        # Acknowledge the message
        message.ack()

    except Exception as e:
        print(f"\n[ERROR] Failed to process message: {e}")
        import traceback
        traceback.print_exc()
        # Acknowledge to avoid reprocessing
        message.ack()

print(f"Listening for messages (30 second timeout)...")
print(f"Press Ctrl+C to stop early")
print()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    # Wait for messages with timeout
    streaming_pull_future.result(timeout=30.0)
except TimeoutError:
    print("\n[TIMEOUT] 30 seconds elapsed")
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
print(f"Total messages received: {total}")
print(f"Reasoning Engine logs: {matched}")
if matched > 0:
    print(f"Output file: {output_file}")
print()

if matched > 0:
    print("[SUCCESS] Found Vertex AI Reasoning Engine logs!")
    print()
    print("View logs:")
    print(f"  cat {output_file} | python -m json.tool | head -100")
    print()
    print("Extract traces:")
    print(f"  grep -o '\"trace\":\"[^\"]*\"' {output_file}")
    print()
    print("Count by reasoning engine:")
    print(f"  grep -o '\"reasoning_engine_id\":\"[^\"]*\"' {output_file} | sort | uniq -c")
else:
    print("[INFO] No Reasoning Engine logs found in this pull")
    print()
    print("Troubleshooting:")
    print("  1. Check log sink configuration:")
    print(f"     gcloud logging sinks describe vertex-ai-telemetry-sink --project={PROJECT_ID}")
    print()
    print("  2. Check if messages are in the topic:")
    print(f"     gcloud pubsub topics list-subscriptions {TOPIC_ID} --project={PROJECT_ID}")
    print()
    print("  3. Make a test request to your Reasoning Engine and wait 1-2 minutes")
print()
