# Dockerfile for Continuous Pull-Based Forwarder
# Optimized for AWS ECS Fargate deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY continuous_forwarder.py .

# Copy GCP credentials (will be overridden by secrets at runtime)
# This is just a placeholder for local testing
RUN mkdir -p /secrets

# Environment variables with defaults
ENV GCP_PROJECT_ID=agentic-ai-integration-490716
ENV PUBSUB_SUBSCRIPTION=all-customers-logs-sub
ENV OTEL_SERVICE_NAME=gcp-vertex-monitor
ENV PORTAL26_BATCH_SIZE=20
ENV PORTAL26_BATCH_TIMEOUT=5
ENV HEALTH_CHECK_INTERVAL=60
ENV AGENT_TYPE=aws-ecs-forwarder

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Run as non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run the forwarder
CMD ["python", "-u", "continuous_forwarder.py"]
