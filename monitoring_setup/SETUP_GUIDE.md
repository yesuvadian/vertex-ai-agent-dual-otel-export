# Complete Setup Guide - GCP Pub/Sub to Portal26

## Your Portal26 Configuration

✅ **Endpoint:** `https://otel-tenant1.portal26.in:4318`
✅ **Tenant:** `tenant1`
✅ **User:** `relusys_terraform`
✅ **Auth:** Basic authentication (titaniam:helloworld)
✅ **Protocol:** HTTP/Protobuf

## Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
cd monitoring_setup
pip install -r requirements.txt
```

### Step 2: Configuration Already Done!

Your `.env` file is already configured with:
- ✅ Portal26 endpoint
- ✅ Authentication credentials
- ✅ Multi-tenant attributes
- ✅ GCP project settings

### Step 3: Test Portal26 Connection

```bash
python test_portal26_connection.py
```

**Expected output:**
```
✅ SUCCESS - Portal26 connection working!
```

If it fails, check:
- Network connectivity to `otel-tenant1.portal26.in:4318`
- Firewall rules allow outbound HTTPS
- Credentials are correct

### Step 4: Test Pub/Sub (Optional)

```bash
python monitor_pubsub.py
```

This pulls messages for 30 seconds to verify Pub/Sub is working.

### Step 5: Start Forwarder

**Option A: JSON-based forwarder (simpler)**
```bash
python monitor_pubsub_to_portal26.py
```

**Option B: OTEL SDK-based forwarder (recommended)**
```bash
python monitor_pubsub_to_portal26_v2.py
```

### Step 6: Verify in Portal26

1. Log into Portal26 dashboard
2. Navigate to **Logs** section
3. Search for: `service.name = "gcp-vertex-monitor"`
4. Filter by: `tenant.id = "tenant1"`
5. Look for logs with `resource.reasoning_engine_id`

## Script Comparison

| Script | Technology | Best For | Complexity |
|--------|-----------|----------|------------|
| `monitor_pubsub_to_portal26.py` | Direct HTTP requests | Quick testing, simple debugging | Low |
| `monitor_pubsub_to_portal26_v2.py` | OTEL SDK | Production, proper protobuf support | Medium |

**Recommendation:** Start with v2 (OTEL SDK) for production use.

## Running Continuously

### Local (Development)

```bash
# Run in foreground
python monitor_pubsub_to_portal26_v2.py

# Run in background (Windows)
start /B python monitor_pubsub_to_portal26_v2.py > forwarder.log 2>&1
```

### AWS Deployment (Production)

See `AWS_DEPLOYMENT.md` for detailed AWS setup:
- **EC2 with systemd** - Most reliable
- **ECS Fargate** - Fully managed
- **Lambda** - Cost-effective (scheduled only)

## Configuration Variables

All set in `.env` file:

### GCP Settings
```bash
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-subscription
GOOGLE_APPLICATION_CREDENTIALS=C:\Yesu\ai_agent_projectgcp\gcp-credentials.json
```

### Portal26 Settings
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_SERVICE_NAME=gcp-vertex-monitor
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
```

### Multi-tenant Attributes
```bash
PORTAL26_TENANT_ID=tenant1
PORTAL26_USER_ID=relusys_terraform
AGENT_TYPE=gcp-vertex-monitor
```

### Performance Tuning
```bash
PORTAL26_BATCH_SIZE=10          # Logs per batch
PORTAL26_BATCH_TIMEOUT=5        # Seconds before flush
```

**For high volume:**
```bash
PORTAL26_BATCH_SIZE=50
PORTAL26_BATCH_TIMEOUT=10
```

**For low latency:**
```bash
PORTAL26_BATCH_SIZE=5
PORTAL26_BATCH_TIMEOUT=2
```

## Monitoring the Forwarder

### Check Status

```bash
# Is it running?
ps aux | grep monitor_pubsub

# View output
tail -f forwarder.log  # if running in background
```

### Watch Statistics

The forwarder prints stats every 50 messages:
```
--- Stats: 150 received | 150 forwarded | 0 errors ---
```

### Success Indicators

Look for these log lines:
```
[10:30:15] Forwarded: engine-123 | INFO | Total: 45
[OTEL] ✓ Portal26 log exporter initialized
```

## Troubleshooting

### No logs in Portal26

**Check 1: Is forwarder receiving logs?**
```bash
# Should see "Forwarded:" messages
python monitor_pubsub_to_portal26_v2.py
```

