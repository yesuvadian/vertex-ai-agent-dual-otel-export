FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy monitoring scripts
COPY monitor_pubsub_continuous.py .
COPY monitor_pubsub_scheduled.py .
COPY monitor_pubsub_alerts.py .
COPY monitor_pubsub_to_portal26.py .

# Create log directory
RUN mkdir -p /app/pubsub_logs

# Default to Portal26 forwarder
CMD ["python", "monitor_pubsub_to_portal26.py"]
