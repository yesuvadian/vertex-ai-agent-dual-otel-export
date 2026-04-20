"""
Continuous 24/7 monitoring of vertex-telemetry-topic
Runs indefinitely until stopped (Ctrl+C)
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
LOG_DIR = os.environ.get("LOG_DIR", "./pubsub_logs")

os.makedirs(LOG_DIR, exist_ok=True)

print("=" * 80)
print("CONTINUOUS MONITORING: vertex-telemetry-topic")
print("=" * 80)
print(f"Project: {PROJECT_ID}")
print(f"Topic: {TOPIC_ID}")
print(f"Subscription: {SUBSCRIPTION_ID}")
print(f"Log directory: {LOG_DIR}")
print("Running continuously - Press Ctrl+C to stop")
print("=" * 80)
print()

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

# Stats
total = 0
matched = 0
errors = 0
current_date = None
current_file = None

def get_daily_log_file():
    """Create new log file for each day"""
    date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
    return os.path.join(LOG_DIR, f"reasoning_engine_logs_{date_str}.jsonl")

def callback(message):
    global total, matched, errors, current_date, current_file
    total += 1

    try:
        log_entry = json.loads(message.data.decode('utf-8'))

        timestamp = log_entry.get('timestamp', 'unknown')
        severity = log_entry.get('severity', 'INFO')
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')
        resource_labels = resource.get('labels', {})
        reasoning_engine_id = resource_labels.get('reasoning_engine_id', 'unknown')

        # Save Reasoning Engine logs
        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            # Rotate log file daily
            today = datetime.now(timezone.utc).date()
            if today != current_date:
                current_date = today
                current_file = get_daily_log_file()
                print(f"\n[LOG ROTATION] New file: {current_file}")

            with open(current_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            matched += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Log #{matched} | Engine: {reasoning_engine_id} | Severity: {severity}")

        message.ack()

        # Print stats every 100 messages
        if total % 100 == 0:
            print(f"\n--- Stats: {total} total, {matched} matched, {errors} errors ---\n")

    except Exception as e:
        errors += 1
        print(f"\n[ERROR] Failed to process message: {e}")
        message.ack()

print("Starting listener...")
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    # Run indefinitely (no timeout)
    streaming_pull_future.result()
except KeyboardInterrupt:
    print("\n\n[STOPPED] User interrupted")
finally:
    streaming_pull_future.cancel()
    streaming_pull_future.result()

print()
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Total messages: {total}")
print(f"Reasoning Engine logs: {matched}")
print(f"Errors: {errors}")
if matched > 0:
    print(f"Latest log file: {current_file}")
print()
