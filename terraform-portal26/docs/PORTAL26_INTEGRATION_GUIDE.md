# Portal 26 Integration Guide

Multiple approaches for integrating Portal 26 with Vertex AI agents.

## Overview

This guide presents different solutions for sending Vertex AI agent telemetry to Portal 26, depending on your constraints.

## Approaches

### Approach 1: Shared OTEL Module (Recommended)

**For:** Vertex AI Agent Engine with source code access

**How it works:**
1. Terraform manages configuration
2. Python script injects `otel_portal26.py` module
3. Adds one import line to agent.py
4. Deploys to Vertex AI Agent Engine

**Code changes:** One line (`import otel_portal26`)

**Pros:**
- ✅ Minimal code changes
- ✅ Terraform managed
- ✅ Multi-client support
- ✅ Pure Vertex AI solution

**Cons:**
- Requires source code access
- Requires redeployment

**Best for:** Most use cases

[Full Documentation](./VERTEX_ENGINE_PORTAL26_SOLUTION.md)

---

### Approach 2: Hardcoded OTEL in Each Agent

**For:** Agents you fully control

**How it works:**
1. Add full OTEL initialization code to each agent
2. Deploy normally

**Code changes:** ~50 lines per agent

**Pros:**
- ✅ Full control
- ✅ No external dependencies

**Cons:**
- ❌ Lots of code duplication
- ❌ Hard to maintain
- ❌ Manual updates required

**Best for:** Single agent projects

---

### Approach 3: Wrapper Service (Cloud Run)

**For:** Agents without source access

**How it works:**
1. Deploy wrapper service on Cloud Run
2. Wrapper adds OTEL, proxies to agents
3. Clients call wrapper instead of agents

**Code changes:** None (to agents)

**Pros:**
- ✅ No agent code changes
- ✅ Centralized OTEL config

**Cons:**
- ❌ Doesn't work with Vertex AI Agent Engine
- ❌ Additional infrastructure
- ❌ Only works with Cloud Run deployments

**Best for:** Cloud Run deployments only

---

### Approach 4: Environment Variables Only

**For:** Theoretical only

**How it works:**
1. Set OTEL env vars via Terraform
2. Hope ADK initializes OTEL

**Code changes:** None

**Pros:**
- Would be perfect if it worked

**Cons:**
- ❌ **Doesn't work** with Vertex AI Agent Engine
- Env vars arrive too late

**Best for:** Nothing (doesn't work)

---

## Comparison Table

| Approach | Code Changes | Terraform | Redeployment | Vertex AI Engine | Cloud Run | Multi-Client |
|----------|-------------|-----------|--------------|------------------|-----------|--------------|
| **Shared Module** | 1 line | ✅ | Yes | ✅ | N/A | ✅ |
| **Hardcoded** | ~50 lines/agent | ❌ | Yes | ✅ | ✅ | ❌ |
| **Wrapper** | None | ✅ | No | ❌ | ✅ | ✅ |
| **Env Vars Only** | None | ✅ | No | ❌ | ❌ | ✅ |

## Recommendation

**For Vertex AI Agent Engine:** Use **Approach 1 (Shared OTEL Module)**

This is the solution implemented in this `terraform-portal26` package.

## Quick Start

See `../README.md` for setup instructions.

## Files in This Package

```
terraform-portal26/
├── otel_portal26.py           # Shared OTEL module (Approach 1)
├── scripts/
│   └── inject_otel_and_deploy.py  # Deployment automation
├── terraform/                  # Terraform configuration
└── docs/
    ├── VERTEX_ENGINE_PORTAL26_SOLUTION.md  # Detailed guide
    └── PORTAL26_INTEGRATION_GUIDE.md       # This file
```

## Support

- **Quick Start:** `../terraform/QUICKSTART_PORTAL26.md`
- **Detailed Solution:** `./VERTEX_ENGINE_PORTAL26_SOLUTION.md`
- **Installation:** `../INSTALL.md`
