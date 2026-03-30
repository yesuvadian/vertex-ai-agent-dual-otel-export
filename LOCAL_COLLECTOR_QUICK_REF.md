# 🚀 Local OTEL Collector - Quick Reference

---

## ⚡ Quick Start (3 Steps)

### 1. Start Collector
```bash
docker-compose -f docker-compose-otel-collector.yml up -d
```

### 2. Start ngrok
```bash
ngrok http 4318
```
**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### 3. Update Cloud Run
```bash
gcloud run services update ai-agent \
  --region=us-central1 \
  --update-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=https://YOUR_NGROK_URL"
```

---

## 📊 View Data

### Collector Logs
```bash
docker logs local-otel-collector -f
```

### ngrok Web Interface
```
http://localhost:4040
```

### Local Files
```bash
# View traces
cat otel-data/otel-traces.json

# View logs
cat otel-data/otel-logs.json

# View metrics
cat otel-data/otel-metrics.json
```

---

## 🧪 Test

```bash
TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://ai-agent-czvzx73drq-uc.a.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test local collector"}'
```

---

## 🛑 Stop

```bash
# Stop collector
docker-compose -f docker-compose-otel-collector.yml down

# Stop ngrok
Ctrl+C
```

---

## 🔄 Restart

```bash
docker-compose -f docker-compose-otel-collector.yml restart
```

---

## 📈 Check Status

```bash
# Collector status
docker ps | grep otel-collector

# View collector config
docker exec local-otel-collector cat /etc/otel-collector-config.yaml

# Check Cloud Run config
gcloud run services describe ai-agent --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)" | grep OTEL
```

---

## 🔧 Troubleshooting

### Collector not receiving data?
1. Check ngrok is running: http://localhost:4040
2. Check Cloud Run env var has correct ngrok URL
3. Check collector logs: `docker logs local-otel-collector`

### ngrok URL changed?
```bash
# Update Cloud Run with new URL
gcloud run services update ai-agent --region=us-central1 \
  --update-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=https://NEW_NGROK_URL"
```

### Reset everything
```bash
# Stop and remove
docker-compose -f docker-compose-otel-collector.yml down

# Remove data
rm -rf otel-data

# Start fresh
docker-compose -f docker-compose-otel-collector.yml up -d
mkdir otel-data
```

---

## 🔙 Revert to Portal26

```bash
gcloud run services update ai-agent \
  --region=us-central1 \
  --update-env-vars="OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318"
```

---

## 📁 Files

- `otel-collector-config.yaml` - Collector configuration
- `docker-compose-otel-collector.yml` - Docker setup
- `otel-data/` - Local telemetry data
- `LOCAL_OTEL_COLLECTOR_SETUP.md` - Full documentation

---

**Quick Help:** See `LOCAL_OTEL_COLLECTOR_SETUP.md` for detailed instructions