If no messages appear, check:
- Pub/Sub subscription exists
- Reasoning Engine is generating logs
- Log sink is configured correctly

**Check 2: Test Portal26 connection**
```bash
python test_portal26_connection.py
```

Should return `✅ SUCCESS`

**Check 3: Verify credentials**
```bash
# Decode the auth header
echo "dGl0YW5pYW06aGVsbG93b3JsZA==" | base64 -d
# Should output: titaniam:helloworld
```

### Authentication Errors (401/403)

```
[ERROR] Portal26 returned 401
```

**Fix:**
1. Verify `OTEL_EXPORTER_OTLP_HEADERS` in `.env`
2. Check if credentials changed
3. Test with `test_portal26_connection.py`

### Connection Timeout

```
[ERROR] Timeout - Could not reach Portal26
```

**Fix:**
1. Check network connectivity: `curl https://otel-tenant1.portal26.in:4318`
2. Verify firewall allows outbound HTTPS
3. Check if Portal26 is accessible from your network

### High Error Rate

```
--- Stats: 100 received | 80 forwarded | 20 errors ---
```

**Possible causes:**
- Rate limiting by Portal26
- Network instability
- Payload too large

**Fix:**
1. Reduce batch size: `PORTAL26_BATCH_SIZE=5`
2. Increase timeout in code (if needed)
3. Check Portal26 service status

### Missing Trace IDs

Trace IDs are only included if:
- GCP logs contain trace information
- Application uses Cloud Trace
- Logs are correlated with traces

This is automatic when available.

## Portal26 Dashboard Queries

### View all GCP logs
```
service.name = "gcp-vertex-monitor"
```

### Filter by tenant
```
tenant.id = "tenant1" AND user.id = "relusys_terraform"
```

### Errors only
```
service.name = "gcp-vertex-monitor" AND severityText = "ERROR"
```

### Specific Reasoning Engine
```
resource.reasoning_engine_id = "your-engine-id"
```

### Recent logs (last hour)
```
service.name = "gcp-vertex-monitor" AND @timestamp > now-1h
```

## Performance Expectations

### Latency
- Pub/Sub pull: 1-2 seconds
- Batch processing: 0-5 seconds (based on batch timeout)
- Portal26 transmission: <1 second
- **Total:** 2-8 seconds end-to-end

### Throughput
- Single instance: ~1000 logs/minute
- Can scale horizontally with multiple instances
- Limited by Pub/Sub subscription throughput

### Resource Usage
- CPU: <5% on t3.micro
- Memory: ~150MB
- Network: Minimal (<1 Mbps)

## Cost Breakdown

### GCP
- Pub/Sub: $0.40 per million messages
- **Typical:** $5-10/month

### AWS (if deployed there)
- EC2 t3.micro: $7-10/month
- **Total:** $15-20/month

### Portal26
- Check your plan for ingestion limits
- This setup minimizes API calls via batching

## Security Best Practices

✅ Credentials in `.env` file (not in code)
✅ Basic auth over HTTPS (encrypted in transit)
✅ Minimal GCP permissions (Pub/Sub subscriber only)
✅ Service account key (not user credentials)

**Important:** Add `.env` to `.gitignore` to prevent credential leaks!

## Next Steps

1. ✅ Test connection: `python test_portal26_connection.py`
2. ✅ Run forwarder: `python monitor_pubsub_to_portal26_v2.py`
3. ✅ Verify in Portal26 dashboard
4. 🔄 Deploy to AWS for production (see `AWS_DEPLOYMENT.md`)
5. 🔄 Set up monitoring alerts
6. 🔄 Create Portal26 dashboards

## Support

- **Portal26 Issues:** Check endpoint URL and credentials
- **GCP Issues:** See `LOG_SINK_INTEGRATION_TEST.md`
- **AWS Deployment:** See `AWS_DEPLOYMENT.md`
- **Script Errors:** Check logs and error messages

## Files Reference

| File | Purpose |
|------|---------|
| `test_portal26_connection.py` | Test Portal26 connectivity |
| `monitor_pubsub.py` | Test Pub/Sub (original) |
| `monitor_pubsub_to_portal26.py` | HTTP-based forwarder |
| `monitor_pubsub_to_portal26_v2.py` | OTEL SDK forwarder ⭐ |
| `.env` | Configuration (your settings) |
| `requirements.txt` | Python dependencies |
| `AWS_DEPLOYMENT.md` | AWS production setup |
| `PORTAL26_QUICKSTART.md` | Quick reference |

---

**Ready to start!** Run the test script first, then start the forwarder.
