# How to Use Client Documentation

This guide explains how to use the client-facing documentation in this folder.

## Overview of Client Documents

```
terraform-portal26/
├── CLIENT_INSTRUCTIONS.md          # Form for clients to fill out
├── CLIENT_ONBOARDING_EMAIL.md      # Email template to send clients
├── CLIENT_FAQ.md                   # Answers to common questions
├── CLIENT_HANDOFF_TEMPLATE.md      # Post-deployment report
└── HOW_TO_USE_CLIENT_DOCS.md       # This file
```

---

## Workflow: Client Onboarding

### Step 1: Initial Contact

**Send:** `CLIENT_ONBOARDING_EMAIL.md`

**Customize:**
```markdown
Hi [Client Name],                                    # ← Insert client name

Subject: Portal 26 Integration for Your Vertex AI Agents - Information Needed
```

**Include attachments:**
- `CLIENT_INSTRUCTIONS.md`
- `CLIENT_FAQ.md` (optional)

**Timeline:** Client fills out form within 1-3 days

---

### Step 2: Receive Client Information

**They return:** Completed `CLIENT_INSTRUCTIONS.md`

**Example filled form:**
```markdown
### 1. GCP Project Information

- [x] **GCP Project ID:** `acme-production-123`
- [x] **Region:** `us-central1`
- [x] **GCP Access:** Service account JSON attached

### 2. Portal 26 Configuration

- [x] **Portal 26 Endpoint URL:** `https://portal26.acme.com`
- [x] **Service Name:** `acme-production-agents`

### 3. Agent Source Code

- [x] **Agent Name:** `customer-support`
- [x] **Agent Display Name:** `ACME Customer Support`
- [x] **Source Code Location:** Git repo: github.com/acme/agents
```

**Action:** Review and verify all information is complete

---

### Step 3: Setup & Deployment

**Internal steps:**

1. Create client Terraform config:
```bash
cd terraform-portal26/terraform/clients
cp client-a.tfvars acme-corp.tfvars
```

2. Edit `acme-corp.tfvars` with client info:
```hcl
project_id = "acme-production-123"
portal26_endpoint = "https://portal26.acme.com"
portal26_service_name = "acme-production-agents"

agents = {
  "customer-support" = {
    source_dir = "/path/to/acme/support_agent"
    display_name = "ACME Customer Support"
  }
}
```

3. Deploy:
```bash
terraform apply -var-file="clients/acme-corp.tfvars"
```

4. Test:
```bash
python3 query_agent.py AGENT_ID "test query"
# Verify telemetry in Portal 26
```

---

### Step 4: Handoff

**Send:** `CLIENT_HANDOFF_TEMPLATE.md` (customized)

**Customize:**
```markdown
**Client:** ACME Corporation                # ← Insert client details
**Deployment Date:** 2024-04-08
**Deployed By:** Your Name

### Agents Deployed

| Agent Name | Agent ID | Display Name | Status |
|------------|----------|--------------|--------|
| customer-support | `123456789` | ACME Customer Support | ✅ Active |
                      ↑ Insert actual agent IDs

### Portal 26 Configuration

- **Endpoint:** `https://portal26.acme.com`     # ← Insert actual endpoint
- **Service Name:** `acme-production-agents`
- **Dashboard URL:** `https://portal26.acme.com/dashboard`
```

**Include:**
- ✅ All agent IDs
- ✅ Test queries
- ✅ Portal 26 dashboard link
- ✅ Support contact info

---

## Document Templates: How to Customize

### CLIENT_ONBOARDING_EMAIL.md

**Variables to replace:**
- `[Client Name]` → Actual client name
- `[Your Name]` → Your name
- `[Your Company]` → Your company name
- `[your-contact-email]` → Your email

**Optional additions:**
- Company logo
- Meeting scheduler link
- Pricing information
- SLA details

---

### CLIENT_INSTRUCTIONS.md

**When to customize:**
- Different GCP regions
- Additional requirements
- Specific security needs

**Example customization:**
```markdown
### Additional Requirements (for ACME Corp)

- [ ] **Compliance:** HIPAA compliance required
- [ ] **Network:** VPC peering needed
- [ ] **Backup:** Daily backups to separate bucket
```

---

### CLIENT_FAQ.md

**When to customize:**
- Pricing specific to client
- Custom support SLAs
- Industry-specific concerns

**Example addition:**
```markdown
### For Healthcare Clients

**Is this HIPAA compliant?**
Yes, all telemetry is encrypted in transit (HTTPS) and at rest.
Portal 26 is BAA-compliant. We can provide documentation.
```

---

### CLIENT_HANDOFF_TEMPLATE.md

**Must customize:**
- Client name
- Deployment date
- Agent IDs (actual IDs from deployment)
- Portal 26 URLs (actual URLs)
- Test queries (relevant to their agents)

**Optional sections:**
- Custom alerts configured
- Integration with their monitoring
- Training schedule

---

## Common Client Questions & Responses

### "How long will this take?"

**Response (from FAQ):**
```
- Single agent: 30 minutes
- Multiple agents (1-5): 2 hours
- Many agents (5+): 4-8 hours

