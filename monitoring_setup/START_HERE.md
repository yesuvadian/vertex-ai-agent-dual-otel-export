# 🚀 START HERE - Portal26 Integration

Forward GCP Vertex AI Reasoning Engine logs to Portal26 in **5 minutes**.

## ✅ Pre-configured

Your Portal26 configuration is **already set up** in `.env`:
- ✅ Endpoint: `https://otel-tenant1.portal26.in:4318`
- ✅ Authentication: Configured
- ✅ Tenant: `tenant1`
- ✅ User: `relusys_terraform`

## 🎯 Quick Start (3 commands)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Test
python test_portal26_connection.py

# 3. Run
python monitor_pubsub_to_portal26_v2.py
```

That's it! Logs will flow: **GCP → Portal26**

## 📊 Verify

Open Portal26 dashboard and search:
```
service.name = "gcp-vertex-monitor"
```

You should see Reasoning Engine logs appearing in real-time.

## 📚 Full Documentation

| Document | Purpose |
|----------|---------|
| **SETUP_GUIDE.md** | Complete setup instructions |
| **AWS_DEPLOYMENT.md** | Deploy to AWS (EC2/ECS/Lambda) |
| **PORTAL26_QUICKSTART.md** | Quick reference guide |
| **DEPLOYMENT_SUMMARY.md** | Architecture overview |

## 🛠️ Scripts

| Script | Purpose |
|--------|---------|
| **test_portal26_connection.py** | Test connectivity ⬅️ Start here |
| **monitor_pubsub_to_portal26_v2.py** | Production forwarder (OTEL SDK) ⭐ |
| monitor_pubsub_to_portal26.py | Alternative (HTTP-based) |
| monitor_pubsub.py | Test Pub/Sub only |

## ⚙️ Configuration

All settings in `.env` file (already configured):

**Portal26:**
- `OTEL_EXPORTER_OTLP_ENDPOINT` - Your endpoint
- `OTEL_EXPORTER_OTLP_HEADERS` - Auth credentials
- `PORTAL26_TENANT_ID` - Multi-tenancy

**GCP:**
- `GCP_PROJECT_ID` - Your GCP project
- `PUBSUB_SUBSCRIPTION` - Subscription name
- `GOOGLE_APPLICATION_CREDENTIALS` - Service account key path

## 🔧 Tuning

For high-volume logs:
```bash
PORTAL26_BATCH_SIZE=50
PORTAL26_BATCH_TIMEOUT=10
```

For low-latency:
```bash
PORTAL26_BATCH_SIZE=5
PORTAL26_BATCH_TIMEOUT=2
```

## 🚨 Troubleshooting

**No logs appearing?**
1. Run `python test_portal26_connection.py` - must show ✅ SUCCESS
2. Check Pub/Sub has messages
3. Verify Reasoning Engine is running

**Authentication error (401)?**
- Check credentials in `.env`
- Verify endpoint URL is correct

**Timeout?**
- Check network connectivity
- Verify firewall allows outbound HTTPS

See **SETUP_GUIDE.md** for detailed troubleshooting.

## 🌐 AWS Deployment

For production 24/7 monitoring:

**Option 1: EC2 (Recommended)**
- Cost: ~$10/month
- Setup: 10 minutes
- See: AWS_DEPLOYMENT.md

**Option 2: ECS Fargate**
- Cost: ~$20/month
- Fully managed
- See: AWS_DEPLOYMENT.md

## 📈 What Gets Forwarded

✅ All Vertex AI Reasoning Engine logs
✅ Trace IDs (when available)
✅ Severity levels (ERROR, WARN, INFO, DEBUG)
✅ Resource metadata (reasoning_engine_id)
✅ Timestamps
✅ Full log context

## 💡 Portal26 Queries

```
# All logs
service.name = "gcp-vertex-monitor"

# Your tenant only
tenant.id = "tenant1"

# Errors
severityText = "ERROR"

# Specific engine
resource.reasoning_engine_id = "your-id"
```

## ✨ Next Steps

1. ✅ Run: `python test_portal26_connection.py`
2. ✅ Run: `python monitor_pubsub_to_portal26_v2.py`
3. ✅ Check Portal26 dashboard
4. 🔄 Deploy to AWS (optional, for production)
5. 🔄 Create dashboards in Portal26
6. 🔄 Set up alerts

---

**Need help?** See `SETUP_GUIDE.md` for complete documentation.
