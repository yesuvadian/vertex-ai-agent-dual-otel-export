# Email Template: Portal 26 Integration Onboarding

---

**Subject:** Portal 26 Integration for Your Vertex AI Agents - Information Needed

---

Hi [Client Name],

We're ready to integrate Portal 26 monitoring with your Vertex AI agents. This will give you complete visibility into:

- 📊 **Agent performance** (response times, success rates)
- 🔍 **Detailed traces** (LLM calls, tool usage)
- 📝 **Application logs** (errors, debug information)
- 📈 **Usage metrics** (request counts, token consumption)

## What We Need From You

Please fill out the attached **CLIENT_INSTRUCTIONS.md** form with:

1. **GCP Project Details**
   - Project ID and region
   - Service account credentials (or grant us temporary access)

2. **Portal 26 Configuration**
   - Your Portal 26 endpoint URL
   - Preferred service name for telemetry

3. **Agent Source Code**
   - Access to your agent source code (Git repo, zip file, or GCP access)
   - List of agents to monitor

## What Changes We'll Make

We'll add **one line of code** to each agent:

```python
import otel_portal26  # Portal 26 telemetry
```

That's it! Your existing agent logic remains unchanged.

## Timeline

- **Information gathering:** Today
- **Setup & deployment:** 1 business day
- **Testing & handoff:** Same day as deployment

## Security & Access

- We only need **temporary access** for deployment
- Access can be revoked after deployment
- Source code is processed locally, not stored
- All telemetry goes directly to **your** Portal 26 instance

## Next Steps

1. Download and complete: [CLIENT_INSTRUCTIONS.md](./CLIENT_INSTRUCTIONS.md)
2. Return to us via email
3. We'll schedule a deployment window with you
4. You'll have Portal 26 monitoring within 24 hours

## Questions?

Reply to this email or contact us at [your-contact-email]

Looking forward to getting your agents monitored!

Best regards,
[Your Name]
[Your Company]

---

**Attachments:**
- CLIENT_INSTRUCTIONS.md
- Portal 26 Integration Overview.pdf (optional)
