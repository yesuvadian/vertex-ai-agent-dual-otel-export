# 🔧 Local OTEL Collector Setup with ngrok

**Purpose:** Run OpenTelemetry Collector locally and receive telemetry from Cloud Run via ngrok

---

## 📋 Architecture

```
Cloud Run (ai-agent)
        ↓
    ngrok tunnel (public URL)
        ↓
Local OTEL Collector (localhost:4318)
        ↓
    ├─→ Portal26 (forward)
    ├─→ Local Files (store)
    └─→ Console (debug)
```

---

## 🚀 Quick Start

### Step 1: Install Prerequisites

**Docker Desktop** (for running collector):
- Windows: https://docs.docker.com/desktop/install/windows-install/
- Or use Docker CLI

**ngrok** (for exposing local endpoint):
```bash
# Download from: https://ngrok.com/download
# Or install via chocolatey:
choco install ngrok

# Or via scoop:
scoop install ngrok
```

---

### Step 2: Start Local OTEL Collector

```bash
# Navigate to project directory
cd C:\Yesu\ai_agent_projectgcp

# Create data directory for logs
mkdir otel-data

# Start the collector
docker-compose -f docker-compose-otel-collector.yml up -d

# Verify it's running
docker ps | grep otel-collector
```

**Expected Output:**
```
local-otel-collector   Up   0.0.0.0:4318->4318/tcp
```

---

### Step 3: Expose Collector with ngrok

```bash
# Start ngrok tunnel
ngrok http 4318
```

**Expected Output:**
```
ngrok

Session Status                online
Account                       your-account
Region                        United States (us)
Forwarding                    https://abc123.ngrok.io -> http://localhost:4318
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

---

### Step 4: Update Cloud Run to Use Local Collector

```bash
# Replace YOUR_NGROK_URL with your actual ngrok URL
gcloud run services update ai-agent \
  --region=us-central1 \
  --update-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=https://YOUR_NGROK_URL" \
  --update-env-vars="OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="
```

**Example:**
```bash
gcloud run services update ai-agent \
  --region=us-central1 \
  --update-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=https://abc123.ngrok.io" \
  --update-env-vars="OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="
```

---

### Step 5: Test the Setup

**Send a test request:**
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://ai-agent-czvzx73drq-uc.a.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test with local collector - Weather in Tokyo"}'
```

---

### Step 6: Verify Data Received

**Check collector logs:**
```bash
docker logs local-otel-collector --tail=50 -f
```

**Check local files:**
```bash
# Traces
cat otel-data/otel-traces.json | tail -20

# Logs
cat otel-data/otel-logs.json | tail -20

# Metrics
cat otel-data/otel-metrics.json | tail -20
```

**View ngrok requests:**
- Open: http://localhost:4040
- See all requests to your local collector

---

## 📊 Monitoring Your Local Collector

### ngrok Web Interface

**URL:** http://localhost:4040

Shows:
- All incoming requests
- Request/response details
- Timing information

### Collector Logs

```bash
# View real-time logs
docker logs local-otel-collector -f

# View last 100 lines
docker logs local-otel-collector --tail=100
```

### Local File Storage

Files are stored in: `C:\Yesu\ai_agent_projectgcp\otel-data\`

- `otel-traces.json` - Trace data
- `otel-logs.json` - Log entries
- `otel-metrics.json` - Metrics data

---

## 🔧 Configuration Options

### Option 1: Local Only (No Portal26 forwarding)

Edit `otel-collector-config.yaml`:

```yaml
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [file/traces, logging]  # Remove otlp/portal26

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [file/metrics, logging]  # Remove otlp/portal26

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [file/logs, logging]  # Remove otlp/portal26
```

Then restart:
```bash
docker-compose -f docker-compose-otel-collector.yml restart
```

---

### Option 2: Multiple Backends

Add more exporters:

```yaml
exporters:
  # Portal26
  otlp/portal26:
    endpoint: https://otel-tenant1.portal26.in:4318
    headers:
      Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==

  # Jaeger for traces
  jaeger:
    endpoint: localhost:14250
    tls:
      insecure: true

  # Prometheus for metrics
  prometheus:
    endpoint: "0.0.0.0:8889"

  # Local files
  file/logs:
    path: ./otel-logs.json

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/portal26, jaeger, file/traces, logging]

    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/portal26, prometheus, file/metrics, logging]
```

---

### Option 3: Filtering/Sampling

Add filtering processor:

```yaml
processors:
  filter/drop-noisy:
    metrics:
      exclude:
        match_type: regexp
        metric_names:
          - ".*health.*"
          - ".*ping.*"

  probabilistic_sampler:
    sampling_percentage: 10  # Only keep 10% of traces

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [probabilistic_sampler, batch]
      exporters: [otlp/portal26, file/traces]
```

---

## 🛠️ Troubleshooting

### Issue 1: Collector Not Starting

**Check logs:**
```bash
docker logs local-otel-collector
```

**Common fixes:**
```bash
# Stop and remove
docker-compose -f docker-compose-otel-collector.yml down

