# Portal 26 Integration - Deployment Complete

**Client:** [Client Name]  
**Deployment Date:** [Date]  
**Deployed By:** [Your Name]  

---

## ✅ Deployment Summary

We've successfully integrated Portal 26 monitoring with your Vertex AI agents!

### Agents Deployed

| Agent Name | Agent ID | Display Name | Status |
|------------|----------|--------------|--------|
| agent-1 | `123456789` | Customer Support | ✅ Active |
| agent-2 | `987654321` | Sales Assistant | ✅ Active |
| agent-3 | `456789123` | Technical Support | ✅ Active |

### Portal 26 Configuration

- **Endpoint:** `https://portal26.example.com/client-name`
- **Service Name:** `client-name-production`
- **Dashboard URL:** `https://portal26.example.com/client-name/dashboard`

---

## 🧪 Testing Your Setup

### 1. Query an Agent

```bash
# Option A: Using gcloud
gcloud ai agents query AGENT_ID \
  --project=YOUR_PROJECT_ID \
  --location=us-central1 \
  --query="What is the weather in Tokyo?"

# Option B: Using our test script
python3 query_agent.py AGENT_ID "What is the weather in Tokyo?"
```

### 2. View Telemetry in Portal 26

1. Go to: `https://portal26.example.com/client-name/dashboard`
2. You should see:
   - **Traces:** Agent invocation → LLM call → Tool execution
   - **Logs:** Application logs with timestamps
   - **Metrics:** Request counts, latency graphs

### 3. Example Queries to Test

```bash
# Test different agents
python3 query_agent.py 123456789 "What services do you offer?"
python3 query_agent.py 987654321 "I need help with my account"
python3 query_agent.py 456789123 "How do I reset my password?"
```

---

## 📊 What You'll See in Portal 26

### Traces

Each request creates a trace showing:
- Request received → Agent invoked
- LLM call to Gemini (with timing)
- Tool execution (if any)
- Response generated
- Total duration

**Screenshot example:**
```
└─ agent_invocation (2.3s)
   ├─ llm_call: gemini-2.5-flash (1.2s)
   ├─ tool_execution: get_weather (0.5s)
   └─ llm_call: format_response (0.6s)
```

### Logs

Application logs with:
- Timestamp
- Log level (INFO, WARNING, ERROR)
- Message
- Associated trace ID

**Example:**
```
2024-04-08 10:15:23 INFO  [trace:abc123] Agent processing query
2024-04-08 10:15:24 INFO  [trace:abc123] Calling LLM with prompt
2024-04-08 10:15:25 INFO  [trace:abc123] Tool get_weather executed
```

### Metrics

Dashboards showing:
- **Request rate:** Requests per minute
- **Latency:** P50, P95, P99 response times
- **Error rate:** Failed requests percentage
- **Token usage:** LLM token consumption

---

## 🔧 Common Portal 26 Queries

### Find Slow Requests

```
service.name = "client-name-production" 
AND duration > 3s
```

### Find Errors

```
status.code = ERROR
AND service.name = "client-name-production"
```

### Track Specific Agent

```
agent.id = "123456789"
```

### Token Usage by Agent

```
GROUP BY agent.id
SUM(llm.token_count.total)
```

---

## 📁 Files & Configuration

### Terraform Configuration

Location: `terraform-portal26/terraform/clients/client-name.tfvars`

```hcl
project_id = "client-project-id"
region     = "us-central1"

portal26_endpoint     = "https://portal26.example.com/client-name"
portal26_service_name = "client-name-production"

agents = {
  "customer-support" = {
    source_dir   = "/path/to/support_agent"
    display_name = "Customer Support"
  }
  # ... more agents
}
```

### To Update Configuration

If you need to change Portal 26 endpoint or add agents:

**Option A - We handle it:**
1. Email us with changes needed
2. We update Terraform config
3. Run `terraform apply`
4. Changes deployed in ~10 minutes

**Option B - You handle it:**
1. We provide you the Terraform config
2. You modify `clients/client-name.tfvars`
3. Run `terraform apply`
4. Changes deployed automatically

---

## 🚨 Troubleshooting

### No telemetry in Portal 26?

**Check:**
```bash
# 1. Verify Portal 26 endpoint is accessible
curl https://portal26.example.com/client-name/health

# 2. Check agent logs for OTEL errors
gcloud ai agents logs read AGENT_ID --limit=50

# 3. Verify agent was redeployed
gcloud ai agents describe AGENT_ID --format="value(updateTime)"
```

**If still not working:** Contact us with agent ID and error messages.

### Agent not responding?

**Check:**
```bash
# Verify agent is active
gcloud ai agents list --filter="displayName:Customer Support"

# Check recent errors
gcloud ai agents logs read AGENT_ID --filter="severity=ERROR"
```

**If agent is down:** Contact us immediately.

### Wrong data in Portal 26?

**Possible causes:**
- Service name mismatch (check Terraform config)
- Multiple agents with same name (check agent IDs)
- Cached old data (wait 5 minutes for refresh)

**Solution:** Contact us to verify configuration.

---

## 📞 Support

### What we support

✅ **Integration issues:**
- Telemetry not appearing
- Configuration updates
- Agent redeployment

✅ **Terraform management:**
- Updating endpoints
- Adding new agents
- Configuration changes

### What Portal 26 supports

Contact Portal 26 support for:
- Portal 26 platform issues
- Dashboard configuration
- Advanced query help
- User management

### Contact Us

- **Email:** [your-email]
- **Slack:** #client-support
- **Phone:** [your-phone] (urgent issues only)

**Response time:** Within 4 business hours

---

## 📋 Next Steps

### For Your Team

1. ✅ **Access Portal 26:** Ensure your team has dashboard access
2. ✅ **Test queries:** Run the test commands above
3. ✅ **Explore dashboard:** Familiarize yourself with traces/logs/metrics
4. ✅ **Set up alerts:** Configure Portal 26 alerts for errors

### Recommended Monitoring

- **Error rate alert:** If >5% of requests fail
- **Latency alert:** If P95 latency >5 seconds
- **Usage alert:** Track daily request volume

### Optional Training

We can provide:
- 30-minute Portal 26 walkthrough
- Dashboard configuration help
- Custom query examples

Contact us to schedule.

---

## 📄 Documentation

All documentation is in the `terraform-portal26` folder:

- **Overview:** `README.md`
- **Client FAQ:** `CLIENT_FAQ.md`
- **Technical details:** `docs/VERTEX_ENGINE_PORTAL26_SOLUTION.md`

We can provide these files upon request.

---

## ✅ Checklist

Before we close this deployment:

- [ ] All agents deployed and active
- [ ] Telemetry visible in Portal 26
- [ ] Test queries successful
- [ ] Your team has Portal 26 access
- [ ] You have agent IDs documented
- [ ] Questions answered

---

**Congratulations! Your agents are now monitored with Portal 26! 🎉**

Questions? Reply to this document or contact us anytime.

Best regards,  
[Your Name]  
[Your Company]
