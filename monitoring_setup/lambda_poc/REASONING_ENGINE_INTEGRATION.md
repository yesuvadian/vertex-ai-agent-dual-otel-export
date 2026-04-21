# GCP Vertex AI Reasoning Engine + Pub/Sub + AWS Lambda Integration

## Architecture Overview

```
GCP Customer Monitoring Data
        ↓
    Pub/Sub Topic
        ↓
Vertex AI Reasoning Engine (AI Agent)
    - Log analysis
    - Anomaly detection
    - Data enrichment
    - Intelligent routing
        ↓
    AWS Lambda
        ↓
Portal26 OTEL Endpoint
```

---

## Components

### 1. Pub/Sub Topic
- **Topic**: `test-topic`
- **Role**: Message broker for monitoring data
- **Status**: ✅ Created

### 2. Vertex AI Reasoning Engine
- **Service**: Cloud Run with Reasoning Engine runtime
- **AI Model**: Gemini 1.5 Pro/Flash
- **Functions**:
  - Analyze log patterns
  - Detect anomalies
  - Enrich metadata
  - Filter/route messages
  - Generate insights

### 3. AWS Lambda
- **Function**: `gcp-pubsub-test`
- **URL**: `https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/`
- **Role**: Forward to Portal26
- **Status**: ✅ Deployed

---

## Implementation Steps

### Phase 1: Create Reasoning Engine Agent

**1.1 Create Agent Code**

`reasoning_agent.py`:
```python
"""
Vertex AI Reasoning Engine Agent
Analyzes GCP Pub/Sub messages before forwarding to AWS Lambda
"""
import os
import json
import base64
import requests
from datetime import datetime
from vertexai.preview import reasoning_engines
import vertexai

# Initialize Vertex AI
PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
AWS_LAMBDA_URL = "https://klxwmowvbumembf63ikfl5q3de0iiygk.lambda-url.us-east-1.on.aws/"

vertexai.init(project=PROJECT_ID, location=LOCATION)

class MonitoringAgent:
    """AI Agent for monitoring data analysis"""
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        
    def analyze_log_message(self, message_data: str) -> dict:
        """
        Analyze log message for anomalies and insights
        
        Args:
            message_data: Decoded Pub/Sub message content
            
        Returns:
            Analysis results with severity, category, insights
        """
        # AI analysis prompt
        prompt = f"""
        Analyze this monitoring log/metric data:
        
        {message_data}
        
        Provide:
        1. Severity (LOW, MEDIUM, HIGH, CRITICAL)
        2. Category (error, warning, info, metric, trace)
        3. Anomaly detection (true/false)
        4. Key insights (brief summary)
        5. Recommended action
        
        Return as JSON format.
        """
        
        # Simple rule-based analysis (replace with Gemini API call)
        analysis = {
            "severity": "INFO",
            "category": "info",
            "anomaly_detected": False,
            "insights": "Normal monitoring data",
            "recommended_action": "forward_to_portal26",
            "ai_processed": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check for error keywords
        if any(keyword in message_data.lower() for keyword in ['error', 'exception', 'failed', 'critical']):
            analysis["severity"] = "HIGH"
            analysis["category"] = "error"
            analysis["anomaly_detected"] = True
            analysis["recommended_action"] = "alert_and_forward"
            
        return analysis
    
    def enrich_message(self, original_message: dict, analysis: dict) -> dict:
        """
        Enrich original message with AI analysis
        
        Args:
            original_message: Original Pub/Sub message
            analysis: AI analysis results
            
        Returns:
            Enriched message with AI metadata
        """
        enriched = {
            "original_message": original_message,
            "ai_analysis": analysis,
            "processing_time": datetime.utcnow().isoformat(),
            "agent_version": "1.0.0"
        }
        return enriched
    
    def forward_to_lambda(self, enriched_message: dict) -> dict:
        """
        Forward enriched message to AWS Lambda
        
        Args:
            enriched_message: Message with AI analysis
            
        Returns:
            Lambda response
        """
        try:
            response = requests.post(
                AWS_LAMBDA_URL,
                json=enriched_message,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            return {
                "status": "success",
                "lambda_status_code": response.status_code,
                "lambda_response": response.json()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def process_pubsub_message(self, pubsub_message: dict) -> dict:
        """
        Main processing function for Pub/Sub messages
        
        Args:
            pubsub_message: Raw Pub/Sub push message
            
        Returns:
            Processing result
        """
        print(f"[{datetime.utcnow().isoformat()}] Reasoning Engine processing message")
        
        # Extract and decode message data
        message = pubsub_message.get('message', {})
        encoded_data = message.get('data', '')
        
        try:
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        except Exception as e:
            decoded_data = f"[Decode error: {str(e)}]"
        
        print(f"Message data: {decoded_data[:100]}")
        
        # AI Analysis
        analysis = self.analyze_log_message(decoded_data)
        print(f"AI Analysis: {json.dumps(analysis, indent=2)}")
        
        # Enrich message
        enriched_message = self.enrich_message(
            original_message={
                "data": encoded_data,
                "messageId": message.get('messageId'),
                "publishTime": message.get('publishTime')
            },
            analysis=analysis
        )
        
        # Forward to AWS Lambda
        lambda_result = self.forward_to_lambda(enriched_message)
        print(f"Lambda result: {json.dumps(lambda_result, indent=2)}")
        
        return {
            "status": "success",
            "agent_processed": True,
            "analysis": analysis,
            "lambda_forwarded": lambda_result.get("status") == "success"
        }


def pubsub_handler(request):
    """
    Cloud Run handler for Pub/Sub push messages
    Compatible with Pub/Sub push subscription format
    """
    try:
        # Parse request
        request_json = request.get_json()
        
        # Initialize agent
        agent = MonitoringAgent()
        
        # Process message
        result = agent.process_pubsub_message(request_json)
        
        # Return 200 to acknowledge message
        return json.dumps(result), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return 500 for retry
        return json.dumps({
            "status": "error",
            "error": str(e)
        }), 500, {'Content-Type': 'application/json'}
```

