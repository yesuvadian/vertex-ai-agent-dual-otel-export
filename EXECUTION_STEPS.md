# Execution Steps - Dual Export Agent Testing

## Quick Start Guide

### Step 1: Verify Infrastructure is Running

```bash
# Check Docker collector is running
docker ps | grep otel-collector

# Check ngrok tunnel is active
curl http://localhost:4040/api/tunnels 2>/dev/null | python -m json.tool | grep public_url

# Expected output: "public_url": "https://tabetha-unelemental-bibulously.ngrok-free.dev"
```

**If not running:**
```bash
# Start Docker collector
docker-compose -f docker-compose-otel-collector.yml up -d

# Start ngrok (in separate terminal)
ngrok http 4318
```

---

### Step 2: Test the Agent via Console (Easiest Method)

1. **Open the Console:**
   ```
   https://console.cloud.google.com/vertex-ai/reasoning-engines/3691509684943978496?project=agentic-ai-integration-490716
   ```

2. **Click the "Test" tab** (or "Query" tab)

3. **Enter a test query:**
   - User ID: `test-user-123`
   - Message: `What is the weather in Tokyo?`

4. **Click "Send" or "Query"**

5. **Expected Response:**
   ```
   The weather in Tokyo is sunny, 28°C with clear skies.
   ```

---

### Step 3: Monitor Telemetry Data

#### Option A: ngrok Web UI (Real-time)
```bash
# Open in browser:
http://localhost:4040

# Look for POST requests to:
# /v1/traces
# /v1/logs
# /v1/metrics
```

#### Option B: Docker Collector Logs (Real-time)
```bash
# Watch collector processing data
docker logs local-otel-collector -f

# Press Ctrl+C to stop watching
```

#### Option C: Local Files (Stored Data)
```bash
# View traces
cat otel-data/otel-traces.json | python -m json.tool | tail -50

# View logs
cat otel-data/otel-logs.json | python -m json.tool | tail -50

# View metrics
cat otel-data/otel-metrics.json | python -m json.tool | tail -50

# Check file sizes (should grow with each query)
ls -lh otel-data/
```

#### Option D: Portal26 Dashboard
```
1. Open: https://portal26.in
2. Login with your credentials
3. Filter by:
   - service.name: ai-agent-engine
   - tenant_id: tenant1
   - user_id: relusys
```

---

### Step 4: Test via REST API (Advanced)

```bash
# Get auth token
TOKEN=$(gcloud auth print-access-token)

# Send query
curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/3691509684943978496:streamQuery" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What is the current time in London?",
      "user_id": "test-user-api"
    }
  }'
```

**Expected Response:**
```json
{"output": "The current time in London is..."}
```

---

### Step 5: Test via Python SDK (Advanced)

Create a test file:
```bash
cat > test_agent_quick.py << 'EOF'
import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agentic-ai-integration-490716-adk-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/3691509684943978496"
agent = reasoning_engines.ReasoningEngine(resource_name)

# Create session
session = agent.create_session(user_id="test-user-python")
print(f"Session ID: {session['id']}")

# Stream query
print("\nQuerying agent...")
response_stream = agent.stream_query(
    message="What is the weather in Paris?",
    user_id="test-user-python"
)

for event in response_stream:
    print(f"Event: {event}")

print("\nCheck telemetry at:")
print("- ngrok: http://localhost:4040")
print("- Local: otel-data/")
print("- Portal26: https://portal26.in")
EOF

# Run it
python test_agent_quick.py
```

---

## Complete Test Workflow

### Full End-to-End Test

```bash
# 1. Clear old data (optional)
rm otel-data/*.json 2>/dev/null

# 2. Start monitoring in one terminal
docker logs local-otel-collector -f

# 3. In another terminal, send a test query
TOKEN=$(gcloud auth print-access-token)
curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/3691509684943978496:streamQuery" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": {"message": "What is the weather in Tokyo?", "user_id": "test-user"}}'

# 4. Check data was received
ls -lh otel-data/

# 5. View the data
cat otel-data/otel-traces.json | python -m json.tool | tail -100
```

---

## Verification Checklist

After testing, verify:

- [ ] Agent responds with weather/time information
- [ ] ngrok shows incoming POST requests (http://localhost:4040)
- [ ] Docker logs show processing messages
- [ ] Local files exist and are growing:
  - [ ] otel-traces.json
  - [ ] otel-logs.json
  - [ ] otel-metrics.json
- [ ] Portal26 shows data (if you have access)

---

## Troubleshooting

### Problem: Agent not responding

```bash
# Check agent status
python list_all_agents.py

# Look for ai-agent-dual-export (Resource ID: 3691509684943978496)
```

### Problem: No telemetry data

```bash
# Check ngrok is running
curl http://localhost:4040/api/tunnels

# Check collector is running
docker ps | grep otel-collector

# Check collector logs for errors
docker logs local-otel-collector --tail=50
```

### Problem: Local files not updating

```bash
# Check file permissions
ls -la otel-data/

# Check collector configuration
cat otel-collector-config.yaml | grep -A 5 "file/"

# Restart collector
docker-compose -f docker-compose-otel-collector.yml restart
```

---

## Quick Commands Reference

```bash
# List all agents
python list_all_agents.py

# View agent in Console
https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716

# Monitor ngrok
http://localhost:4040

# Watch collector logs
docker logs local-otel-collector -f

# Check local data files
ls -lh otel-data/

# View traces
cat otel-data/otel-traces.json | python -m json.tool | tail -50

# Get auth token
gcloud auth print-access-token

# Test agent via curl
TOKEN=$(gcloud auth print-access-token)
curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines/3691509684943978496:streamQuery" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": {"message": "Test query", "user_id": "test-user"}}'
```

---

## Expected Results

### Successful Query Response:
```
Weather in Tokyo: 28°C, sunny
Current time in London: 2026-03-27 20:30:00 GMT
```

### ngrok UI (http://localhost:4040):
```
POST /v1/traces   200 OK   15ms
POST /v1/logs     200 OK   12ms
POST /v1/metrics  200 OK   18ms
```

### Local Files:
```
otel-traces.json   (growing)
otel-logs.json     (growing)
otel-metrics.json  (growing)
```

### Docker Logs:
```
info  Traces  {"resource": {"service.name": "ai-agent-engine"}}
info  Logs    {"log records": 2}
info  Metrics {"data points": 15}
```

---

## Next Steps

1. ✅ Test agent via Console (easiest)
2. ✅ Verify telemetry in ngrok UI
3. ✅ Check local files are updating
4. ✅ View data in Portal26 (optional)
5. ✅ Test with different queries
6. ✅ Monitor for 5-10 queries to see data accumulate

---

**Agent Resource ID:** 3691509684943978496
**Console URL:** https://console.cloud.google.com/vertex-ai/reasoning-engines/3691509684943978496?project=agentic-ai-integration-490716
**Project:** agentic-ai-integration-490716
**Region:** us-central1
