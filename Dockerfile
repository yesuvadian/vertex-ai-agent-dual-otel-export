# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent_manual.py .
COPY agent_router.py .
COPY app.py .
COPY telemetry.py .
# Note: .env is NOT copied - Cloud Run uses environment variables from deployment config

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/')" || exit 1

# Run the application
# Cloud Run sets PORT environment variable
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