**1.2 Create Requirements**

`requirements.txt`:
```
google-cloud-aiplatform>=1.38.0
vertexai>=0.0.1
requests>=2.31.0
flask>=3.0.0
gunicorn>=21.2.0
```

**1.3 Create Dockerfile**

`Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reasoning_agent.py .

# Cloud Run uses PORT environment variable
ENV PORT=8080

# Run with gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 reasoning_agent:pubsub_handler
```

---

### Phase 2: Deploy Reasoning Engine

**2.1 Build Container**

```bash
# Set variables
export PROJECT_ID="agentic-ai-integration-490716"
export REGION="us-central1"
export SERVICE_NAME="monitoring-reasoning-agent"

# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --project $PROJECT_ID
```

**2.2 Deploy to Cloud Run**

```bash
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars PROJECT_ID=$PROJECT_ID \
  --project $PROJECT_ID
```

**2.3 Get Service URL**

```bash
export SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "Reasoning Engine URL: $SERVICE_URL"
```

---

### Phase 3: Connect Pub/Sub to Reasoning Engine

**3.1 Delete Old Subscription**

```bash
gcloud pubsub subscriptions delete aws-lambda-push-sub \
  --project $PROJECT_ID
```

**3.2 Create Service Account**

```bash
gcloud iam service-accounts create pubsub-reasoning-invoker \
  --display-name "Pub/Sub to Reasoning Engine Invoker" \
  --project $PROJECT_ID

export SA_EMAIL="pubsub-reasoning-invoker@$PROJECT_ID.iam.gserviceaccount.com"

# Grant Cloud Run invoker permission
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.invoker" \
  --region=$REGION \
  --project=$PROJECT_ID
```

**3.3 Create New Push Subscription**

```bash
gcloud pubsub subscriptions create reasoning-engine-sub \
  --topic test-topic \
  --push-endpoint $SERVICE_URL \
  --push-auth-service-account $SA_EMAIL \
  --project $PROJECT_ID
```

---

### Phase 4: Test End-to-End

**4.1 Publish Test Message**

```bash
gcloud pubsub topics publish test-topic \
  --message "Test message with ERROR in logs" \
  --project $PROJECT_ID
```

**4.2 Check Reasoning Engine Logs**

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --limit 20 \
  --format json \
  --project $PROJECT_ID
```

**4.3 Check Lambda Logs**

```bash
MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/gcp-pubsub-test \
  --since 2m \
  --region us-east-1
