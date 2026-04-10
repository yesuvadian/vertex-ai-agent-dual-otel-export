# Frequently Asked Questions - Portal 26 Integration

## General Questions

### What is Portal 26 integration?

Portal 26 is a monitoring and observability platform. This integration automatically sends telemetry (traces, logs, metrics) from your Vertex AI agents to Portal 26 for analysis and monitoring.

### Why do I need this?

Portal 26 integration gives you:
- **Real-time monitoring** of agent performance
- **Debugging tools** when agents behave unexpectedly
- **Usage analytics** to understand how agents are being used
- **Cost tracking** via token usage metrics

### Will this affect my existing agents?

Minimal impact:
- ✅ **Code changes:** Only one import line added
- ✅ **Performance:** <5ms overhead per request
- ✅ **Functionality:** No changes to agent behavior
- ✅ **Existing features:** All remain intact

---

## Technical Questions

### What code changes are required?

We add one line to your `agent.py`:

```python
import otel_portal26  # Auto-initializes Portal 26 telemetry
```

Everything else remains unchanged.

### Will my agents need to be redeployed?

Yes, but:
- ✅ We handle the redeployment
- ✅ Minimal downtime (5-10 minutes per agent)
- ✅ Rollback available if needed
- ✅ Deployed to same agent IDs (clients don't need updates)

### What data is sent to Portal 26?

**Sent:**
- Request/response timing
- LLM model calls and token counts
- Tool executions and results
- Error messages and stack traces
- Application logs

**NOT sent:**
- User credentials or secrets
- Raw training data
- Internal GCP configurations

### Is this secure?

Yes:
- ✅ **Direct connection:** Telemetry goes from your agents to **your** Portal 26 (not through us)
- ✅ **No third parties:** We don't see your telemetry data
- ✅ **Standard protocols:** Uses OTLP (OpenTelemetry standard)
- ✅ **Encrypted:** All data sent over HTTPS

---

## Access & Permissions

### What GCP permissions do you need?

**For detailed permissions setup, see [PERMISSIONS.md](PERMISSIONS.md)**

**Summary:**

**Approach 1 (One-Time Injection):**
- `roles/aiplatform.user` - Deploy agents
- `roles/storage.objectAdmin` - Access staging buckets
- `roles/cloudbuild.builds.viewer` - Monitor deployments

**Approach 2 (Terraform Automation):**
- `roles/aiplatform.admin` - Full agent management
- `roles/storage.admin` - Storage management
- `roles/iam.serviceAccountUser` - Service account impersonation
- `roles/serviceusage.serviceUsageAdmin` - Enable APIs

**Quick Setup:**
```bash
# Automated setup script (creates service account with correct permissions)
./scripts/setup_terraform_sa.sh your-project-id

# Verify configuration
./scripts/verify_permissions.sh SA_EMAIL PROJECT_ID
```

**Access duration:** Permanent for service accounts, or can be time-limited for individual users.

**Security:** Service account keys should be rotated every 90 days. See [PERMISSIONS.md](PERMISSIONS.md) for security best practices.

### Do you need access to our source code?

Yes, but only temporarily:
- **Option A:** Grant us read access to your Git repository
- **Option B:** Send us a zip file of agent source code
- **Option C:** Grant us temporary GCP project access

We don't store your source code after deployment.

### Can we do the integration ourselves?

Yes! We can provide:
- Documentation and guides
- Terraform configuration template
- Support via email/Slack

Most clients prefer us to handle it (faster and less error-prone).

---

## Deployment Questions

### How long does deployment take?

- **Single agent:** 30 minutes
- **Multiple agents (1-5):** 2 hours
- **Many agents (5+):** 4-8 hours

### What happens during deployment?

1. We create a Terraform configuration for your agents
2. Our script injects the Portal 26 module
3. Agents are redeployed to Vertex AI Agent Engine
4. We verify telemetry is flowing to Portal 26
5. You get agent IDs and test instructions

### What if something goes wrong?

- ✅ **Rollback available:** We keep original agent versions
- ✅ **Terraform state:** Easy to revert changes
- ✅ **Support:** We monitor the deployment with you
- ✅ **Testing:** We test before handoff

### Can we test first before going to production?

Yes! We recommend:
1. **Test deployment:** One non-production agent first
2. **Verify telemetry:** Check Portal 26 dashboard
3. **Full deployment:** After you approve the test

---

## Cost Questions

### Does this cost extra?

- **Our service:** [Your pricing - e.g., "One-time setup fee of $X"]
- **GCP costs:** Unchanged (agents run the same way)
- **Portal 26:** Depends on your Portal 26 plan
- **Network:** Minimal (<1MB per 1000 requests)

### Will telemetry increase my bills?

Minimal impact:
- **Network egress:** ~1-2KB per request (negligible)
- **Compute:** <5ms per request (negligible)
- **Storage:** Portal 26 costs (check your plan)

**Example:** 1 million requests = ~$0.05 additional cost

---

## Portal 26 Questions

### What if we don't have Portal 26 yet?

No problem:
1. Sign up for Portal 26 first
2. Get your endpoint URL
3. Then we'll integrate your agents

We can recommend Portal 26 plans if needed.

### Can we use multiple Portal 26 instances?

Yes! We can configure:
- **Development agents** → Dev Portal 26 instance
- **Production agents** → Production Portal 26 instance

### What if our Portal 26 endpoint changes?

Easy to update:
1. Tell us the new endpoint
2. We update Terraform config
3. Run `terraform apply`
4. All agents update automatically (~10 minutes)

---

## Ongoing Management

### What happens after deployment?

You get:
- ✅ **Agent IDs** for all deployed agents
- ✅ **Portal 26 dashboard** access
- ✅ **Test queries** to verify everything works
- ✅ **Documentation** for your team

### Can we add more agents later?

Yes! Just provide:
- New agent source code
- Portal 26 configuration (usually same as existing)

We'll add them to your Terraform config.

### What if we need to update an agent?

Two options:

**Option A - Simple updates (logic changes):**
- Update your agent code
- Tell us it changed
- We redeploy via Terraform

**Option B - Self-service:**
- We give you the Terraform config
- You can deploy updates yourself

### Do we need to maintain anything?

Minimal:
- ✅ **Portal 26 integration:** Works automatically
- ✅ **Terraform config:** We can maintain or hand off to you
- ✅ **Agent updates:** Contact us or self-deploy

---

## Support Questions

### What support do you provide?

**During deployment:**
- ✅ Setup and configuration
- ✅ Testing and verification
- ✅ Issue resolution

**After deployment:**
- ✅ Email support for integration issues
- ✅ Terraform configuration updates
- ✅ Portal 26 endpoint changes

**Not included:**
- Portal 26 platform support (contact Portal 26)
- Agent logic debugging (unless telemetry-related)
- GCP infrastructure support

### What if telemetry stops working?

We'll help diagnose:
1. **Check Portal 26 endpoint** (is it accessible?)
2. **Check agent logs** (any OTEL errors?)
3. **Check GCP networking** (firewall issues?)
4. **Redeploy if needed** (takes 10 minutes)

### Can we get training on Portal 26?

We provide:
- ✅ **Basic training:** How to view traces/logs/metrics
- ✅ **Documentation:** Portal 26 dashboard guide
- ✅ **Examples:** Common queries and filters

For advanced Portal 26 features, contact Portal 26 support.

---

## Troubleshooting

### "No telemetry appears in Portal 26"

**Check:**
1. Portal 26 endpoint is correct and accessible
2. Agent has been redeployed with Portal 26 integration
3. Agent has been queried at least once
4. Network allows HTTPS to Portal 26 endpoint

**Solution:** Contact us with agent ID and error logs.

### "Agent is slower after integration"

**Expected:** <5ms additional latency per request

**If more:**
1. Check Portal 26 endpoint latency (should be <50ms)
2. Verify network connection to Portal 26
3. Consider using a closer Portal 26 region

**Solution:** We can help optimize batch/async settings.

### "Portal 26 shows wrong service name"

**Cause:** Configuration mismatch

**Solution:**
1. Tell us the correct service name
2. We update Terraform config
3. Redeploy (10 minutes)

---

## Next Steps

Ready to enable Portal 26 monitoring?

1. **Review:** Read this FAQ
2. **Complete:** [CLIENT_INSTRUCTIONS.md](./CLIENT_INSTRUCTIONS.md)
3. **Send:** Return completed form to us
4. **Deploy:** We'll schedule deployment with you

Questions? Contact us at [your-contact-email]
