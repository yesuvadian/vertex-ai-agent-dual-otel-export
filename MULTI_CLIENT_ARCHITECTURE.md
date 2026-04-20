# Multi-Client, Multi-Agent Architecture

## Your Question: Multiple Clients with Multiple Agents

**Scenario:** You have many clients, each with their own agents. How should the architecture work?

---

## Architecture Options

### Option 1: Shared Pub/Sub with Filtering (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                    ALL CLIENTS & AGENTS                      │
├─────────────────────────────────────────────────────────────┤
│  Client A                Client B                Client C    │
│  ├─ Agent 1             ├─ Agent 1               ├─ Agent 1 │
│  ├─ Agent 2             ├─ Agent 2               ├─ Agent 2 │
│  └─ Agent 3             └─ Agent 3               └─ Agent 3 │
└────────┬──────────────────────┬──────────────────────┬──────┘
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   SINGLE LOG SINK     │
                    │   (Filters all logs)  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  SINGLE PUB/SUB TOPIC │
                    │  vertex-telemetry-all │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  SINGLE FORWARDER     │
                    │  (Tags by client)     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      PORTAL26         │
                    │  (Filter by client)   │
                    └───────────────────────┘
```

**How it works:**
- ✅ One Pub/Sub topic for all clients/agents
- ✅ One forwarder instance
- ✅ Logs tagged with `client_id` and `agent_id` attributes
- ✅ Filter in Portal26 by client: `client.id = "client-a"`
- ✅ Most cost-effective
- ✅ Simplest to manage

**Log format:**
```json
{
  "resource": {
    "attributes": [
      {"key": "service.name", "value": "gcp-vertex-monitor"},
      {"key": "client.id", "value": "client-a"},
      {"key": "agent.id", "value": "agent-1"},
      {"key": "resource.reasoning_engine_id", "value": "123456"}
    ]
  }
}
```

**Portal26 queries:**
```
# All logs for Client A
client.id = "client-a"

# Specific agent for Client B
client.id = "client-b" AND agent.id = "agent-2"

# All clients, specific agent name
agent.id = "billing-agent"
```

---

### Option 2: One Pub/Sub Topic Per Client

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Client A    │      │  Client B    │      │  Client C    │
│  All Agents  │      │  All Agents  │      │  All Agents  │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Log Sink A   │      │ Log Sink B   │      │ Log Sink C   │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Pub/Sub      │      │ Pub/Sub      │      │ Pub/Sub      │
│ Topic A      │      │ Topic B      │      │ Topic C      │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       ▼                     ▼                     �▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Forwarder A  │      │ Forwarder B  │      │ Forwarder C  │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┴─────────────────────┘
                             │
                             ▼
                    ┌──────────────┐
                    │  PORTAL26    │
                    └──────────────┘
```

**How it works:**
- ✅ Complete isolation per client
- ✅ Easier billing (track Pub/Sub usage per client)
- ✅ Can scale forwarders independently
- ❌ More infrastructure to manage
- ❌ Higher cost (N topics + N forwarders)

**Use case:** When clients require data isolation or separate billing

---

### Option 3: Shared Topic, Multiple Subscriptions

```
                    ┌───────────────────────┐
                    │  ALL CLIENTS/AGENTS   │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   SINGLE PUB/SUB TOPIC│
                    └─────┬────┬────┬───────┘
                          │    │    │
         ┌────────────────┘    │    └────────────────┐
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Subscription A  │  │ Subscription B  │  │ Subscription C  │
│ (Filter: A)     │  │ (Filter: B)     │  │ (Filter: C)     │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Forwarder A     │  │ Forwarder B     │  │ Forwarder C     │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                     │                      │
         └─────────────────────┴──────────────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │      PORTAL26         │
                    └───────────────────────┘
```

**How it works:**
- ✅ One topic with filtered subscriptions
- ✅ Each subscription filters for specific client
- ✅ Independent forwarders per client
- ⚠️ Limited filtering capability in Pub/Sub subscriptions
- ⚠️ Still multiple forwarders to manage

---

## Recommended Architecture: Option 1 (Shared + Tagging)

### Why This is Best:

