# Pub/Sub Monitoring Setup

Four monitoring approaches for Vertex AI Reasoning Engine logs via `vertex-telemetry-topic`.

## Portal26 Integration (Recommended)

**File:** `monitor_pubsub_to_portal26.py`

**Use case:** Forward GCP logs to Portal26 OTEL endpoint for unified observability

```bash
# Configure Portal26 endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.portal26.io
export OTEL_SERVICE_NAME=gcp-vertex-monitor

# Run forwarder
python monitoring_setup/monitor_pubsub_to_portal26.py
```

**Features:**
- Converts GCP logs to OTEL format
- Batches logs for efficient transmission (configurable batch size)
- Preserves trace context and severity levels
- Automatic retry on failures
- Real-time forwarding to Portal26

**Environment variables:**
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.portal26.io  # Portal26 endpoint
OTEL_SERVICE_NAME=gcp-vertex-monitor                  # Service identifier
PORTAL26_BATCH_SIZE=10                                # Logs per batch
PORTAL26_BATCH_TIMEOUT=5                              # Seconds before flush
```

---

## 1. Continuous Monitoring (24/7)

**File:** `monitor_pubsub_continuous.py`

**Use case:** Catch all logs in real-time, daily log rotation

```bash
# Run in background (Windows)
python monitoring_setup/monitor_pubsub_continuous.py

# Run as service (Linux with systemd)
sudo cp monitoring_setup/monitor-pubsub.service /etc/systemd/system/
sudo systemctl enable monitor-pubsub
sudo systemctl start monitor-pubsub
```

**Features:**
- Runs indefinitely until Ctrl+C
- Daily log rotation (one file per day)
- Progress stats every 100 messages
- Auto-creates `./pubsub_logs/` directory

## 2. Scheduled Collection (Hourly)

**File:** `monitor_pubsub_scheduled.py`

**Use case:** Periodic batch collection with statistics

```bash
# Run once (60 second pull)
python monitoring_setup/monitor_pubsub_scheduled.py

# Schedule with cron (every hour)
crontab -e
# Add: 0 * * * * cd /path/to/ai_agent_projectgcp && python monitoring_setup/monitor_pubsub_scheduled.py

# Windows Task Scheduler
# Import: monitoring_setup/scheduled-monitoring.xml
```

**Features:**
- Configurable timeout (default 60s)
- Batch statistics (severity counts, engine counts)
- JSON stats file per run
- Exit code 1 if errors detected

**Environment variables:**
```bash
PULL_TIMEOUT=120     # Pull duration in seconds
LOG_DIR=./pubsub_logs
```

## 3. Alert Monitoring (Real-time)

**File:** `monitor_pubsub_alerts.py`

**Use case:** Detect issues and send notifications

```bash
# Configure alerts
export ERROR_THRESHOLD=5
export WARNING_THRESHOLD=10
export WINDOW_SIZE=50
export ALERT_EMAIL=ops@example.com
export SMTP_HOST=smtp.gmail.com
export SMTP_USER=alerts@example.com
export SMTP_PASS=your-app-password

# Run
python monitoring_setup/monitor_pubsub_alerts.py
```

**Features:**
- Sliding window error/warning tracking
- Email alerts when thresholds exceeded
- Immediate console alerts if email not configured
- Logs all ERROR/CRITICAL/ALERT severity to console

## Configuration

All scripts support these environment variables:

```bash
# .env file
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription
LOG_DIR=./pubsub_logs

# Alert-specific
ERROR_THRESHOLD=5
WARNING_THRESHOLD=10
WINDOW_SIZE=50
ALERT_EMAIL=your-email@example.com
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-smtp-user
SMTP_PASS=your-smtp-password
```

## Comparison

| Approach | Run Mode | Best For | Resource Usage |
|----------|----------|----------|----------------|
| **Portal26 Forwarder** | Always on | Unified observability, production monitoring | Medium (streaming + batching) |
| **Continuous** | Always on | Local log capture, complete archive | High (always running) |
| **Scheduled** | Periodic | Cost-effective analysis, batch processing | Low (runs periodically) |
| **Alerts** | Always on | Issue detection, oncall notifications | Medium (targeted processing) |

## Setup Steps

1. **Create subscription** (if not exists):
```bash
gcloud pubsub subscriptions create vertex-telemetry-subscription \
  --topic=vertex-telemetry-topic \
  --project=agentic-ai-integration-490716
```

2. **Create logs directory**:
```bash
mkdir -p pubsub_logs
```

3. **Choose monitoring approach** and run

4. **Optional: Configure alerts** (for alert monitoring)

## Log Analysis

View daily logs:
```bash
cat pubsub_logs/reasoning_engine_logs_20260419.jsonl | python -m json.tool | less
```

Count by engine:
```bash
grep -o '"reasoning_engine_id":"[^"]*"' pubsub_logs/*.jsonl | sort | uniq -c
```

Find errors:
```bash
grep '"severity":"ERROR"' pubsub_logs/*.jsonl
```

Stats from scheduled runs:
```bash
cat pubsub_logs/batch_*_stats.json | jq .
```