# Start fresh
docker-compose -f docker-compose-otel-collector.yml up -d
```

---

### Issue 2: ngrok Connection Issues

**Check ngrok status:**
```bash
# View ngrok web interface
http://localhost:4040
```

**Restart ngrok:**
```bash
# Stop (Ctrl+C)
# Start again
ngrok http 4318
```

---

### Issue 3: Cloud Run Not Sending Data

**Verify environment variable:**
```bash
gcloud run services describe ai-agent --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)" | grep OTEL_EXPORTER
```

**Should show your ngrok URL:**
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://abc123.ngrok.io
```

---

### Issue 4: No Data in Local Files

**Check collector config:**
```bash
docker exec local-otel-collector cat /etc/otel-collector-config.yaml
```

**Check file permissions:**
```bash
ls -la otel-data/
```

**Restart collector:**
```bash
docker-compose -f docker-compose-otel-collector.yml restart
```

---

## 📈 Testing the Setup

### Complete Test Script

```bash
echo "Testing Local OTEL Collector Setup"
echo "==================================="
echo ""

# 1. Check collector is running
echo "1. Checking collector status..."
docker ps | grep otel-collector
echo ""

# 2. Check ngrok tunnel
echo "2. ngrok tunnel (visit http://localhost:4040)"
echo ""

# 3. Send test request
echo "3. Sending test request to Cloud Run..."
TOKEN=$(gcloud auth print-identity-token)
curl -s -X POST https://ai-agent-czvzx73drq-uc.a.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Local collector test - Weather in Paris"}'
echo ""
echo ""

# 4. Wait for data
echo "4. Waiting for telemetry data (10 seconds)..."
sleep 10

# 5. Check local files
echo "5. Checking local trace file..."
if [ -f "otel-data/otel-traces.json" ]; then
    echo "Traces received! Last entry:"
    tail -5 otel-data/otel-traces.json
else
    echo "No trace file yet"
fi
echo ""

# 6. Check collector logs
echo "6. Collector logs (last 10 lines):"
docker logs local-otel-collector --tail=10

echo ""
echo "==================================="
echo "Test complete!"
```

---

## 🔒 Security Considerations

### ngrok Free vs Paid

**Free Tier:**
- URL changes on restart
- Need to update Cloud Run each time
- Limited connections

**Paid Tier ($8/month):**
- Fixed domain (e.g., `myapp.ngrok.io`)
- No need to update Cloud Run
- Better for long-term use

### Alternative: Use ngrok Reserved Domain

```bash
# With ngrok authtoken
ngrok authtoken YOUR_TOKEN

# Start with fixed domain
ngrok http --domain=your-domain.ngrok.io 4318
```

---

## 📊 Viewing Data

### Local Files (JSON)

```bash
# Pretty print traces
cat otel-data/otel-traces.json | python -m json.tool | less

# Count entries
wc -l otel-data/otel-logs.json

# Search for specific data
grep "Weather in Tokyo" otel-data/otel-logs.json
```

### Using jq (Advanced)

```bash
# Install jq (JSON processor)
choco install jq

# Extract specific fields
cat otel-data/otel-traces.json | jq '.resourceSpans[].scopeSpans[].spans[].name'

# Filter by attribute
cat otel-data/otel-logs.json | jq 'select(.body.stringValue | contains("Weather"))'
```

---

## 🎯 Production Setup

For production, instead of ngrok, consider:

### Option A: Cloud Run with Public IP
Deploy collector as Cloud Run service with public endpoint

### Option B: GCP VM with Static IP
Run collector on VM with firewall rules

### Option C: Cloud Load Balancer
Use load balancer with SSL certificate

---

## 🔄 Switching Back to Portal26

To revert Cloud Run to send directly to Portal26:

```bash
gcloud run services update ai-agent \
  --region=us-central1 \
  --update-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318" \
  --update-env-vars="OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="
```

---

## 📋 Quick Commands Reference

### Start Collector
```bash
docker-compose -f docker-compose-otel-collector.yml up -d
```

### Start ngrok
```bash
ngrok http 4318
```

### View Collector Logs
```bash
docker logs local-otel-collector -f
```

### View ngrok Requests
```bash
# Open browser
http://localhost:4040
```

### Stop Everything
```bash
# Stop collector
docker-compose -f docker-compose-otel-collector.yml down

# Stop ngrok
Ctrl+C (in ngrok terminal)
```

---

## ✅ Checklist

- [ ] Docker installed and running
- [ ] ngrok installed
- [ ] Collector started (`docker ps` shows running)
- [ ] ngrok tunnel started (note URL)
- [ ] Cloud Run updated with ngrok URL
- [ ] Test request sent
- [ ] Data visible in local files
- [ ] ngrok web interface showing requests
- [ ] Collector logs showing activity

---

**Setup Complete!** Your local OTEL collector is now receiving telemetry from Cloud Run! 🎉

---

**Version:** 1.0
**Last Updated:** 2026-03-27