1. **Cost-Effective**
   - One Pub/Sub topic (~$5/month)
   - One forwarder instance (~$10-15/month)
   - Total: ~$20/month for ALL clients

2. **Simple to Manage**
   - Single deployment
   - One codebase
   - Easy updates

3. **Flexible**
   - Add new clients without infrastructure changes
   - Filter in Portal26 (powerful query engine)
   - Multi-tenant attributes built-in

4. **Scalable**
   - Forwarder can handle thousands of clients
   - Add more forwarders if needed (automatic load balancing)
   - Portal26 handles filtering efficiently

---

## Implementation: Shared Architecture

### 1. Log Sink Configuration

**Single log sink for all agents:**

```bash
gcloud logging sinks create vertex-telemetry-all-clients \
  --log-filter='resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --destination=pubsub.googleapis.com/projects/PROJECT/topics/vertex-telemetry-all \
  --project=PROJECT_ID
```

### 2. Client & Agent Identification

**Option A: From Resource Labels (Automatic)**

If your Reasoning Engines have labels:
```python
# When creating Reasoning Engine
engine = reasoning_engines.ReasoningEngine.create(
    my_agent,
    labels={
        "client_id": "client-a",
        "agent_id": "billing-agent",
        "environment": "production"
    }
)
```

These labels appear in logs automatically!

**Option B: From Engine Naming Convention**

Use naming pattern: `{client-id}-{agent-name}-{env}`
- Example: `acme-billing-agent-prod`

Parse in forwarder:
```python
engine_name = "acme-billing-agent-prod"
parts = engine_name.split('-')
client_id = parts[0]  # "acme"
agent_id = parts[1]   # "billing"
```

**Option C: Lookup Table**

Maintain mapping:
```python
ENGINE_CLIENT_MAP = {
    "6010661182900273152": {"client_id": "client-a", "agent_id": "agent-1"},
    "7020771293011384263": {"client_id": "client-b", "agent_id": "agent-2"},
}
```

### 3. Enhanced Forwarder

**Modified `continuous_forwarder.py`:**

```python
# Add client/agent identification
def convert_to_otel(log_entry):
    # ... existing code ...
    
    # Extract identifiers
    resource_labels = resource.get('labels', {})
    reasoning_engine_id = resource_labels.get('reasoning_engine_id', 'unknown')
    
    # Get client/agent info
    client_info = get_client_info(reasoning_engine_id, resource_labels)
    
    # Add to OTEL attributes
    otel_log["attributes"].extend([
        {"key": "client.id", "value": {"stringValue": client_info['client_id']}},
        {"key": "agent.id", "value": {"stringValue": client_info['agent_id']}},
        {"key": "agent.type", "value": {"stringValue": client_info['agent_type']}},
    ])
    
    return otel_log

def get_client_info(engine_id, labels):
    """Extract client/agent info from labels or lookup table"""
    # From labels (if available)
    if 'client_id' in labels:
        return {
            'client_id': labels.get('client_id', 'unknown'),
            'agent_id': labels.get('agent_id', 'unknown'),
            'agent_type': labels.get('agent_type', 'unknown')
        }
    
    # From lookup table
    if engine_id in ENGINE_CLIENT_MAP:
        return ENGINE_CLIENT_MAP[engine_id]
    
    # Default
    return {
        'client_id': 'unknown',
        'agent_id': engine_id,
        'agent_type': 'reasoning-engine'
    }
```

### 4. Portal26 Resource Attributes

**Final OTEL format:**
```json
{
  "resourceLogs": [{
    "resource": {
      "attributes": [
        {"key": "service.name", "value": "gcp-vertex-monitor"},
        {"key": "client.id", "value": "acme-corp"},
        {"key": "agent.id", "value": "billing-agent"},
        {"key": "agent.type", "value": "billing"},
        {"key": "environment", "value": "production"},
        {"key": "resource.reasoning_engine_id", "value": "123456"},
        {"key": "resource.location", "value": "us-central1"}
      ]
    }
  }]
}
```

---

## Portal26 Multi-Client Queries

### View all clients:
```
service.name = "gcp-vertex-monitor" | stats count by client.id
```

