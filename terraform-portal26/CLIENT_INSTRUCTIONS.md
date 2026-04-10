# Portal 26 Integration - Client Instructions

## What We Need From You

To enable Portal 26 monitoring for your Vertex AI agents, we need the following information:

### 1. GCP Project Information

- [ ] **GCP Project ID:** `_______________________`
- [ ] **Region:** (e.g., us-central1, europe-west1) `_______________________`
- [ ] **GCP Access:** Provide service account credentials or grant us access

### 2. Portal 26 Configuration

- [ ] **Portal 26 Endpoint URL:** `_______________________`
  - Example: `https://portal26.example.com/your-company`
- [ ] **Service Name:** `_______________________`
  - Example: `acme-production-agents`

### 3. Agent Source Code

For each agent you want to monitor, provide:

- [ ] **Agent Name:** `_______________________`
- [ ] **Agent Display Name:** `_______________________`
- [ ] **Source Code Location:**
  - Option A: Git repository URL + branch
  - Option B: Zip file of agent source code
  - Option C: Direct access to your GCP project

**Required files per agent:**
- `agent.py` (main agent code)
- `requirements.txt` (Python dependencies)
- Any other agent files

### 4. Access Requirements

Please ensure we have:

- [ ] **Vertex AI API** enabled in your project
- [ ] **IAM Permissions:**
  - `roles/aiplatform.admin` (to deploy agents)
  - `roles/iam.serviceAccountUser`
  - `roles/storage.admin` (for staging buckets)

## What We Will Do

1. ✅ Create a configuration file for your agents
2. ✅ Add Portal 26 telemetry to your agents (minimal code changes)
3. ✅ Deploy agents to Vertex AI Agent Engine
4. ✅ Test telemetry flow to Portal 26
5. ✅ Provide you with agent IDs and testing instructions

## Timeline

- **Setup:** 1-2 hours
- **Initial deployment:** 30 minutes per agent
- **Testing:** 1 hour
- **Total:** 1 business day

## After Deployment

You will receive:

- ✅ List of deployed agent IDs
- ✅ Portal 26 dashboard link
- ✅ Test queries to verify telemetry
- ✅ Documentation for querying agents

## Questions?

Contact us at: [your-contact-email]

---

## For Your Records

**Deployment Date:** `_______________________`
**Contact Person:** `_______________________`
**Portal 26 Namespace:** `_______________________`
**Number of Agents:** `_______________________`
