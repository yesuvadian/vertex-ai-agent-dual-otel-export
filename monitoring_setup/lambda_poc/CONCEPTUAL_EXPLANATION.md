# Requirement Flow: Cross-Cloud Observability Architecture

## 🎯 **Requirement**

**System Requirements:**
- AI agents deployed on Google Cloud Platform (Vertex AI Reasoning Engine)
- Agents perform operations: answering queries, executing tools, processing data
- Complete observability required: activity tracking, debugging capability, performance monitoring
- Telemetry data must be forwarded to Portal26 observability platform/Kinesis/S3 (AWS-hosted)

**Technical Challenge:** 
- Source: Google Cloud Platform (GCP)
- Destination: Portal26 on AWS
- Requirement: Secure cross-cloud data pipeline for logs, traces, and metrics

---

## 🌊 **The Complete Flow **

Think of it like a relay race with security checkpoints:

```
1. AI Agent does work (like answering "What's the weather?")
   ↓
2. Cloud Logging automatically captures what the agent did (raw logs)
   ↓
3. Log Sink filter says "only send logs from these specific agents"
   ↓
4. Pub/Sub queues and sends raw logs to AWS
   ↓
5. Before sending, Google gives Pub/Sub a "security badge" (JWT token)
   ↓
6. AWS Lambda receives raw logs with badge
   ↓
7. Lambda checks: "Is this badge real? Is it for me?"
   ↓
8. [AWS SIDE] Lambda extracts traces and metrics from received logs
   ↓
9. [AWS SIDE] Lambda transforms to OTEL format (traces, logs, metrics)
   ↓
10. [AWS SIDE] Lambda routes based on trace size:
    • Small traces → Portal26 OTEL Endpoint
    • Large traces → S3
    • All traces → Kinesis stream
    (If authentication failed → Reject and log security event)
```

---

## 🔑 **Key Concepts Explained**

### 1. **OIDC Authentication (The Security Badge System)**

**What is it?**
Think of OIDC like a driver's license or passport - it proves who you are without needing to share passwords.

**How it works in our system:**
- Google Cloud says: "I'm sending this message, here's my official ID badge (JWT token)"
- AWS Lambda says: "Let me check with Google if this badge is real"
- Google says: "Yes, that's my badge, it's valid"
- AWS Lambda: "Okay, I'll process the message"

**Why this matters:**
- No passwords or API keys to steal
- Can't be forged (signed by Google's secret key)
- Expires after 1 hour (even if stolen, becomes useless quickly)

### 2. **JWT Token (The Actual Badge)**

**What's in the badge:**
```
Issuer: "Google issued this"
Audience: "This is specifically for Lambda URL xyz123"
Subject: "Service account abc is sending this"
Expiration: "Valid until 2:00 PM today"
Signature: "Signed with Google's secret key - can't be faked"
```

**Why it's secure:**
- Like a hologram on a credit card - you can verify it's real
- Can only be used for the specific Lambda it was made for
- Time-limited, so old badges don't work

---

## 🏗️ **Why Each Component Exists**

| Component | Why It's Needed | What If We Removed It? |
|-----------|----------------|------------------------|
| **Cloud Logging** | Auto-captures all agent activity | We'd miss logs, have blind spots |
| **Log Sink** | Filters only relevant logs | Would send ALL logs (expensive, noisy) |
| **Pub/Sub** | Reliable queuing + retries | Messages could be lost if Lambda is down |
| **OIDC/JWT** | Secure authentication | Anyone could send fake messages to Lambda |
| **Lambda** | Extract traces/metrics, transform to OTEL, route based on size | Need something to process logs and route telemetry data |
| **Portal26 OTEL** | Real-time processing for small traces | No real-time analytics for small traces |
| **S3** | Storage for large traces and archival | Large traces would overload OTEL endpoint |
| **Kinesis** | Real-time streaming for all trace data | No streaming analytics capability |

---

This architecture is essentially a **secure, reliable postal system** for AI agent logs that crosses cloud provider boundaries using modern authentication standards. It's production-ready, scalable, and maintainable.