### Logs for specific client:
```
client.id = "acme-corp"
```

### Specific agent for client:
```
client.id = "acme-corp" AND agent.id = "billing-agent"
```

### All billing agents across clients:
```
agent.type = "billing"
```

### Errors for Client A:
```
client.id = "client-a" AND severityText = "ERROR"
```

### Compare clients:
```
service.name = "gcp-vertex-monitor" 
| stats count by client.id, severityText
| sort by count desc
```

---

## Scaling Considerations

### When You Have 10 Clients:
- ✅ Single forwarder handles it easily
- Cost: ~$20/month total

### When You Have 100 Clients:
- ✅ Still single forwarder (if <10K logs/day)
- If more traffic: Add 2-3 forwarders
- Cost: ~$50/month total

### When You Have 1000+ Clients:
- Option 1: Multiple forwarders (5-10 instances)
- Option 2: Switch to push-based Cloud Functions (auto-scales)
- Cost: ~$100-200/month

**Shared architecture scales to thousands of clients easily!**

---

## Client Isolation & Security

### Data Isolation in Portal26:

**Option 1: Role-Based Access Control**
```
User "acme-admin" can only query: client.id = "acme-corp"
User "beta-admin" can only query: client.id = "beta-inc"
```

**Option 2: Separate Portal26 Tenants**
```
Acme Corp → tenant: acme
Beta Inc → tenant: beta
```

**Option 3: API Key per Client**
```
Each client gets unique Portal26 API key
Forwarder uses client-specific key
```

### Network Isolation:

If required, use **Option 2** (separate topics per client) for complete isolation.

---

## Migration Path

### Phase 1: Start with Shared (1-10 clients)
```
Single topic + Single forwarder
Cost: $20/month
```

### Phase 2: Scale (10-100 clients)
```
Single topic + 2-3 forwarders
Cost: $50/month
```

### Phase 3: High Scale (100+ clients)
```
Option A: Single topic + Push-based (auto-scaling)
Option B: Topic per client group (enterprise, standard, free)
Cost: $100-200/month
```

---

## Configuration Example

### Environment Variables (.env):

```bash
# GCP
GCP_PROJECT_ID=agentic-ai-integration-490716
PUBSUB_SUBSCRIPTION=vertex-telemetry-all

# Portal26
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
OTEL_SERVICE_NAME=gcp-vertex-monitor

# Multi-client support
ENABLE_CLIENT_TAGGING=true
CLIENT_LOOKUP_TABLE=clients.json  # Optional
DEFAULT_CLIENT_ID=unknown
DEFAULT_AGENT_TYPE=reasoning-engine
```

### Client Lookup Table (clients.json):

```json
{
  "6010661182900273152": {
    "client_id": "acme-corp",
    "client_name": "Acme Corporation",
    "agent_id": "billing-agent",
    "agent_type": "billing",
    "environment": "production"
  },
  "7020771293011384263": {
    "client_id": "beta-inc",
    "client_name": "Beta Industries",
    "agent_id": "support-agent",
    "agent_type": "customer-support",
    "environment": "production"
  }
}
```

---

## Cost Comparison

### Shared Architecture (Recommended):
```
1-10 clients:     $20/month
10-100 clients:   $50/month
100-1000 clients: $200/month
```

### Separate Topics Per Client:
```
10 clients:  $150/month (10 topics + 10 forwarders)
100 clients: $1500/month (not scalable!)
```

**Shared = 7-10x cheaper at scale!**

---

## Summary

### ✅ Recommended: Shared Pub/Sub with Client Tagging

**Why:**
- Cost-effective ($20/month for many clients)
- Simple to manage (one deployment)
- Flexible (filter in Portal26)
- Scales to thousands of clients
- Easy to add new clients (no infrastructure changes)

**When to use separate topics:**
- Strict data isolation required
- Different SLAs per client
- Separate billing per client
- Compliance requirements

**Implementation:**
- Use existing forwarder code
- Add client/agent identification logic
- Tag logs with `client.id` and `agent.id`
- Query by client in Portal26

---

**Your setup can easily handle 100+ clients with a single Pub/Sub topic and forwarder!** 🚀
