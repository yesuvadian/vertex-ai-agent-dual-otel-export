# Empty Agent with Portal26 OTEL

Minimal agent for testing Portal26 telemetry ingestion.

## Features

- ✅ Simple echo functionality
- ✅ Health check endpoint
- ✅ Portal26 OTEL integration (auto-injected by Terraform)
- ✅ Traces, logs, and metrics to Kinesis

## Functions

### `simple_query(query: str) -> str`
Echoes the input query with a prefix.

### `get_status() -> dict`
Returns agent status and capabilities.

## Deployment

This agent is deployed via Terraform with automatic OTEL injection:

```bash
cd terraform-portal26/terraform
terraform apply -var-file="empty-agent.tfvars"
```

## Testing

```bash
# Query the agent
python3 ../../query_agent.py AGENT_ID "Hello Portal26"

# Check status
python3 ../../query_agent.py AGENT_ID "What is your status?"
```

## Telemetry

All activity is tracked and sent to:
- **Portal26 Endpoint**: https://otel-tenant1.portal26.in:4318
- **Service Name**: empty-agent-portal26
- **User ID**: relusys_terraform
- **Tenant ID**: tenant1

Check Kinesis for telemetry data:
```bash
cd ../../portal26_otel_agent
python3 pull_agent_logs.py
```