We'll schedule deployment at a convenient time for you.
```

### "What code changes are needed?"

**Response:**
```
Only one line added to each agent:

    import otel_portal26  # Portal 26 telemetry

Your existing agent logic remains completely unchanged.
We can show you the exact changes before deployment.
```

### "Is this secure?"

**Response (from FAQ):**
```
Yes:
✅ Telemetry goes directly from YOUR agents to YOUR Portal 26
✅ We don't see your telemetry data
✅ All data encrypted over HTTPS
✅ Follows OpenTelemetry standard protocols
✅ You control access to Portal 26 dashboard
```

### "What if we need to update agents later?"

**Response:**
```
Two options:

1. Contact us: We redeploy via Terraform (~10 minutes)
2. Self-service: We give you Terraform config to manage yourself

Most clients prefer option 1 for simplicity.
```

---

## Email Sequences

### Initial Outreach

**Day 1:** Send `CLIENT_ONBOARDING_EMAIL.md`

**Day 3:** Follow-up if no response
```
Hi [Client],

Just following up on Portal 26 integration. Do you have any 
questions about the information we need?

Happy to schedule a quick call to discuss.

Best,
[Your Name]
```

**Day 7:** Final follow-up
```
Hi [Client],

Wanted to check in one more time about Portal 26 integration.

If timing isn't right now, we can revisit in the future.
Let me know!

Best,
[Your Name]
```

---

### Post-Deployment

**Day 1 (immediately):** Send `CLIENT_HANDOFF_TEMPLATE.md`

**Day 2:** Check-in email
```
Hi [Client],

Just checking in - have you had a chance to test the agents
and view telemetry in Portal 26?

Any questions or issues?

Best,
[Your Name]
```

**Week 1:** Follow-up
```
Hi [Client],

It's been a week since deployment. How's Portal 26 working
out for you?

We can schedule a quick training session if helpful.

Best,
[Your Name]
```

**Month 1:** Feedback request
```
Hi [Client],

One month update! How has Portal 26 monitoring been?

We'd love your feedback to improve our service.

Best,
[Your Name]
```

---

## Customization Checklist

Before sending to clients:

### CLIENT_ONBOARDING_EMAIL.md
- [ ] Replace [Client Name]
- [ ] Replace [Your Name]
- [ ] Replace [Your Company]
- [ ] Replace [your-contact-email]
- [ ] Add pricing information (if applicable)
- [ ] Add your company branding

### CLIENT_INSTRUCTIONS.md
- [ ] Review required fields
- [ ] Add any client-specific requirements
- [ ] Update contact information
- [ ] Add security/compliance questions if needed

### CLIENT_FAQ.md
- [ ] Update pricing information
- [ ] Update support contact details
- [ ] Add industry-specific questions
- [ ] Review technical details match your setup

### CLIENT_HANDOFF_TEMPLATE.md
- [ ] Insert client name
- [ ] Insert deployment date
- [ ] Insert actual agent IDs
- [ ] Insert actual Portal 26 URLs
- [ ] Add relevant test queries
- [ ] Update support contact info
- [ ] Add training schedule (if applicable)

---

## Tips for Success

### 1. Be Proactive
- Send FAQ with initial email (reduces back-and-forth)
- Offer to schedule a kickoff call
- Provide examples of what they'll see in Portal 26

### 2. Set Expectations
- Clear timeline (24-48 hours for deployment)
- What you need from them
- What they'll receive from you

### 3. Follow Up
- Check in 24 hours after handoff
- Ask for feedback after 1 week
- Offer training if needed

### 4. Document Everything
- Keep copies of completed CLIENT_INSTRUCTIONS.md
- Save deployment configurations
- Track what clients are using

### 5. Iterate
- Update FAQ based on new questions
- Add common scenarios to templates
- Improve based on client feedback

---

## File Organization

### For Each Client, Create:

```
clients-docs/
└── acme-corp/
    ├── 01-onboarding-email-sent.md       # Copy of email sent
    ├── 02-instructions-received.md       # Their completed form
    ├── 03-deployment-notes.md            # Your notes during deployment
    └── 04-handoff-sent.md               # Copy of handoff document
```

### Terraform Config (Separate)

```
terraform-portal26/terraform/clients/
└── acme-corp.tfvars    # Their Terraform configuration
```

---

## Summary

**Client Journey:**
1. **Initial Contact** → Send onboarding email + instructions
2. **Information Gathering** → Receive completed form
3. **Deployment** → You deploy via Terraform
4. **Handoff** → Send completion report + testing instructions
5. **Support** → Ongoing assistance as needed

**Documents Used:**
- `CLIENT_ONBOARDING_EMAIL.md` → First contact
- `CLIENT_INSTRUCTIONS.md` → Information gathering
- `CLIENT_FAQ.md` → Answer questions
- `CLIENT_HANDOFF_TEMPLATE.md` → Final delivery

**Key Success Factors:**
- Clear communication
- Set expectations
- Quick turnaround
- Good documentation
- Follow-up support

---

Questions about using these documents? Update this guide based on your experience!
