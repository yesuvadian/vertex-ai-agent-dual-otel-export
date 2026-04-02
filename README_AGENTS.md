# AI Agent Project - GCP with Multiple Telemetry Destinations

## Quick Summary

**3 Agents Deployed:**

1. **portal26_ngrok_agent** - Ngrok → Local Receiver → Portal26 + JSON files
2. **portal26_otel_agent** - Direct to Portal26 ✓ (Tested & Working)
3. **gcp_traces_agent** - GCP Cloud Trace (default) 🆕

---

## Testing & Verification

### Test Portal26 Integration

**Quick test:**
```bash
python test_otel_direct.py
```
✓ Confirmed working - sends to Portal26 with authentication

**Verify Portal26 dashboard:**
```bash
python verify_telemetry.py
```

**Check Portal26 endpoint:**
```bash
python check_portal26_response.py
```
✓ Returns 200 OK

### View GCP Cloud Traces

For **gcp_traces_agent** (default GCP telemetry):

1. Go to: https://console.cloud.google.com/traces?project=agentic-ai-integration-490716
2. Filter by service: `gcp_traces_agent`
3. Query the agent via Console to generate traces

### Team Member Verification

**For Portal26:** See `VERIFY_PORTAL26.md`
- Login to Portal26
- Filter: tenant_id=tenant1, user_id=relusys
- Look for traces from portal26_otel_agent

---

## Agent Endpoints

**GCP Console:**
https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=agentic-ai-integration-490716

**Portal26:**
- Endpoint: https://otel-tenant1.portal26.in:4318
- Auth: Basic dGl0YW5pYW06aGVsbG93b3JsZA==
- Tenant: tenant1, User: relusys

**GCP Cloud Trace:**
https://console.cloud.google.com/traces?project=agentic-ai-integration-490716

---

## Files Structure

```
ai_agent_projectgcp/
├── portal26_ngrok_agent/       # Ngrok → Local → Portal26
│   ├── agent.py               # Custom OTEL
│   ├── .env                   # Ngrok endpoint
│   └── requirements.txt
│
├── portal26_otel_agent/        # Direct Portal26 ✓
│   ├── agent.py               # Custom OTEL
│   ├── .env                   # Portal26 + auth
│   └── requirements.txt
│
├── gcp_traces_agent/           # GCP Cloud Trace 🆕
│   ├── agent.py               # No custom OTEL
│   ├── .env                   # GCP defaults only
│   └── requirements.txt
│
├── local_otel_receiver.py      # Forwards ngrok → Portal26
├── test_otel_direct.py         # Test Portal26 direct ✓
├── verify_telemetry.py         # Verification script
├── check_portal26_response.py  # Portal26 endpoint test ✓
├── send_test_trace.py          # Generate test traces
│
├── VERIFY_PORTAL26.md          # Team verification guide
├── PORTAL26_READY_TO_DEPLOY.md # Deployment guide
├── AGENTS_COMPARISON.md        # Detailed comparison
└── terraform/                  # Infrastructure as code
    ├── main.tf
    ├── terraform.tfvars
    └── *.bat                   # Switch configs
```

---

## Quick Start

### 1. Test Portal26 (Already Working ✓)

```bash
python test_otel_direct.py
```

Expected: Span sent to Portal26, check dashboard

### 2. Query Deployed Agent

Go to GCP Console → portal26_otel_agent → Send query:
```
What is the weather in Bengaluru?
```

Check Portal26 dashboard for traces

### 3. View GCP Traces (New Agent)

Go to GCP Console → gcp_traces_agent → Send query:
```
What is the weather in Tokyo?
```

Check: https://console.cloud.google.com/traces

---

## Key Differences

| Agent | OTEL Setup | Destination | Auth Required | Best For |
|-------|-----------|-------------|---------------|----------|
| portal26_ngrok | Custom | Local+Portal26 | Via receiver | Development |
| portal26_otel | Custom | Portal26 direct | In .env | Production |
| gcp_traces | Default | GCP Trace | N/A | Standard GCP |

---

## Status

✅ Portal26 authentication working (200 OK)  
✅ portal26_otel_agent tested locally  
✅ gcp_traces_agent deploying  
✅ All configurations verified  

---

For detailed information:
- **Portal26 verification:** `VERIFY_PORTAL26.md`
- **Agent comparison:** `AGENTS_COMPARISON.md`
- **Terraform setup:** `terraform/README.md`
