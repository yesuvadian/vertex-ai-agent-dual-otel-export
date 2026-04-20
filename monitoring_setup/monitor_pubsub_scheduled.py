"""
Scheduled monitoring (hourly pulls for analysis)
Run via cron or Windows Task Scheduler
Collects logs in batches and aggregates statistics
"""
import json
import os
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv
import sys

load_dotenv()

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "agentic-ai-integration-490716")
TOPIC_ID = "vertex-telemetry-topic"
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "vertex-telemetry-subscription")
LOG_DIR = os.environ.get("LOG_DIR", "./pubsub_logs")
PULL_TIMEOUT = int(os.environ.get("PULL_TIMEOUT", "60"))  # seconds

os.makedirs(LOG_DIR, exist_ok=True)

timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(LOG_DIR, f"batch_{timestamp}.jsonl")
stats_file = os.path.join(LOG_DIR, f"batch_{timestamp}_stats.json")

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled pull")
print(f"Project: {PROJECT_ID}, Timeout: {PULL_TIMEOUT}s")

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

total = 0
matched = 0
errors = 0
severity_counts = {}
engine_counts = {}

def callback(message):
    global total, matched, errors, severity_counts, engine_counts

    total += 1

    try:
        log_entry = json.loads(message.data.decode('utf-8'))

        severity = log_entry.get('severity', 'INFO')
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')
        resource_labels = resource.get('labels', {})
        reasoning_engine_id = resource_labels.get('reasoning_engine_id', 'unknown')

        # Track statistics
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            matched += 1
            engine_counts[reasoning_engine_id] = engine_counts.get(reasoning_engine_id, 0) + 1

        message.ack()

    except Exception as e:
        errors += 1
        print(f"[ERROR] {e}", file=sys.stderr)
        message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    streaming_pull_future.result(timeout=PULL_TIMEOUT)
except TimeoutError:
    pass
except Exception as e:
    print(f"[ERROR] {e}", file=sys.stderr)
finally:
    streaming_pull_future.cancel()
    streaming_pull_future.result()

# Save statistics
stats = {
    "timestamp": timestamp,
    "total_messages": total,
    "reasoning_engine_logs": matched,
    "errors": errors,
    "severity_counts": severity_counts,
    "engine_counts": engine_counts,
    "log_file": log_file if matched > 0 else None
}

with open(stats_file, 'w') as f:
    json.dump(stats, f, indent=2)

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Completed: {total} total, {matched} matched")
print(f"Stats: {stats_file}")

# Exit code for alerting
if errors > 0:
    sys.exit(1)