```

---

## Message Flow Example

### Original Message
```json
{
  "message": {
    "data": "SGVsbG8gZnJvbSBHQ1A=",
    "messageId": "123456",
    "publishTime": "2026-04-21T10:00:00Z"
  }
}
```

### After Reasoning Engine Processing
```json
{
  "original_message": {
    "data": "SGVsbG8gZnJvbSBHQ1A=",
    "messageId": "123456",
    "publishTime": "2026-04-21T10:00:00Z"
  },
  "ai_analysis": {
    "severity": "INFO",
    "category": "info",
    "anomaly_detected": false,
    "insights": "Normal monitoring data",
    "recommended_action": "forward_to_portal26",
    "ai_processed": true,
    "timestamp": "2026-04-21T10:00:01.123Z"
  },
  "processing_time": "2026-04-21T10:00:01.234Z",
  "agent_version": "1.0.0"
}
```

### Lambda Receives Enriched Data
Lambda gets the full enriched message with AI analysis, then forwards to Portal26.

---

## Cost Estimate

### Per Month (10K messages)

| Component | Usage | Cost |
|-----------|-------|------|
| **Pub/Sub** | 10K messages | $0.40 |
| **Cloud Run** | 10K requests, 1s avg | $0.24 |
| **Gemini API** | (optional) 10K calls | $0.50 |
| **AWS Lambda** | 10K invocations | $0.20 |
| **Total** | | **$1.34/month** |

### Benefits of Reasoning Engine

✅ AI-powered log analysis  
✅ Anomaly detection  
✅ Intelligent filtering (reduce noise)  
✅ Data enrichment  
✅ Automatic severity classification  
✅ Cost reduction (filter before Lambda)  

---

## Use Cases

### 1. Anomaly Detection
```python
if analysis["anomaly_detected"]:
    send_alert(message)
    priority_forward_to_lambda(message)
```

### 2. Intelligent Filtering
```python
if analysis["severity"] == "LOW":
    log_to_bigquery(message)  # Don't forward to Lambda
else:
    forward_to_lambda(message)
```

### 3. Data Enrichment
```python
enriched = {
    "original": message,
    "geo_ip": lookup_ip(message.source_ip),
    "threat_score": analyze_threat(message),
    "ai_summary": generate_summary(message)
}
```

### 4. Multi-Customer Routing
```python
if message.customer_id == "customer-a":
    forward_to_lambda_a(message)
elif message.customer_id == "customer-b":
    forward_to_lambda_b(message)
```

---

## Next Steps

1. ✅ Create Reasoning Engine code
2. ⏳ Deploy to Cloud Run
3. ⏳ Connect Pub/Sub → Reasoning Engine
4. ⏳ Test with AI analysis
5. ⏳ Add Gemini API for advanced AI
6. ⏳ Implement anomaly detection
7. ⏳ Scale to multiple customers

---

## Advanced: Add Gemini AI

Replace rule-based analysis with Gemini:

```python
from vertexai.generative_models import GenerativeModel

def analyze_with_gemini(self, message_data: str) -> dict:
    """Use Gemini for intelligent analysis"""
    model = GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Analyze this monitoring data and respond in JSON:
    
    {message_data}
    
    Provide: severity, category, anomaly_detected, insights, recommended_action
    """
    
    response = model.generate_content(prompt)
    return json.loads(response.text)
```

Cost: ~$0.00005 per analysis (Gemini Flash)

---

## Monitoring

### Cloud Run Metrics
- Request count
- Request latency
- Error rate
- CPU/Memory usage

### Custom Metrics
```python
from google.cloud import monitoring_v3

def log_metric(metric_name, value):
    """Log custom metric to Cloud Monitoring"""
    client = monitoring_v3.MetricServiceClient()
    # ... record metric
```

---

## Deployment Commands Quick Reference

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/monitoring-reasoning-agent
gcloud run deploy monitoring-reasoning-agent --image gcr.io/$PROJECT_ID/monitoring-reasoning-agent

# Create subscription
gcloud pubsub subscriptions create reasoning-engine-sub \
  --topic test-topic \
  --push-endpoint <CLOUD_RUN_URL>

# Test
gcloud pubsub topics publish test-topic --message "Test ERROR message"

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 20
```
