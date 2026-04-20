"""
Real-time alert monitoring for Reasoning Engine logs
Detects issues and sends notifications
"""
import json
import os
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "agentic-ai-integration-490716")
TOPIC_ID = "vertex-telemetry-topic"
SUBSCRIPTION_ID = os.environ.get("PUBSUB_SUBSCRIPTION", "vertex-telemetry-subscription")
LOG_DIR = os.environ.get("LOG_DIR", "./pubsub_logs")

# Alert thresholds
ERROR_THRESHOLD = int(os.environ.get("ERROR_THRESHOLD", "5"))  # errors in window
WARNING_THRESHOLD = int(os.environ.get("WARNING_THRESHOLD", "10"))  # warnings in window
WINDOW_SIZE = int(os.environ.get("WINDOW_SIZE", "50"))  # sliding window

# Notification config
ALERT_EMAIL = os.environ.get("ALERT_EMAIL")
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

os.makedirs(LOG_DIR, exist_ok=True)

print("=" * 80)
print("ALERT MONITORING: vertex-telemetry-topic")
print("=" * 80)
print(f"Project: {PROJECT_ID}")
print(f"Error threshold: {ERROR_THRESHOLD} in {WINDOW_SIZE} messages")
print(f"Warning threshold: {WARNING_THRESHOLD} in {WINDOW_SIZE} messages")
if ALERT_EMAIL:
    print(f"Alerts to: {ALERT_EMAIL}")
print("=" * 80)
print()

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

# Sliding window tracking
recent_severities = []
total = 0
alerts_sent = 0

def send_alert(subject, body):
    """Send email alert (if configured)"""
    global alerts_sent

    if not all([ALERT_EMAIL, SMTP_HOST, SMTP_USER, SMTP_PASS]):
        print(f"\n[ALERT] {subject}")
        print(body)
        return

    try:
        msg = MIMEText(body)
        msg['Subject'] = f"[Reasoning Engine] {subject}"
        msg['From'] = SMTP_USER
        msg['To'] = ALERT_EMAIL

        with smtplib.SMTP(SMTP_HOST, 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        alerts_sent += 1
        print(f"\n[ALERT SENT] {subject}")

    except Exception as e:
        print(f"\n[ALERT FAILED] {e}")
        print(f"Subject: {subject}")
        print(body)

def check_alerts():
    """Check if alert thresholds are exceeded"""
    if len(recent_severities) < WINDOW_SIZE:
        return

    error_count = recent_severities.count('ERROR')
    warning_count = recent_severities.count('WARNING')

    if error_count >= ERROR_THRESHOLD:
        send_alert(
            f"High Error Rate Detected ({error_count} errors)",
            f"Detected {error_count} ERROR logs in the last {WINDOW_SIZE} messages.\n\n"
            f"Total messages processed: {total}\n"
            f"Check logs in: {LOG_DIR}\n"
        )

    if warning_count >= WARNING_THRESHOLD:
        send_alert(
            f"High Warning Rate ({warning_count} warnings)",
            f"Detected {warning_count} WARNING logs in the last {WINDOW_SIZE} messages.\n\n"
            f"Total messages processed: {total}\n"
            f"Check logs in: {LOG_DIR}\n"
        )

def callback(message):
    global total, recent_severities

    total += 1

    try:
        log_entry = json.loads(message.data.decode('utf-8'))

        timestamp = log_entry.get('timestamp', 'unknown')
        severity = log_entry.get('severity', 'INFO')
        resource = log_entry.get('resource', {})
        resource_type = resource.get('type', 'unknown')
        resource_labels = resource.get('labels', {})
        reasoning_engine_id = resource_labels.get('reasoning_engine_id', 'unknown')

        if resource_type == "aiplatform.googleapis.com/ReasoningEngine":
            # Log all reasoning engine messages
            log_file = os.path.join(LOG_DIR, f"alerts_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl")
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            # Track severity in sliding window
            recent_severities.append(severity)
            if len(recent_severities) > WINDOW_SIZE:
                recent_severities.pop(0)

            # Print important logs
            if severity in ['ERROR', 'CRITICAL', 'ALERT']:
                print(f"\n[{severity}] {timestamp}")
                print(f"  Engine: {reasoning_engine_id}")
                text_payload = log_entry.get('textPayload', '')
                if text_payload:
                    print(f"  Message: {text_payload[:200]}")

            # Check alert conditions
            check_alerts()

        message.ack()

        # Progress indicator
        if total % 10 == 0:
            error_count = recent_severities.count('ERROR')
            warning_count = recent_severities.count('WARNING')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed: {total} | Window: {error_count}E {warning_count}W")

    except Exception as e:
        print(f"\n[PROCESSING ERROR] {e}")
        message.ack()

print("Starting alert monitor...")
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    streaming_pull_future.result()
except KeyboardInterrupt:
    print("\n\n[STOPPED] User interrupted")
finally:
    streaming_pull_future.cancel()
    streaming_pull_future.result()

print()
print("=" * 80)
print("MONITORING SUMMARY")
print("=" * 80)
print(f"Total messages: {total}")
print(f"Alerts sent: {alerts_sent}")
print()
